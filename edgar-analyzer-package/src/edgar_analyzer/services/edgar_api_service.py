"""SEC EDGAR API service implementation."""

import asyncio
import time
from typing import Dict, Optional

import aiohttp
import structlog
from aiohttp import ClientTimeout

from edgar_analyzer.config.settings import ConfigService
from edgar_analyzer.services.interfaces import ICacheService, IEdgarApiService

logger = structlog.get_logger(__name__)


class EdgarApiService(IEdgarApiService):
    """SEC EDGAR API service implementation."""

    def __init__(self, config: ConfigService, cache_service: Optional[ICacheService] = None):
        """Initialize EDGAR API service."""
        self._config = config
        self._cache = cache_service
        self._edgar_config = config.get_edgar_config()
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0.0

        logger.info("EDGAR API service initialized", config=self._edgar_config)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self._edgar_config["timeout"])
            headers = {
                "User-Agent": self._edgar_config["user_agent"],
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self._session

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        delay = self._edgar_config["rate_limit_delay"]

        if time_since_last < delay:
            sleep_time = delay - time_since_last
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()

    async def _make_request(self, url: str, cache_key: Optional[str] = None) -> Dict:
        """Make HTTP request with caching and error handling."""
        # Check cache first
        if cache_key and self._cache:
            cached_data = await self._cache.get(cache_key)
            if cached_data:
                logger.debug("Cache hit", cache_key=cache_key)
                return cached_data

        # Rate limiting
        await self._rate_limit()

        session = await self._get_session()

        for attempt in range(self._edgar_config["max_retries"]):
            try:
                logger.debug("Making API request", url=url, attempt=attempt + 1)

                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Cache the response
                    if cache_key and self._cache:
                        await self._cache.set(cache_key, data)
                        logger.debug("Data cached", cache_key=cache_key)

                    logger.info("API request successful", url=url, status=response.status)
                    return data

            except aiohttp.ClientError as e:
                logger.warning(
                    "API request failed",
                    url=url,
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt == self._edgar_config["max_retries"] - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise Exception(f"Failed to fetch data from {url} after {self._edgar_config['max_retries']} attempts")

    async def get_company_submissions(self, cik: str) -> Dict:
        """Get company submission history."""
        cik_formatted = str(cik).zfill(10)
        url = f"{self._edgar_config['base_url']}/submissions/CIK{cik_formatted}.json"
        cache_key = f"submissions:{cik_formatted}"

        logger.info("Fetching company submissions", cik=cik_formatted)
        return await self._make_request(url, cache_key)

    async def get_company_facts(self, cik: str) -> Dict:
        """Get company XBRL facts."""
        cik_formatted = str(cik).zfill(10)
        url = f"{self._edgar_config['base_url']}/api/xbrl/companyfacts/CIK{cik_formatted}.json"
        cache_key = f"facts:{cik_formatted}"

        logger.info("Fetching company facts", cik=cik_formatted)
        return await self._make_request(url, cache_key)

    async def get_filing_content(self, accession_number: str, cik: str) -> str:
        """Get filing content by accession number."""
        # This would need to be implemented based on specific filing URL structure
        # For now, return empty string as placeholder
        logger.warning("Filing content retrieval not yet implemented")
        return ""

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("EDGAR API session closed")