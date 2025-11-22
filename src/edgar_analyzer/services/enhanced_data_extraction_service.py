"""
Enhanced data extraction service with FMP API integration
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from edgar_analyzer.services.fmp_api_service import FMPApiService
from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.interfaces import IEdgarApiService, ICompanyService

logger = logging.getLogger(__name__)

class EnhancedDataExtractionService:
    """Enhanced data extraction with FMP API primary and EDGAR fallback"""
    
    def __init__(
        self,
        fmp_api_key: Optional[str] = None,
        edgar_api_service: Optional[IEdgarApiService] = None,
        company_service: Optional[ICompanyService] = None
    ):
        """Initialize enhanced data extraction service"""
        
        # Primary: FMP API service
        self.fmp_service = FMPApiService(api_key=fmp_api_key)
        
        # Fallback: EDGAR extraction service
        self.edgar_service = None
        if edgar_api_service and company_service:
            self.edgar_service = DataExtractionService(edgar_api_service, company_service)
        
        logger.info(f"Enhanced data extraction service initialized: FMP enabled, EDGAR fallback: {self.edgar_service is not None}")
    
    async def extract_executive_compensation(
        self, 
        company_name: str, 
        rank: int,
        cik: Optional[str] = None,
        year: int = 2023
    ) -> Optional[Dict]:
        """Extract executive compensation using FMP API with EDGAR fallback"""
        
        logger.info(f"Starting enhanced compensation extraction for {company_name} (rank {rank}, year {year})")
        
        # Step 1: Try FMP API first
        fmp_result = await self._extract_from_fmp(company_name, rank, year)
        
        if fmp_result and self._validate_fmp_data(fmp_result):
            logger.info(f"Successfully extracted from FMP API for {company_name}: {len(fmp_result['executives'])} executives")
            return fmp_result
        
        # Step 2: Fallback to EDGAR if available
        if self.edgar_service and cik:
            logger.info(f"Falling back to EDGAR extraction for {company_name} (CIK: {cik})")
            edgar_result = await self._extract_from_edgar(cik, company_name, rank)
            
            if edgar_result and edgar_result.get("success"):
                logger.info(f"Successfully extracted from EDGAR for {company_name}: {len(edgar_result.get('executives', []))} executives")
                return edgar_result
        
        # Step 3: Return failure
        logger.warning(f"All extraction methods failed for {company_name}")
        return {
            "name": company_name,
            "rank": rank,
            "success": False,
            "executives": [],
            "error": "No data available from FMP API or EDGAR",
            "data_source": "none"
        }
    
    async def _extract_from_fmp(self, company_name: str, rank: int, year: int) -> Optional[Dict]:
        """Extract compensation data from FMP API"""
        
        # Get company symbol
        symbol = self.fmp_service.get_company_symbol(company_name)
        
        if not symbol:
            logger.warning(f"No symbol mapping found for {company_name}")
            return None
        
        try:
            # Get compensation data from FMP
            fmp_data = await self.fmp_service.get_executive_compensation(symbol, year)
            
            if not fmp_data:
                return None
            
            # Format to our internal structure
            formatted_data = self.fmp_service.format_compensation_data(
                fmp_data, company_name, rank
            )
            
            return formatted_data
        
        except Exception as e:
            logger.error(f"FMP extraction failed for {company_name}: {str(e)}")
            return None
    
    async def _extract_from_edgar(self, cik: str, company_name: str, rank: int) -> Optional[Dict]:
        """Extract compensation data from EDGAR (fallback)"""
        
        if not self.edgar_service:
            return None
        
        try:
            # Use existing EDGAR extraction
            edgar_result = await self.edgar_service.extract_executive_compensation(cik)
            
            if edgar_result and edgar_result.get("executives"):
                # Format to match our structure
                return {
                    "name": company_name,
                    "rank": rank,
                    "success": True,
                    "executives": edgar_result["executives"],
                    "data_source": "edgar_fallback",
                    "cik": cik
                }
            
            return None
        
        except Exception as e:
            logger.error(f"EDGAR extraction failed for {company_name} (CIK: {cik}): {str(e)}")
            return None
    
    def _validate_fmp_data(self, data: Dict) -> bool:
        """Validate FMP data quality"""
        
        if not data or not data.get("success"):
            return False
        
        executives = data.get("executives", [])
        
        if not executives:
            return False
        
        # Check for reasonable data
        for exec_data in executives:
            name = exec_data.get("name", "")
            total_comp = exec_data.get("total_compensation", 0)
            
            # Basic validation
            if not name or len(name.split()) < 2:
                logger.warning(f"Invalid executive name: {name}")
                return False
            
            if total_comp <= 0:
                logger.warning(f"Invalid compensation for {name}: {total_comp}")
                return False
            
            # Reasonable compensation range (Fortune companies)
            if total_comp < 100_000 or total_comp > 1_000_000_000:
                logger.warning(f"Compensation out of reasonable range for {name}: {total_comp}")
                return False
        
        return True
    
    async def batch_extract_compensation(
        self, 
        companies: List[Dict],
        year: int = 2023,
        max_concurrent: int = 5
    ) -> List[Dict]:
        """Extract compensation for multiple companies concurrently"""
        
        logger.info(f"Starting batch compensation extraction for {len(companies)} companies (year {year})")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single(company: Dict) -> Dict:
            async with semaphore:
                return await self.extract_executive_compensation(
                    company_name=company["name"],
                    rank=company["rank"],
                    cik=company.get("cik"),
                    year=year
                )
        
        # Execute all extractions concurrently
        tasks = [extract_single(company) for company in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = 0
        failed = 0
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Extraction failed with exception for {companies[i]['name']}: {str(result)}")
                processed_results.append({
                    "name": companies[i]["name"],
                    "rank": companies[i]["rank"],
                    "success": False,
                    "executives": [],
                    "error": str(result),
                    "data_source": "error"
                })
                failed += 1
            else:
                processed_results.append(result)
                if result and result.get("success"):
                    successful += 1
                else:
                    failed += 1
        
        logger.info(f"Batch extraction completed: {successful}/{len(companies)} successful, {failed} failed")
        
        return processed_results
    
    async def close(self):
        """Close all services"""
        if self.fmp_service:
            await self.fmp_service.close()
        
        logger.info("Enhanced data extraction service closed")
