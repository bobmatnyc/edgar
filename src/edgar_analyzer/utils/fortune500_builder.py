"""Fortune 500 company database builder."""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import structlog
from bs4 import BeautifulSoup

from edgar_analyzer.models.company import Company

logger = structlog.get_logger(__name__)


class Fortune500Builder:
    """Build comprehensive Fortune 500 company database."""

    def __init__(self):
        """Initialize Fortune 500 builder."""
        self.session: Optional[aiohttp.ClientSession] = None

        # Known Fortune 500 companies with CIK mappings (Top 50)
        self.known_companies = [
            {"rank": 1, "name": "Walmart Inc.", "ticker": "WMT", "cik": "0000066740"},
            {"rank": 2, "name": "Amazon.com Inc.", "ticker": "AMZN", "cik": "0001018724"},
            {"rank": 3, "name": "Apple Inc.", "ticker": "AAPL", "cik": "0000320193"},
            {"rank": 4, "name": "CVS Health Corporation", "ticker": "CVS", "cik": "0000064803"},
            {"rank": 5, "name": "UnitedHealth Group Incorporated", "ticker": "UNH", "cik": "0000731766"},
            {"rank": 6, "name": "Exxon Mobil Corporation", "ticker": "XOM", "cik": "0000034088"},
            {"rank": 7, "name": "Berkshire Hathaway Inc.", "ticker": "BRK.A", "cik": "0001067983"},
            {"rank": 8, "name": "Alphabet Inc.", "ticker": "GOOGL", "cik": "0001652044"},
            {"rank": 9, "name": "McKesson Corporation", "ticker": "MCK", "cik": "0000927653"},
            {"rank": 10, "name": "Cencora Inc.", "ticker": "COR", "cik": "0001140859"},
            {"rank": 11, "name": "Costco Wholesale Corporation", "ticker": "COST", "cik": "0000909832"},
            {"rank": 12, "name": "JPMorgan Chase & Co.", "ticker": "JPM", "cik": "0000019617"},
            {"rank": 13, "name": "Microsoft Corporation", "ticker": "MSFT", "cik": "0000789019"},
            {"rank": 14, "name": "Cardinal Health, Inc.", "ticker": "CAH", "cik": "0000721371"},
            {"rank": 15, "name": "Chevron Corporation", "ticker": "CVX", "cik": "0000093410"},
            {"rank": 16, "name": "Ford Motor Company", "ticker": "F", "cik": "0000037996"},
            {"rank": 17, "name": "General Motors Company", "ticker": "GM", "cik": "0001467858"},
            {"rank": 18, "name": "Elevance Health, Inc.", "ticker": "ELV", "cik": "0001156039"},
            {"rank": 19, "name": "Fannie Mae", "ticker": "FNMA", "cik": "0000310522"},
            {"rank": 20, "name": "Home Depot, Inc.", "ticker": "HD", "cik": "0000354950"},
            {"rank": 21, "name": "Marathon Petroleum Corporation", "ticker": "MPC", "cik": "0001510295"},
            {"rank": 22, "name": "Phillips 66", "ticker": "PSX", "cik": "0001534701"},
            {"rank": 23, "name": "Valero Energy Corporation", "ticker": "VLO", "cik": "0001035002"},
            {"rank": 24, "name": "Kroger Co.", "ticker": "KR", "cik": "0000056873"},
            {"rank": 25, "name": "Bank of America Corporation", "ticker": "BAC", "cik": "0000070858"},
            {"rank": 26, "name": "Centene Corporation", "ticker": "CNC", "cik": "0001071739"},
            {"rank": 27, "name": "Verizon Communications Inc.", "ticker": "VZ", "cik": "0000732712"},
            {"rank": 28, "name": "Cigna Group", "ticker": "CI", "cik": "0000701221"},
            {"rank": 29, "name": "AT&T Inc.", "ticker": "T", "cik": "0000732717"},
            {"rank": 30, "name": "General Electric Company", "ticker": "GE", "cik": "0000040545"},
            {"rank": 31, "name": "Tesla, Inc.", "ticker": "TSLA", "cik": "0001318605"},
            {"rank": 32, "name": "Walgreens Boots Alliance, Inc.", "ticker": "WBA", "cik": "0001618921"},
            {"rank": 33, "name": "Meta Platforms, Inc.", "ticker": "META", "cik": "0001326801"},
            {"rank": 34, "name": "Comcast Corporation", "ticker": "CMCSA", "cik": "0001166691"},
            {"rank": 35, "name": "Freddie Mac", "ticker": "FMCC", "cik": "0000026214"},
            {"rank": 36, "name": "IBM Corporation", "ticker": "IBM", "cik": "0000051143"},
            {"rank": 37, "name": "Energy Transfer LP", "ticker": "ET", "cik": "0001276187"},
            {"rank": 38, "name": "Procter & Gamble Company", "ticker": "PG", "cik": "0000080424"},
            {"rank": 39, "name": "Archer-Daniels-Midland Company", "ticker": "ADM", "cik": "0000007084"},
            {"rank": 40, "name": "Johnson & Johnson", "ticker": "JNJ", "cik": "0000200406"},
            {"rank": 41, "name": "Dell Technologies Inc.", "ticker": "DELL", "cik": "0001571996"},
            {"rank": 42, "name": "FedEx Corporation", "ticker": "FDX", "cik": "0001048911"},
            {"rank": 43, "name": "UPS, Inc.", "ticker": "UPS", "cik": "0001090727"},
            {"rank": 44, "name": "Lowe's Companies, Inc.", "ticker": "LOW", "cik": "0000060667"},
            {"rank": 45, "name": "Wells Fargo & Company", "ticker": "WFC", "cik": "0000072971"},
            {"rank": 46, "name": "Target Corporation", "ticker": "TGT", "cik": "0000027419"},
            {"rank": 47, "name": "Humana Inc.", "ticker": "HUM", "cik": "0000049071"},
            {"rank": 48, "name": "Lockheed Martin Corporation", "ticker": "LMT", "cik": "0000936468"},
            {"rank": 49, "name": "AbbVie Inc.", "ticker": "ABBV", "cik": "0001551152"},
            {"rank": 50, "name": "Caterpillar Inc.", "ticker": "CAT", "cik": "0000018230"},
        ]

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def build_fortune500_database(self, output_file: str = "data/companies/fortune_500_complete.json") -> List[Company]:
        """Build complete Fortune 500 database."""
        logger.info("Building Fortune 500 database")

        companies = []

        # Start with known companies
        for company_data in self.known_companies:
            try:
                company = Company(
                    cik=company_data["cik"],
                    name=company_data["name"],
                    ticker=company_data["ticker"],
                    fortune_rank=company_data["rank"],
                    industry=self._get_industry_from_ticker(company_data["ticker"]),
                    sector=self._get_sector_from_ticker(company_data["ticker"])
                )
                companies.append(company)
                logger.debug("Added company", name=company.name, rank=company.fortune_rank)
            except Exception as e:
                logger.warning("Failed to create company", company=company_data["name"], error=str(e))

        # Save to file
        await self._save_companies_to_file(companies, output_file)

        logger.info("Fortune 500 database built", total_companies=len(companies))
        return companies

    def _get_industry_from_ticker(self, ticker: str) -> str:
        """Get industry classification from ticker."""
        # Industry mapping for major companies
        industry_map = {
            "WMT": "Retail - General Merchandise",
            "AMZN": "E-commerce & Cloud Computing",
            "AAPL": "Technology Hardware",
            "CVS": "Healthcare Services",
            "UNH": "Healthcare Insurance",
            "XOM": "Oil & Gas",
            "BRK.A": "Financial Services",
            "GOOGL": "Internet & Technology",
            "MCK": "Healthcare Distribution",
            "COR": "Healthcare Distribution",
            "COST": "Retail - Warehouse Clubs",
            "JPM": "Banking",
            "MSFT": "Software & Technology",
            "CAH": "Healthcare Distribution",
            "CVX": "Oil & Gas",
            "F": "Automotive",
            "GM": "Automotive",
            "ELV": "Healthcare Insurance",
            "FNMA": "Financial Services",
            "HD": "Retail - Home Improvement",
            "MPC": "Oil Refining",
            "PSX": "Oil Refining",
            "VLO": "Oil Refining",
            "KR": "Retail - Grocery",
            "BAC": "Banking",
            "CNC": "Healthcare Insurance",
            "VZ": "Telecommunications",
            "CI": "Healthcare Insurance",
            "T": "Telecommunications",
            "GE": "Industrial Conglomerate",
            "TSLA": "Electric Vehicles",
            "WBA": "Retail - Pharmacy",
            "META": "Social Media & Technology",
            "CMCSA": "Media & Telecommunications",
            "FMCC": "Financial Services",
            "IBM": "Technology Services",
            "ET": "Energy Infrastructure",
            "PG": "Consumer Goods",
            "ADM": "Agriculture & Food Processing",
            "JNJ": "Pharmaceuticals",
            "DELL": "Technology Hardware",
            "FDX": "Transportation & Logistics",
            "UPS": "Transportation & Logistics",
            "LOW": "Retail - Home Improvement",
            "WFC": "Banking",
            "TGT": "Retail - General Merchandise",
            "HUM": "Healthcare Insurance",
            "LMT": "Aerospace & Defense",
            "ABBV": "Pharmaceuticals",
            "CAT": "Industrial Machinery",
        }
        return industry_map.get(ticker, "Unknown")

    def _get_sector_from_ticker(self, ticker: str) -> str:
        """Get sector classification from ticker."""
        # Sector mapping for major companies
        sector_map = {
            "WMT": "Consumer Staples", "AMZN": "Consumer Discretionary", "AAPL": "Technology",
            "CVS": "Healthcare", "UNH": "Healthcare", "XOM": "Energy", "BRK.A": "Financial Services",
            "GOOGL": "Technology", "MCK": "Healthcare", "COR": "Healthcare", "COST": "Consumer Staples",
            "JPM": "Financial Services", "MSFT": "Technology", "CAH": "Healthcare", "CVX": "Energy",
            "F": "Consumer Discretionary", "GM": "Consumer Discretionary", "ELV": "Healthcare",
            "FNMA": "Financial Services", "HD": "Consumer Discretionary", "MPC": "Energy",
            "PSX": "Energy", "VLO": "Energy", "KR": "Consumer Staples", "BAC": "Financial Services",
            "CNC": "Healthcare", "VZ": "Telecommunications", "CI": "Healthcare", "T": "Telecommunications",
            "GE": "Industrials", "TSLA": "Consumer Discretionary", "WBA": "Consumer Staples",
            "META": "Technology", "CMCSA": "Telecommunications", "FMCC": "Financial Services",
            "IBM": "Technology", "ET": "Energy", "PG": "Consumer Staples", "ADM": "Consumer Staples",
            "JNJ": "Healthcare", "DELL": "Technology", "FDX": "Industrials", "UPS": "Industrials",
            "LOW": "Consumer Discretionary", "WFC": "Financial Services", "TGT": "Consumer Discretionary",
            "HUM": "Healthcare", "LMT": "Industrials", "ABBV": "Healthcare", "CAT": "Industrials",
        }
        return sector_map.get(ticker, "Unknown")

    async def _save_companies_to_file(self, companies: List[Company], output_file: str) -> None:
        """Save companies to JSON file."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            companies_data = [company.dict() for company in companies]
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(companies_data, f, indent=2, default=str)

            logger.info("Companies saved to file", file=str(output_path), count=len(companies))

        except Exception as e:
            logger.error("Failed to save companies to file", error=str(e))
            raise

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()