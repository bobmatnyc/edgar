"""SEC EDGAR API client for fetching company filings."""

import re
from dataclasses import dataclass
from typing import Any, cast

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class SecEdgarClient:
    """Client for SEC EDGAR API.

    Attributes:
        user_agent: Required User-Agent header for SEC API
        base_url: SEC API base URL
        timeout: Request timeout in seconds
    """

    user_agent: str = "EDGAR Platform research@example.com"
    base_url: str = "https://data.sec.gov"
    timeout: float = 30.0

    async def get_company_submissions(self, cik: str) -> dict[str, Any]:
        """Get all submissions for a company.

        Args:
            cik: Company CIK number (10 digits with leading zeros)

        Returns:
            Company submissions data including all filings
        """
        url = f"{self.base_url}/submissions/CIK{cik.zfill(10)}.json"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    async def get_latest_filing(
        self,
        cik: str,
        form_type: str = "DEF 14A",
    ) -> dict[str, Any]:
        """Get the most recent filing of a specific type.

        Args:
            cik: Company CIK number
            form_type: SEC form type (e.g., "DEF 14A", "10-K", "10-Q")

        Returns:
            Filing metadata including accession number and document URL
        """
        submissions = await self.get_company_submissions(cik)
        filings = submissions["filings"]["recent"]

        # Find first matching form type
        for i, form in enumerate(filings["form"]):
            if form == form_type:
                accession = filings["accessionNumber"][i].replace("-", "")
                primary_doc = filings["primaryDocument"][i]
                filing_date = filings["filingDate"][i]

                return {
                    "cik": cik,
                    "accession_number": filings["accessionNumber"][i],
                    "filing_date": filing_date,
                    "form_type": form_type,
                    "primary_document": primary_doc,
                    "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}",
                }

        raise ValueError(f"No {form_type} filing found for CIK {cik}")

    async def fetch_filing_html(self, url: str) -> str:
        """Fetch the HTML content of a filing.

        Args:
            url: Full URL to the filing document

        Returns:
            HTML content as string
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            return response.text


def parse_summary_compensation_table(html: str) -> list[dict[str, Any]]:
    """Parse Summary Compensation Table from DEF 14A HTML.

    Args:
        html: HTML content of DEF 14A filing

    Returns:
        List of executive compensation records
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find the Summary Compensation Table
    # Look for table following "Summary Compensation Table" heading
    sct_header = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "b", "strong"]):
        text = tag.get_text(strip=True).lower()
        if "summary compensation table" in text and "narrative" not in text:
            sct_header = tag
            break

    if not sct_header:
        raise ValueError("Summary Compensation Table not found in document")

    # Find the next table after the header
    table = sct_header.find_next("table")
    if not table:
        raise ValueError("No table found after Summary Compensation Table header")

    # Parse table rows
    rows = table.find_all("tr")
    if len(rows) < 2:
        raise ValueError("Table has insufficient rows")

    # Extract data rows (skip header rows)
    executives = []
    current_exec = None

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        # Get cell text values
        values = [clean_cell_value(cell.get_text(strip=True)) for cell in cells]

        # Skip header rows
        if any(h in values[0].lower() for h in ["name", "principal", "position", "year"]):
            continue

        # Check if this is a name row or data row
        if values[0] and not values[0].isdigit() and len(values[0]) > 3:
            # This might be a name/title row
            name_match = extract_executive_name(values[0])
            if name_match:
                current_exec = {
                    "name": name_match["name"],
                    "title": name_match.get("title", ""),
                    "compensation": [],
                }
                executives.append(current_exec)

        # Try to parse as data row (year, salary, bonus, etc.)
        if current_exec and len(values) >= 7:
            year = extract_year(values)
            if year:
                comp_data = parse_compensation_row(values, year)
                if comp_data:
                    compensation_list = cast(list[dict[str, Any]], current_exec["compensation"])
                    compensation_list.append(comp_data)

    return executives


def clean_cell_value(value: str) -> str:
    """Clean a table cell value."""
    # Remove footnote markers, normalize whitespace
    value = re.sub(r"\(\d+\)", "", value)  # Remove (1), (2), etc.
    value = re.sub(r"\[\d+\]", "", value)  # Remove [1], [2], etc.
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_executive_name(text: str) -> dict[str, str] | None:
    """Extract executive name and title from text."""
    # Common patterns: "Tim Cook Chief Executive Officer" or "Tim Cook, CEO"
    lines = text.split("\n")
    if lines:
        name = lines[0].strip()
        title = lines[1].strip() if len(lines) > 1 else ""
        if len(name) > 2 and not name[0].isdigit():
            return {"name": name, "title": title}
    return None


def extract_year(values: list[str]) -> int | None:
    """Extract fiscal year from row values."""
    for val in values[:3]:
        if val.isdigit() and 2000 <= int(val) <= 2030:
            return int(val)
    return None


def parse_compensation_row(values: list[str], year: int) -> dict[str, Any] | None:
    """Parse a compensation data row."""

    def to_number(s: str) -> float:
        """Convert string to number, handling currency formatting."""
        if not s or s in ["—", "–", "-", "N/A", ""]:
            return 0.0
        # Remove $, commas, parentheses
        s = re.sub(r"[$,()]", "", s)
        try:
            return float(s)
        except ValueError:
            return 0.0

    # Standard SCT columns after name/year:
    # Salary, Bonus, Stock Awards, Option Awards, Non-Equity, Pension, Other, Total
    try:
        return {
            "year": year,
            "salary": to_number(values[2] if len(values) > 2 else ""),
            "bonus": to_number(values[3] if len(values) > 3 else ""),
            "stock_awards": to_number(values[4] if len(values) > 4 else ""),
            "option_awards": to_number(values[5] if len(values) > 5 else ""),
            "non_equity_incentive": to_number(values[6] if len(values) > 6 else ""),
            "pension_change": to_number(values[7] if len(values) > 7 else ""),
            "other_compensation": to_number(values[8] if len(values) > 8 else ""),
            "total": to_number(values[9] if len(values) > 9 else values[-1]),
        }
    except (IndexError, ValueError):
        return None
