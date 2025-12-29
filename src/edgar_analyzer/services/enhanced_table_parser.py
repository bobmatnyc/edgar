"""
Enhanced table parser for better proxy statement parsing
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class EnhancedTableParser:
    """Enhanced parser for proxy statement tables"""

    def __init__(self):
        # Common table headers for compensation tables
        self.compensation_headers = [
            "name",
            "title",
            "year",
            "salary",
            "bonus",
            "stock awards",
            "option awards",
            "non-equity incentive plan compensation",
            "change in pension value",
            "all other compensation",
            "total",
        ]

        # Table identification patterns
        self.table_patterns = [
            r"summary compensation table",
            r"executive compensation",
            r"named executive officer",
            r"compensation discussion",
            r"annual compensation",
        ]

        # Executive title patterns
        self.title_patterns = [
            r"chief executive officer|ceo",
            r"chief financial officer|cfo",
            r"chief operating officer|coo",
            r"president",
            r"executive vice president",
            r"senior vice president",
        ]

    def find_compensation_tables(self, html_content: str) -> List[Dict]:
        """Find all potential compensation tables in HTML content"""
        soup = BeautifulSoup(html_content, "html.parser")
        tables = []

        # Method 1: Find tables by nearby text
        tables.extend(self._find_tables_by_context(soup))

        # Method 2: Find tables by header content
        tables.extend(self._find_tables_by_headers(soup))

        # Method 3: Find tables by structure analysis
        tables.extend(self._find_tables_by_structure(soup))

        # Remove duplicates and rank by confidence
        unique_tables = self._deduplicate_and_rank(tables)

        return unique_tables

    def _find_tables_by_context(self, soup: BeautifulSoup) -> List[Dict]:
        """Find tables by looking for compensation-related text nearby"""
        tables = []

        # Find all text that mentions compensation tables
        for pattern in self.table_patterns:
            matches = soup.find_all(text=re.compile(pattern, re.IGNORECASE))

            for match in matches:
                # Look for tables near this text
                parent = match.parent
                for _ in range(5):  # Look up to 5 levels up
                    if parent is None:
                        break

                    # Find tables in this parent or nearby siblings
                    nearby_tables = parent.find_all("table")
                    for table in nearby_tables:
                        confidence = self._calculate_table_confidence(table, pattern)
                        if confidence > 0.3:
                            tables.append(
                                {
                                    "table": table,
                                    "confidence": confidence,
                                    "method": "context",
                                    "pattern": pattern,
                                }
                            )

                    parent = parent.parent

        return tables

    def _find_tables_by_headers(self, soup: BeautifulSoup) -> List[Dict]:
        """Find tables by analyzing header content"""
        tables = []

        for table in soup.find_all("table"):
            headers = self._extract_table_headers(table)
            confidence = self._score_headers(headers)

            if confidence > 0.4:
                tables.append(
                    {
                        "table": table,
                        "confidence": confidence,
                        "method": "headers",
                        "headers": headers,
                    }
                )

        return tables

    def _find_tables_by_structure(self, soup: BeautifulSoup) -> List[Dict]:
        """Find tables by analyzing structure (rows, columns, data types)"""
        tables = []

        for table in soup.find_all("table"):
            structure_score = self._analyze_table_structure(table)

            if structure_score > 0.5:
                tables.append(
                    {
                        "table": table,
                        "confidence": structure_score,
                        "method": "structure",
                    }
                )

        return tables

    def _extract_table_headers(self, table: Tag) -> List[str]:
        """Extract headers from a table"""
        headers = []

        # Try different header extraction methods
        # Method 1: th tags
        th_tags = table.find_all("th")
        if th_tags:
            headers = [th.get_text().strip().lower() for th in th_tags]

        # Method 2: First row of td tags
        if not headers:
            first_row = table.find("tr")
            if first_row:
                cells = first_row.find_all(["td", "th"])
                headers = [cell.get_text().strip().lower() for cell in cells]

        # Method 3: Bold text in first few rows
        if not headers:
            rows = table.find_all("tr")[:3]  # Check first 3 rows
            for row in rows:
                bold_cells = row.find_all(["b", "strong"])
                if bold_cells:
                    headers = [cell.get_text().strip().lower() for cell in bold_cells]
                    break

        return headers

    def _score_headers(self, headers: List[str]) -> float:
        """Score headers based on compensation table patterns"""
        if not headers:
            return 0.0

        score = 0.0
        total_headers = len(headers)

        for header in headers:
            header_lower = header.lower()

            # High value headers
            if any(
                comp_header in header_lower
                for comp_header in [
                    "name",
                    "total",
                    "salary",
                    "bonus",
                    "stock",
                    "option",
                ]
            ):
                score += 0.2

            # Medium value headers
            elif any(
                comp_header in header_lower
                for comp_header in ["compensation", "awards", "incentive", "year"]
            ):
                score += 0.1

            # Executive title indicators
            elif any(
                re.search(pattern, header_lower) for pattern in self.title_patterns
            ):
                score += 0.15

        # Normalize by number of headers
        return min(1.0, score)

    def _analyze_table_structure(self, table: Tag) -> float:
        """Analyze table structure for compensation table characteristics"""
        rows = table.find_all("tr")
        if len(rows) < 3:  # Too few rows
            return 0.0

        score = 0.0

        # Check for appropriate number of columns (typically 6-12 for comp tables)
        first_row_cells = len(rows[0].find_all(["td", "th"]))
        if 6 <= first_row_cells <= 12:
            score += 0.3

        # Check for numeric data (compensation amounts)
        numeric_cells = 0
        total_cells = 0

        for row in rows[1:6]:  # Check first few data rows
            cells = row.find_all(["td", "th"])
            for cell in cells:
                text = cell.get_text().strip()
                total_cells += 1

                # Look for dollar amounts or large numbers
                if re.search(r"\$[\d,]+|\b\d{4,}\b", text):
                    numeric_cells += 1

        if total_cells > 0:
            numeric_ratio = numeric_cells / total_cells
            if numeric_ratio > 0.3:  # At least 30% numeric data
                score += 0.4

        # Check for executive names/titles
        name_indicators = 0
        for row in rows[1:]:  # Skip header row
            cells = row.find_all(["td", "th"])
            if cells:
                first_cell = cells[0].get_text().strip()

                # Look for name patterns
                if re.search(r"^[A-Z][a-z]+\s+[A-Z]", first_cell):
                    name_indicators += 1
                # Look for title patterns
                elif any(
                    re.search(pattern, first_cell.lower())
                    for pattern in self.title_patterns
                ):
                    name_indicators += 1

        if name_indicators >= 2:  # At least 2 rows with name/title indicators
            score += 0.3

        return min(1.0, score)

    def _calculate_table_confidence(self, table: Tag, pattern: str) -> float:
        """Calculate confidence score for a table based on context pattern"""
        base_score = 0.5  # Base score for being near compensation text

        # Analyze table content
        headers = self._extract_table_headers(table)
        header_score = self._score_headers(headers)

        structure_score = self._analyze_table_structure(table)

        # Combine scores
        confidence = (base_score + header_score + structure_score) / 3

        # Bonus for specific patterns
        if "summary compensation" in pattern.lower():
            confidence += 0.2

        return min(1.0, confidence)

    def _deduplicate_and_rank(self, tables: List[Dict]) -> List[Dict]:
        """Remove duplicate tables and rank by confidence"""
        # Remove duplicates by comparing table HTML
        seen_tables = set()
        unique_tables = []

        for table_info in tables:
            table_html = str(table_info["table"])
            table_hash = hash(table_html)

            if table_hash not in seen_tables:
                seen_tables.add(table_hash)
                unique_tables.append(table_info)

        # Sort by confidence (highest first)
        unique_tables.sort(key=lambda x: x["confidence"], reverse=True)

        return unique_tables
