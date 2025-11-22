"""
Financial Modeling Prep API service for executive compensation data
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FMPApiService:
    """Financial Modeling Prep API service for executive compensation"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize FMP API service"""
        self.api_key = api_key or "demo"  # Use demo key for testing
        self.base_url = "https://financialmodelingprep.com/api"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Company symbol mappings for Fortune 1-100
        self.company_symbols = {
            # Fortune 1-10
            "Walmart Inc.": "WMT",
            "Amazon.com Inc.": "AMZN", 
            "Apple Inc.": "AAPL",
            "CVS Health Corporation": "CVS",
            "UnitedHealth Group Incorporated": "UNH",
            "Exxon Mobil Corporation": "XOM",
            "Berkshire Hathaway Inc.": "BRK.A",
            "Alphabet Inc.": "GOOGL",
            "McKesson Corporation": "MCK",
            "Cencora Inc.": "COR",
            
            # Fortune 11-20
            "Costco Wholesale Corporation": "COST",
            "JPMorgan Chase & Co.": "JPM",
            "Microsoft Corporation": "MSFT",
            "Cardinal Health, Inc.": "CAH",
            "Chevron Corporation": "CVX",
            "Ford Motor Company": "F",
            "General Motors Company": "GM",
            "Elevance Health, Inc.": "ELV",
            "Home Depot, Inc.": "HD",
            
            # Fortune 21-30
            "Marathon Petroleum Corporation": "MPC",
            "Phillips 66": "PSX",
            "Valero Energy Corporation": "VLO",
            "Kroger Co.": "KR",
            "Bank of America Corporation": "BAC",
            "Centene Corporation": "CNC",
            "Verizon Communications Inc.": "VZ",
            "Cigna Group": "CI",
            "AT&T Inc.": "T",
            "General Electric Company": "GE",
            
            # Fortune 31-40
            "Tesla, Inc.": "TSLA",
            "Walgreens Boots Alliance, Inc.": "WBA",
            "Meta Platforms, Inc.": "META",
            "Comcast Corporation": "CMCSA",
            "IBM Corporation": "IBM",
            "Energy Transfer LP": "ET",
            "Procter & Gamble Company": "PG",
            "Archer-Daniels-Midland Company": "ADM",
            "Johnson & Johnson": "JNJ",
            
            # Fortune 41-50
            "Dell Technologies Inc.": "DELL",
            "FedEx Corporation": "FDX",
            "UPS, Inc.": "UPS",
            "Lowe's Companies, Inc.": "LOW",
            "Wells Fargo & Company": "WFC",
            "Target Corporation": "TGT",
            "Humana Inc.": "HUM",
            "Lockheed Martin Corporation": "LMT",
            "AbbVie Inc.": "ABBV",
            "Caterpillar Inc.": "CAT"
        }
        
        api_key_type = "demo" if api_key is None else "provided"
        logger.info(f"FMP API service initialized with {api_key_type} API key")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def get_company_symbol(self, company_name: str) -> Optional[str]:
        """Get stock symbol for company name"""
        return self.company_symbols.get(company_name)
    
    async def get_executive_compensation(self, symbol: str, year: int = 2023) -> Optional[Dict]:
        """Get executive compensation data from FMP API"""
        
        try:
            session = await self._get_session()
            
            # FMP executive compensation endpoint
            url = f"{self.base_url}/v4/executive-compensation"
            params = {
                "symbol": symbol,
                "year": year,
                "apikey": self.api_key
            }
            
            logger.info(f"Fetching executive compensation for {symbol} year {year}")
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and isinstance(data, list) and len(data) > 0:
                        logger.info(f"Successfully retrieved compensation data for {symbol}: {len(data)} executives")
                        return {
                            "symbol": symbol,
                            "year": year,
                            "executives": data,
                            "data_source": "fmp_api",
                            "retrieved_at": datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"No compensation data found for {symbol}")
                        return None
                
                elif response.status == 429:
                    logger.warning(f"Rate limit exceeded for {symbol}")
                    return None

                elif response.status == 401:
                    logger.error(f"API key invalid or expired for {symbol}")
                    return None

                else:
                    logger.error(f"API request failed for {symbol}: status {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error fetching compensation data for {symbol}: {str(e)}")
            return None
    
    async def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """Get company profile information"""
        
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/v3/profile/{symbol}"
            params = {"apikey": self.api_key}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        return data[0]
                
                return None
        
        except Exception as e:
            logger.error(f"Error fetching company profile for {symbol}: {str(e)}")
            return None
    
    def format_compensation_data(self, fmp_data: Dict, company_name: str, rank: int) -> Dict:
        """Format FMP compensation data to our internal format"""
        
        executives = []
        
        for exec_data in fmp_data.get("executives", []):
            # Map FMP fields to our format
            executive = {
                "name": exec_data.get("name", ""),
                "title": exec_data.get("title", ""),
                "total_compensation": self._safe_int(exec_data.get("totalCompensation", 0)),
                "salary": self._safe_int(exec_data.get("salary", 0)),
                "bonus": self._safe_int(exec_data.get("bonus", 0)),
                "stock_awards": self._safe_int(exec_data.get("stockAwards", 0)),
                "option_awards": self._safe_int(exec_data.get("optionAwards", 0)),
                "other_compensation": self._safe_int(exec_data.get("otherCompensation", 0))
            }
            
            # Calculate other compensation if not provided
            if executive["other_compensation"] == 0:
                calculated_other = (
                    executive["total_compensation"] - 
                    executive["salary"] - 
                    executive["bonus"] - 
                    executive["stock_awards"] - 
                    executive["option_awards"]
                )
                executive["other_compensation"] = max(0, calculated_other)
            
            executives.append(executive)
        
        return {
            "name": company_name,
            "rank": rank,
            "success": True,
            "executives": executives,
            "data_source": "fmp_api",
            "symbol": fmp_data.get("symbol", ""),
            "year": fmp_data.get("year", 2023),
            "retrieved_at": fmp_data.get("retrieved_at", datetime.now().isoformat())
        }
    
    def _safe_int(self, value) -> int:
        """Safely convert value to integer"""
        if value is None:
            return 0
        
        try:
            if isinstance(value, str):
                # Remove commas and dollar signs
                value = value.replace(",", "").replace("$", "")
            return int(float(value))
        except (ValueError, TypeError):
            return 0
