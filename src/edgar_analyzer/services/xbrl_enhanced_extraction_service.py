"""
XBRL-Enhanced Executive Compensation Extraction Service

This service leverages the new SEC Inline XBRL requirements for executive compensation
to provide high-quality, structured data extraction from proxy statements.
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import edgar
from edgar import Company, Filing

logger = logging.getLogger(__name__)


class XBRLEnhancedExtractionService:
    """Enhanced executive compensation extraction using XBRL and modern EDGAR tools"""

    def __init__(self, identity: str = "edgar.analyzer@example.com"):
        """Initialize the XBRL-enhanced extraction service"""
        self.identity = identity
        edgar.set_identity(identity)
        logger.info(
            f"XBRL Enhanced Extraction Service initialized with identity: {identity}"
        )

    async def extract_executive_compensation(
        self, symbol: str, company_name: str
    ) -> Dict:
        """
        Extract executive compensation using multiple methods with XBRL priority

        Priority order:
        1. XBRL structured data (highest quality)
        2. Enhanced text parsing with edgartools
        3. Fallback to traditional HTML parsing
        """

        logger.info(f"Starting XBRL-enhanced extraction for {company_name} ({symbol})")

        try:
            # Get company object
            company = Company(symbol)

            # Get latest proxy filing (DEF 14A)
            proxy_filings = company.get_filings(form="DEF 14A")

            if not proxy_filings:
                logger.warning(f"No proxy filings found for {symbol}")
                return self._create_error_result(
                    symbol, company_name, "no_proxy_filings"
                )

            proxy_filing = proxy_filings[0]  # Most recent
            logger.info(
                f"Found proxy filing {proxy_filing.accession_number} dated {proxy_filing.filing_date}"
            )

            # Try XBRL extraction first
            xbrl_result = await self._extract_xbrl_compensation(
                proxy_filing, symbol, company_name
            )
            if xbrl_result["success"]:
                logger.info(f"XBRL extraction successful for {symbol}")
                return xbrl_result

            # Fallback to enhanced text extraction
            text_result = await self._extract_text_compensation(
                proxy_filing, symbol, company_name
            )
            if text_result["success"]:
                logger.info(f"Enhanced text extraction successful for {symbol}")
                return text_result

            # Final fallback
            logger.warning(f"All extraction methods failed for {symbol}")
            return self._create_error_result(symbol, company_name, "all_methods_failed")

        except Exception as e:
            logger.error(f"Error extracting compensation for {symbol}: {e}")
            return self._create_error_result(
                symbol, company_name, "extraction_error", str(e)
            )

    async def _extract_xbrl_compensation(
        self, filing: Filing, symbol: str, company_name: str
    ) -> Dict:
        """Extract executive compensation from XBRL structured data"""

        try:
            filing_obj = filing.obj()

            # Check for XBRL instance
            if not hasattr(filing_obj, "xbrl") or not filing_obj.xbrl:
                logger.info(f"No XBRL instance found for {symbol}")
                return {"success": False, "reason": "no_xbrl"}

            # Extract XBRL executive compensation data
            # This would be implemented when XBRL executive compensation taxonomy is available
            logger.info(
                f"XBRL instance found for {symbol} - extracting structured data"
            )

            # TODO: Implement XBRL executive compensation extraction
            # For now, return not implemented
            return {"success": False, "reason": "xbrl_not_implemented"}

        except Exception as e:
            logger.error(f"XBRL extraction error for {symbol}: {e}")
            return {"success": False, "reason": "xbrl_error", "error": str(e)}

    async def _extract_text_compensation(
        self, filing: Filing, symbol: str, company_name: str
    ) -> Dict:
        """Extract executive compensation using enhanced text parsing"""

        try:
            filing_obj = filing.obj()

            # Get text content
            if not hasattr(filing_obj, "text"):
                logger.warning(f"No text content available for {symbol}")
                return {"success": False, "reason": "no_text"}

            text_content = filing_obj.text()
            logger.info(
                f"Retrieved text content for {symbol}: {len(text_content)} characters"
            )

            # Enhanced text parsing for executive compensation
            executives = await self._parse_executive_compensation_text(
                text_content, symbol
            )

            if not executives:
                logger.warning(f"No executives found in text parsing for {symbol}")
                return {"success": False, "reason": "no_executives_found"}

            return {
                "success": True,
                "company_name": company_name,
                "symbol": symbol,
                "filing_date": str(filing.filing_date),
                "accession_number": filing.accession_number,
                "data_source": "enhanced_text_extraction",
                "executives": executives,
                "extraction_method": "edgartools_text_parsing",
                "quality_score": self._calculate_quality_score(executives),
            }

        except Exception as e:
            logger.error(f"Text extraction error for {symbol}: {e}")
            return {"success": False, "reason": "text_error", "error": str(e)}

    async def _parse_executive_compensation_text(
        self, text: str, symbol: str
    ) -> List[Dict]:
        """Parse executive compensation from proxy statement text"""

        executives = []

        # Look for executive compensation table patterns
        # This is a simplified implementation - would need more sophisticated parsing

        # Pattern 1: Summary Compensation Table
        summary_table_pattern = r"SUMMARY COMPENSATION TABLE.*?(?=\n\n|\n[A-Z])"
        summary_match = re.search(
            summary_table_pattern, text, re.IGNORECASE | re.DOTALL
        )

        if summary_match:
            table_text = summary_match.group(0)
            logger.info(f"Found Summary Compensation Table for {symbol}")

            # Extract executive data from table
            # This would need more sophisticated parsing logic
            executives = self._parse_compensation_table(table_text, symbol)

        # Pattern 2: Look for individual executive sections
        if not executives:
            executives = self._parse_individual_executive_sections(text, symbol)

        return executives

    def _parse_compensation_table(self, table_text: str, symbol: str) -> List[Dict]:
        """Parse compensation data from table text"""

        executives = []

        # This is a simplified implementation
        # In practice, would need sophisticated table parsing

        # Look for common executive titles and compensation amounts
        lines = table_text.split("\n")

        for line in lines:
            # Look for lines with executive names and compensation
            if any(
                title in line.lower()
                for title in [
                    "ceo",
                    "chief executive",
                    "president",
                    "cfo",
                    "chief financial",
                ]
            ):
                # Extract name and compensation (simplified)
                compensation_match = re.findall(r"\$[\d,]+", line)
                if compensation_match:
                    # This is very simplified - real implementation would be more sophisticated
                    total_comp = compensation_match[0].replace("$", "").replace(",", "")

                    executive = {
                        "name": "Executive Name (parsed)",  # Would extract actual name
                        "title": "Executive Title (parsed)",  # Would extract actual title
                        "total_compensation": (
                            int(total_comp) if total_comp.isdigit() else 0
                        ),
                        "salary": 0,  # Would parse individual components
                        "bonus": 0,
                        "stock_awards": 0,
                        "option_awards": 0,
                        "other_compensation": 0,
                    }

                    executives.append(executive)

        logger.info(f"Parsed {len(executives)} executives from table for {symbol}")
        return executives

    def _parse_individual_executive_sections(
        self, text: str, symbol: str
    ) -> List[Dict]:
        """Parse executive compensation from individual sections"""

        # This would implement parsing of individual executive compensation sections
        # For now, return empty list
        logger.info(f"Individual section parsing not yet implemented for {symbol}")
        return []

    def _calculate_quality_score(self, executives: List[Dict]) -> float:
        """Calculate quality score for extracted data"""

        if not executives:
            return 0.0

        # Simple quality scoring based on data completeness
        total_score = 0
        for exec_data in executives:
            score = 0
            if exec_data.get("name"):
                score += 0.2
            if exec_data.get("title"):
                score += 0.2
            if exec_data.get("total_compensation", 0) > 0:
                score += 0.3
            if exec_data.get("salary", 0) > 0:
                score += 0.1
            if exec_data.get("bonus", 0) > 0:
                score += 0.1
            if exec_data.get("stock_awards", 0) > 0:
                score += 0.1

            total_score += score

        return total_score / len(executives)

    def _create_error_result(
        self, symbol: str, company_name: str, reason: str, error: str = None
    ) -> Dict:
        """Create standardized error result"""

        return {
            "success": False,
            "company_name": company_name,
            "symbol": symbol,
            "reason": reason,
            "error": error,
            "data_source": "xbrl_enhanced_extraction",
            "extraction_method": "failed",
        }
