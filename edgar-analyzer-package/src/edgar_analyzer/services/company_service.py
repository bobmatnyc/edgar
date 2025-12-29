"""Company data service implementation."""

import json
from pathlib import Path
from typing import List, Optional

import structlog

from edgar_analyzer.config.settings import ConfigService
from edgar_analyzer.models.company import Company
from edgar_analyzer.services.interfaces import ICacheService, ICompanyService, IEdgarApiService

logger = structlog.get_logger(__name__)


class CompanyService(ICompanyService):
    """Company data service implementation."""

    def __init__(
        self,
        config: ConfigService,
        edgar_api_service: IEdgarApiService,
        cache_service: Optional[ICacheService] = None
    ):
        """Initialize company service."""
        self._config = config
        self._edgar_api = edgar_api_service
        self._cache = cache_service
        self._companies_file = Path(config.settings.database.companies_file)
        self._companies_cache: Optional[List[Company]] = None

        logger.info("Company service initialized", companies_file=str(self._companies_file))

    async def _load_companies_from_file(self) -> List[Company]:
        """Load companies from JSON file."""
        try:
            if not self._companies_file.exists():
                logger.warning("Companies file not found", file=str(self._companies_file))
                return []

            with open(self._companies_file, 'r', encoding='utf-8') as f:
                companies_data = json.load(f)

            companies = [Company(**company_data) for company_data in companies_data]
            logger.info("Companies loaded from file", count=len(companies))
            return companies

        except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
            logger.error("Failed to load companies from file", error=str(e))
            return []

    async def _get_companies_cache(self) -> List[Company]:
        """Get companies from cache or load from file."""
        if self._companies_cache is None:
            self._companies_cache = await self._load_companies_from_file()
        return self._companies_cache

    async def get_company_by_cik(self, cik: str) -> Optional[Company]:
        """Get company information by CIK."""
        cik_formatted = str(cik).zfill(10)

        # First check local companies database
        companies = await self._get_companies_cache()
        for company in companies:
            if company.cik == cik_formatted:
                logger.debug("Company found in local database", cik=cik_formatted, name=company.name)
                return company

        # If not found locally, try to fetch from EDGAR API
        try:
            submissions_data = await self._edgar_api.get_company_submissions(cik_formatted)

            if submissions_data:
                company = Company(
                    cik=cik_formatted,
                    name=submissions_data.get('name', 'Unknown'),
                    ticker=submissions_data.get('tickers', [None])[0] if submissions_data.get('tickers') else None,
                    exchange=submissions_data.get('exchanges', [None])[0] if submissions_data.get('exchanges') else None,
                    sic=submissions_data.get('sic'),
                    industry=submissions_data.get('sicDescription'),
                )

                logger.info("Company fetched from EDGAR API", cik=cik_formatted, name=company.name)
                return company

        except Exception as e:
            logger.warning("Failed to fetch company from EDGAR API", cik=cik_formatted, error=str(e))

        logger.warning("Company not found", cik=cik_formatted)
        return None

    async def get_fortune_500_companies(self) -> List[Company]:
        """Get Fortune 500 companies list."""
        companies = await self._get_companies_cache()

        # Filter companies that have fortune_rank
        fortune_companies = [
            company for company in companies
            if company.fortune_rank is not None
        ]

        # Sort by Fortune ranking
        fortune_companies.sort(key=lambda x: x.fortune_rank or 999999)

        logger.info("Fortune 500 companies retrieved", count=len(fortune_companies))
        return fortune_companies

    async def search_companies(self, query: str) -> List[Company]:
        """Search companies by name or ticker."""
        if not query:
            return []

        query_lower = query.lower()
        companies = await self._get_companies_cache()

        matching_companies = []
        for company in companies:
            # Search in company name
            if query_lower in company.name.lower():
                matching_companies.append(company)
                continue

            # Search in ticker
            if company.ticker and query_lower in company.ticker.lower():
                matching_companies.append(company)
                continue

        logger.info("Company search completed", query=query, results=len(matching_companies))
        return matching_companies

    async def update_company(self, company: Company) -> Company:
        """Update company information."""
        companies = await self._get_companies_cache()

        # Find and update existing company
        for i, existing_company in enumerate(companies):
            if existing_company.cik == company.cik:
                companies[i] = company
                self._companies_cache = companies
                await self._save_companies_to_file(companies)
                logger.info("Company updated", cik=company.cik, name=company.name)
                return company

        # Add new company if not found
        companies.append(company)
        self._companies_cache = companies
        await self._save_companies_to_file(companies)
        logger.info("New company added", cik=company.cik, name=company.name)
        return company

    async def _save_companies_to_file(self, companies: List[Company]) -> None:
        """Save companies to JSON file."""
        try:
            # Create backup if enabled
            if self._config.settings.database.backup_enabled:
                await self._create_backup()

            # Ensure directory exists
            self._companies_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict and save
            companies_data = [company.dict() for company in companies]
            with open(self._companies_file, 'w', encoding='utf-8') as f:
                json.dump(companies_data, f, indent=2, default=str)

            logger.info("Companies saved to file", count=len(companies))

        except Exception as e:
            logger.error("Failed to save companies to file", error=str(e))
            raise

    async def _create_backup(self) -> None:
        """Create backup of companies file."""
        try:
            if not self._companies_file.exists():
                return

            backup_dir = Path(self._config.settings.database.backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"companies_backup_{timestamp}.json"

            import shutil
            shutil.copy2(self._companies_file, backup_file)

            logger.info("Companies backup created", backup_file=str(backup_file))

        except Exception as e:
            logger.warning("Failed to create backup", error=str(e))