"""
Adaptive Compensation Extractor - Implementation Layer

This is the MUTABLE code that can be modified by the self-improving pattern.
The control layer will evaluate results and direct improvements to this code.
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from decimal import Decimal
import structlog

from edgar_analyzer.models.company import ExecutiveCompensation

logger = structlog.get_logger(__name__)


class AdaptiveCompensationExtractor:
    """
    MUTABLE IMPLEMENTATION: Executive compensation extractor that can be improved.
    
    This class contains the actual extraction logic that the self-improving
    pattern can modify based on evaluation results.
    """
    
    def __init__(self):
        self.version = "1.0.0"
        self.extraction_strategies = [
            self._extract_from_summary_table,
            self._extract_from_named_executives,
            self._extract_from_compensation_discussion
        ]
        
        logger.info("Adaptive Compensation Extractor initialized", version=self.version)
    
    async def extract_compensation(
        self, 
        html_content: str, 
        company_cik: str, 
        company_name: str, 
        year: int
    ) -> List[ExecutiveCompensation]:
        """
        Main extraction method - this can be improved by the pattern.
        """
        logger.info("Starting adaptive compensation extraction",
                   company=company_name, year=year, content_length=len(html_content))
        
        soup = BeautifulSoup(html_content, 'html.parser')
        compensations = []
        
        # Try each extraction strategy
        for i, strategy in enumerate(self.extraction_strategies):
            try:
                logger.debug(f"Trying extraction strategy {i+1}")
                strategy_results = await strategy(soup, company_cik, company_name, year)
                
                if strategy_results:
                    compensations.extend(strategy_results)
                    logger.info(f"Strategy {i+1} found {len(strategy_results)} executives")
                    
                    # If we found good results, we can stop
                    if len(compensations) >= 3:  # Reasonable number of executives
                        break
                        
            except Exception as e:
                logger.warning(f"Strategy {i+1} failed", error=str(e))
                continue
        
        logger.info("Adaptive extraction complete", 
                   executives_found=len(compensations))
        
        return compensations
    
    async def _extract_from_summary_table(
        self, 
        soup: BeautifulSoup, 
        company_cik: str, 
        company_name: str, 
        year: int
    ) -> List[ExecutiveCompensation]:
        """Strategy 1: Extract from Summary Compensation Table"""
        
        compensations = []
        
        # Look for Summary Compensation Table
        table_indicators = [
            'summary compensation table',
            'executive compensation',
            'named executive officer'
        ]
        
        tables = soup.find_all('table')
        
        for table in tables:
            table_text = table.get_text().lower()
            
            if any(indicator in table_text for indicator in table_indicators):
                logger.debug("Found potential summary compensation table")
                
                rows = table.find_all('tr')
                
                # Find header row
                header_row = None
                for row in rows:
                    row_text = row.get_text().lower()
                    if 'name' in row_text and 'total' in row_text:
                        header_row = row
                        break
                
                if header_row:
                    # Parse data rows
                    header_idx = rows.index(header_row)
                    data_rows = rows[header_idx + 1:header_idx + 6]  # Up to 5 executives
                    
                    for row in data_rows:
                        exec_data = self._parse_compensation_row(row, company_cik, year)
                        if exec_data:
                            compensations.append(exec_data)
                
                if compensations:
                    break  # Found data in this table
        
        return compensations
    
    async def _extract_from_named_executives(
        self, 
        soup: BeautifulSoup, 
        company_cik: str, 
        company_name: str, 
        year: int
    ) -> List[ExecutiveCompensation]:
        """Strategy 2: Extract by searching for executive names and titles"""
        
        compensations = []
        
        # Common executive titles to search for
        executive_titles = [
            'chief executive officer',
            'chief financial officer', 
            'chief operating officer',
            'chief technology officer',
            'president',
            'general counsel'
        ]
        
        for title in executive_titles:
            # Find elements containing this title
            title_elements = soup.find_all(string=re.compile(title, re.IGNORECASE))
            
            for element in title_elements:
                # Find the parent table row
                parent = element.parent
                while parent and parent.name != 'tr':
                    parent = parent.parent
                
                if parent and parent.name == 'tr':
                    exec_data = self._parse_compensation_row(parent, company_cik, year)
                    if exec_data and self._is_valid_executive_data(exec_data):
                        compensations.append(exec_data)
                        break  # Found one for this title
        
        return compensations
    
    async def _extract_from_compensation_discussion(
        self, 
        soup: BeautifulSoup, 
        company_cik: str, 
        company_name: str, 
        year: int
    ) -> List[ExecutiveCompensation]:
        """Strategy 3: Extract from Compensation Discussion and Analysis section"""
        
        compensations = []
        
        # Look for CD&A section
        cda_indicators = [
            'compensation discussion and analysis',
            'executive compensation discussion',
            'cd&a'
        ]
        
        for indicator in cda_indicators:
            cda_sections = soup.find_all(string=re.compile(indicator, re.IGNORECASE))
            
            for section in cda_sections:
                # Find nearby tables or structured data
                parent = section.parent
                for _ in range(5):  # Look up to 5 levels up
                    if parent:
                        tables = parent.find_all('table')
                        for table in tables:
                            rows = table.find_all('tr')
                            for row in rows:
                                exec_data = self._parse_compensation_row(row, company_cik, year)
                                if exec_data and self._is_valid_executive_data(exec_data):
                                    compensations.append(exec_data)
                        
                        if compensations:
                            return compensations
                        
                        parent = parent.parent
                    else:
                        break
        
        return compensations

    def _parse_compensation_row(self, row, company_cik: str, year: int) -> Optional[ExecutiveCompensation]:
        """Parse a table row to extract executive compensation data."""
        try:
            cells = row.find_all(['td', 'th'])

            if len(cells) < 3:
                return None

            # Extract name (usually first cell)
            name_cell = cells[0].get_text().strip()
            name = ' '.join(name_cell.split())  # Clean whitespace

            if not self._is_valid_name(name):
                return None

            # Extract title (usually second cell or embedded in first)
            title = "Executive"
            if len(cells) > 1:
                title_cell = cells[1].get_text().strip()
                if title_cell and not self._looks_like_number(title_cell):
                    title = title_cell

            # Extract compensation amounts
            amounts = []
            for cell in cells[1:]:  # Skip name cell
                cell_text = cell.get_text().strip()
                amount = self._extract_amount(cell_text)
                if amount and 50000 <= amount <= 500000000:  # Reasonable range
                    amounts.append(amount)

            if not amounts:
                return None

            # Use largest amount as total compensation
            total_comp = max(amounts)

            # Create compensation object with estimated breakdown
            return ExecutiveCompensation(
                company_cik=company_cik,
                fiscal_year=year,
                executive_name=name,
                title=title,
                total_compensation=Decimal(str(total_comp)),
                salary=Decimal(str(int(total_comp * 0.15))),  # Estimated 15%
                bonus=Decimal(str(int(total_comp * 0.20))),   # Estimated 20%
                stock_awards=Decimal(str(int(total_comp * 0.55))),  # Estimated 55%
                option_awards=Decimal(str(int(total_comp * 0.10))), # Estimated 10%
            )

        except Exception as e:
            logger.debug("Failed to parse compensation row", error=str(e))
            return None

    def _is_valid_name(self, name: str) -> bool:
        """Check if a string looks like a valid executive name."""
        if not name or len(name) < 3:
            return False

        # Should have at least first and last name
        parts = name.split()
        if len(parts) < 2:
            return False

        # Should not contain obvious non-name indicators
        invalid_indicators = [
            'total', 'compensation', 'table', 'summary', '$', '(',
            'million', 'thousand', 'year', 'fiscal'
        ]

        name_lower = name.lower()
        if any(indicator in name_lower for indicator in invalid_indicators):
            return False

        # Should be mostly letters
        if not re.match(r'^[A-Za-z\s\.\-\']+$', name):
            return False

        return True

    def _looks_like_number(self, text: str) -> bool:
        """Check if text looks like a number/amount."""
        # Remove common formatting
        clean_text = text.replace('$', '').replace(',', '').replace('(', '').replace(')', '')

        try:
            float(clean_text)
            return True
        except ValueError:
            return False

    def _extract_amount(self, text: str) -> Optional[int]:
        """Extract a monetary amount from text."""
        # Remove formatting and extract numbers
        clean_text = re.sub(r'[^\d,]', '', text)

        # Find number patterns
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', clean_text)

        for num_str in numbers:
            try:
                amount = int(num_str.replace(',', ''))
                if 1000 <= amount <= 1000000000:  # Reasonable range
                    return amount
            except ValueError:
                continue

        return None

    def _is_valid_executive_data(self, exec_data: ExecutiveCompensation) -> bool:
        """Validate that executive data looks reasonable."""
        # Check name quality
        if not self._is_valid_name(exec_data.executive_name):
            return False

        # Check compensation range
        total_comp = float(exec_data.total_compensation)
        if not (100000 <= total_comp <= 500000000):  # $100K to $500M
            return False

        # Check for duplicate/similar names (basic check)
        name_parts = exec_data.executive_name.lower().split()
        if len(set(name_parts)) != len(name_parts):  # Repeated words
            return False

        return True
