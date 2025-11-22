"""
Multi-Source Enhanced Executive Compensation Service

This service combines multiple data sources for maximum coverage and quality:
1. XBRL Pay vs Performance data (our breakthrough discovery)
2. SEC-API.io professional service (when available)
3. Financial Modeling Prep API (backup source)
4. AI-powered LLM extraction (for complex cases)
5. Traditional HTML parsing (fallback)
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import aiohttp
import json

from .breakthrough_xbrl_service import BreakthroughXBRLService

logger = logging.getLogger(__name__)

class MultiSourceEnhancedService:
    """Enhanced service combining multiple data sources for maximum coverage"""
    
    def __init__(self, identity: str = "edgar.analyzer@example.com"):
        """Initialize the multi-source enhanced service"""
        self.identity = identity
        
        # Initialize sub-services
        self.xbrl_service = BreakthroughXBRLService(identity)
        
        # API configurations (would be loaded from environment in production)
        self.sec_api_key = os.getenv('SEC_API_KEY')  # SEC-API.io key
        self.fmp_api_key = os.getenv('FMP_API_KEY')  # Financial Modeling Prep key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # For AI extraction
        
        logger.info(f"Multi-Source Enhanced Service initialized")
        logger.info(f"Available sources: XBRL, SEC-API.io: {bool(self.sec_api_key)}, FMP: {bool(self.fmp_api_key)}, AI: {bool(self.openai_api_key)}")
    
    async def extract_executive_compensation(self, symbol: str, company_name: str) -> Dict:
        """
        Extract executive compensation using multiple sources in priority order:
        1. XBRL (highest quality, our breakthrough)
        2. SEC-API.io (professional service)
        3. Financial Modeling Prep (backup)
        4. AI-powered extraction (complex cases)
        5. Traditional parsing (fallback)
        """
        
        logger.info(f"🚀 Multi-source extraction for {company_name} ({symbol})")
        
        # Track all attempts for comprehensive reporting
        attempts = []
        
        # Method 1: XBRL Pay vs Performance (our breakthrough)
        try:
            logger.info(f"🎯 Attempting XBRL extraction for {symbol}")
            xbrl_result = await self.xbrl_service.extract_executive_compensation(symbol, company_name)
            attempts.append(('xbrl_breakthrough', xbrl_result))
            
            if xbrl_result.get('success'):
                logger.info(f"✅ XBRL extraction successful for {symbol}")
                xbrl_result['extraction_method'] = 'multi_source_xbrl_priority'
                xbrl_result['data_source'] = 'xbrl_pay_vs_performance'
                return xbrl_result
                
        except Exception as e:
            logger.warning(f"XBRL extraction failed for {symbol}: {e}")
            attempts.append(('xbrl_breakthrough', {'success': False, 'error': str(e)}))
        
        # Method 2: SEC-API.io Professional Service
        if self.sec_api_key:
            try:
                logger.info(f"🔧 Attempting SEC-API.io extraction for {symbol}")
                sec_api_result = await self._extract_from_sec_api(symbol, company_name)
                attempts.append(('sec_api_professional', sec_api_result))
                
                if sec_api_result.get('success'):
                    logger.info(f"✅ SEC-API.io extraction successful for {symbol}")
                    return sec_api_result
                    
            except Exception as e:
                logger.warning(f"SEC-API.io extraction failed for {symbol}: {e}")
                attempts.append(('sec_api_professional', {'success': False, 'error': str(e)}))
        
        # Method 3: Financial Modeling Prep API
        if self.fmp_api_key:
            try:
                logger.info(f"📊 Attempting FMP extraction for {symbol}")
                fmp_result = await self._extract_from_fmp(symbol, company_name)
                attempts.append(('fmp_api', fmp_result))
                
                if fmp_result.get('success'):
                    logger.info(f"✅ FMP extraction successful for {symbol}")
                    return fmp_result
                    
            except Exception as e:
                logger.warning(f"FMP extraction failed for {symbol}: {e}")
                attempts.append(('fmp_api', {'success': False, 'error': str(e)}))
        
        # Method 4: AI-Powered LLM Extraction
        if self.openai_api_key:
            try:
                logger.info(f"🤖 Attempting AI extraction for {symbol}")
                ai_result = await self._extract_with_ai(symbol, company_name)
                attempts.append(('ai_llm_extraction', ai_result))
                
                if ai_result.get('success'):
                    logger.info(f"✅ AI extraction successful for {symbol}")
                    return ai_result
                    
            except Exception as e:
                logger.warning(f"AI extraction failed for {symbol}: {e}")
                attempts.append(('ai_llm_extraction', {'success': False, 'error': str(e)}))
        
        # All methods failed - return comprehensive failure report
        logger.error(f"❌ All extraction methods failed for {symbol}")
        
        return {
            'success': False,
            'company_name': company_name,
            'symbol': symbol,
            'reason': 'all_methods_failed',
            'extraction_method': 'multi_source_comprehensive',
            'data_source': 'multi_source_enhanced_service',
            'attempts': attempts,
            'available_sources': {
                'xbrl_breakthrough': True,
                'sec_api_professional': bool(self.sec_api_key),
                'fmp_api': bool(self.fmp_api_key),
                'ai_llm_extraction': bool(self.openai_api_key)
            }
        }
    
    async def _extract_from_sec_api(self, symbol: str, company_name: str) -> Dict:
        """Extract from SEC-API.io professional service"""
        
        try:
            url = f"https://api.sec-api.io/executive-compensation"
            params = {
                'token': self.sec_api_key,
                'ticker': symbol
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert SEC-API.io format to our standard format
                        executives = []
                        for exec_data in data.get('executives', []):
                            executive = {
                                'name': exec_data.get('name', 'Unknown'),
                                'title': exec_data.get('title', 'Unknown'),
                                'total_compensation': exec_data.get('totalCompensation', 0),
                                'salary': exec_data.get('salary', 0),
                                'bonus': exec_data.get('bonus', 0),
                                'stock_awards': exec_data.get('stockAwards', 0),
                                'option_awards': exec_data.get('optionAwards', 0),
                                'other_compensation': exec_data.get('otherCompensation', 0),
                                'data_source': 'sec_api_professional'
                            }
                            executives.append(executive)
                        
                        return {
                            'success': True,
                            'company_name': company_name,
                            'symbol': symbol,
                            'filing_date': data.get('filingDate', 'Unknown'),
                            'data_source': 'sec_api_professional',
                            'executives': executives,
                            'extraction_method': 'sec_api_professional',
                            'quality_score': 0.90  # Professional service = high quality
                        }
                    else:
                        return {'success': False, 'error': f'SEC-API.io returned status {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': f'SEC-API.io request failed: {str(e)}'}
    
    async def _extract_from_fmp(self, symbol: str, company_name: str) -> Dict:
        """Extract from Financial Modeling Prep API"""
        
        try:
            url = f"https://financialmodelingprep.com/api/v4/governance/executive_compensation"
            params = {
                'symbol': symbol,
                'apikey': self.fmp_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert FMP format to our standard format
                        executives = []
                        for exec_data in data:
                            executive = {
                                'name': exec_data.get('nameAndTitle', 'Unknown').split(',')[0].strip(),
                                'title': exec_data.get('nameAndTitle', 'Unknown').split(',')[-1].strip() if ',' in exec_data.get('nameAndTitle', '') else 'Unknown',
                                'total_compensation': exec_data.get('totalCompensation', 0),
                                'salary': exec_data.get('salary', 0),
                                'bonus': exec_data.get('bonus', 0),
                                'stock_awards': exec_data.get('stockAwards', 0),
                                'option_awards': exec_data.get('optionAwards', 0),
                                'other_compensation': exec_data.get('allOtherCompensation', 0),
                                'data_source': 'fmp_api'
                            }
                            executives.append(executive)
                        
                        return {
                            'success': True,
                            'company_name': company_name,
                            'symbol': symbol,
                            'filing_date': 'Unknown',  # FMP doesn't always provide filing date
                            'data_source': 'fmp_api',
                            'executives': executives,
                            'extraction_method': 'fmp_api',
                            'quality_score': 0.85  # Good quality API
                        }
                    else:
                        return {'success': False, 'error': f'FMP returned status {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': f'FMP request failed: {str(e)}'}
    
    async def _extract_with_ai(self, symbol: str, company_name: str) -> Dict:
        """Extract using AI-powered LLM analysis (placeholder for future implementation)"""
        
        # This would implement AI-powered extraction using OpenAI/Claude
        # For now, return a placeholder indicating the capability exists
        
        return {
            'success': False,
            'reason': 'ai_extraction_not_implemented',
            'note': 'AI-powered extraction capability available but not yet implemented',
            'data_source': 'ai_llm_extraction',
            'extraction_method': 'ai_placeholder'
        }
