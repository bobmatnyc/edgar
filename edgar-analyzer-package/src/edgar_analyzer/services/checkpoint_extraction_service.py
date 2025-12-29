"""Checkpoint-aware data extraction service with resume functionality."""

import asyncio
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import structlog

from edgar_analyzer.models.company import Company
from edgar_analyzer.models.intermediate_data import (
    AnalysisCheckpoint,
    CheckpointManager,
    CompanyExtractionData,
    ExtractionStatus,
)
from edgar_analyzer.services.interfaces import (
    ICompanyService,
    IDataExtractionService,
)

logger = structlog.get_logger(__name__)


class CheckpointExtractionService:
    """Data extraction service with checkpoint/resume functionality."""

    def __init__(
        self,
        data_extraction_service: IDataExtractionService,
        company_service: ICompanyService,
        checkpoint_manager: Optional[CheckpointManager] = None
    ):
        """Initialize checkpoint extraction service."""
        self._data_extraction = data_extraction_service
        self._company_service = company_service
        self._checkpoint_manager = checkpoint_manager or CheckpointManager()

        logger.info("Checkpoint extraction service initialized")

    async def start_analysis(
        self,
        company_ciks: List[str],
        target_year: int,
        analysis_years: Optional[List[int]] = None,
        analysis_id: Optional[str] = None,
        config: Optional[dict] = None
    ) -> AnalysisCheckpoint:
        """Start a new analysis or resume an existing one."""

        # Generate analysis ID if not provided
        if analysis_id is None:
            analysis_id = f"fortune500_{target_year}_{uuid.uuid4().hex[:8]}"

        # Default to 5-year analysis
        if analysis_years is None:
            analysis_years = [target_year - 4, target_year - 3, target_year - 2, target_year - 1, target_year]

        # Try to load existing checkpoint
        checkpoint = self._checkpoint_manager.load_checkpoint(analysis_id, target_year)

        if checkpoint:
            logger.info(
                "Resuming existing analysis",
                analysis_id=analysis_id,
                progress=f"{checkpoint.progress_percentage:.1f}%",
                completed=checkpoint.completed_companies,
                total=checkpoint.total_companies
            )
        else:
            # Create new checkpoint
            logger.info("Starting new analysis", analysis_id=analysis_id, companies=len(company_ciks))

            # Get company information
            companies_data = []
            for cik in company_ciks:
                company = await self._company_service.get_company_by_cik(cik)
                if company:
                    company_data = CompanyExtractionData(
                        cik=company.cik,
                        name=company.name,
                        ticker=company.ticker,
                        fortune_rank=company.fortune_rank,
                        sector=company.sector,
                        industry=company.industry,
                        status=ExtractionStatus.PENDING
                    )
                    companies_data.append(company_data)

            checkpoint = AnalysisCheckpoint(
                analysis_id=analysis_id,
                target_year=target_year,
                analysis_years=analysis_years,
                total_companies=len(companies_data),
                config=config or {},
                companies=companies_data
            )

            # Save initial checkpoint
            self._checkpoint_manager.save_checkpoint(checkpoint)

        return checkpoint

    async def extract_company_data(
        self,
        checkpoint: AnalysisCheckpoint,
        company_cik: str,
        max_retries: int = 3
    ) -> bool:
        """Extract data for a single company with error handling."""

        company_data = checkpoint.get_company_by_cik(company_cik)
        if not company_data:
            logger.warning("Company not found in checkpoint", cik=company_cik)
            return False

        # Skip if already completed
        if company_data.status == ExtractionStatus.COMPLETED:
            logger.debug("Company already completed", cik=company_cik, name=company_data.name)
            return True

        # Update status to in progress
        company_data.status = ExtractionStatus.IN_PROGRESS
        company_data.extraction_start_time = datetime.now()

        try:
            logger.info("Extracting company data", cik=company_cik, name=company_data.name)

            # Extract data for each year
            for year in checkpoint.analysis_years:
                await self._extract_year_data(company_data, year)

                # Small delay to respect rate limits
                await asyncio.sleep(0.1)

            # Calculate derived metrics
            self._calculate_company_metrics(company_data)

            # Mark as completed
            company_data.status = ExtractionStatus.COMPLETED
            company_data.extraction_end_time = datetime.now()
            checkpoint.completed_companies += 1

            logger.info(
                "Company extraction completed",
                cik=company_cik,
                name=company_data.name,
                years=len(checkpoint.analysis_years)
            )

            return True

        except Exception as e:
            company_data.retry_count += 1
            error_msg = str(e)

            if company_data.retry_count >= max_retries:
                # Mark as failed after max retries
                company_data.status = ExtractionStatus.FAILED
                company_data.error_message = error_msg
                company_data.extraction_end_time = datetime.now()
                checkpoint.failed_companies += 1

                logger.error(
                    "Company extraction failed after retries",
                    cik=company_cik,
                    name=company_data.name,
                    error=error_msg,
                    retries=company_data.retry_count
                )

                return False
            else:
                # Reset to pending for retry
                company_data.status = ExtractionStatus.PENDING
                company_data.error_message = f"Retry {company_data.retry_count}: {error_msg}"

                logger.warning(
                    "Company extraction failed, will retry",
                    cik=company_cik,
                    name=company_data.name,
                    error=error_msg,
                    retry=company_data.retry_count
                )

                return False

    async def _extract_year_data(self, company_data: CompanyExtractionData, year: int) -> None:
        """Extract data for a specific year."""
        try:
            # Extract tax expense data
            tax_expense = await self._data_extraction.extract_tax_expense(company_data.cik, year)
            if tax_expense:
                company_data.tax_data[year] = {
                    "total_tax_expense": float(tax_expense.total_tax_expense),
                    "current_tax_expense": float(tax_expense.current_tax_expense),
                    "deferred_tax_expense": float(tax_expense.deferred_tax_expense),
                    "effective_tax_rate": float(tax_expense.effective_tax_rate) if tax_expense.effective_tax_rate else None,
                    "fiscal_year": tax_expense.fiscal_year,
                    "filing_date": tax_expense.filing_date.isoformat() if tax_expense.filing_date else None
                }

            # Extract executive compensation data
            compensations = await self._data_extraction.extract_executive_compensation(company_data.cik, year)
            if compensations:
                company_data.compensation_data[year] = [
                    {
                        "name": comp.name,
                        "title": comp.title,
                        "total_compensation": float(comp.total_compensation),
                        "salary": float(comp.salary),
                        "bonus": float(comp.bonus),
                        "stock_awards": float(comp.stock_awards),
                        "option_awards": float(comp.option_awards),
                        "other_compensation": float(comp.other_compensation),
                        "fiscal_year": comp.fiscal_year
                    }
                    for comp in compensations
                ]

        except Exception as e:
            logger.warning(
                "Failed to extract data for year",
                cik=company_data.cik,
                year=year,
                error=str(e)
            )
            # Continue with other years even if one fails

    def _calculate_company_metrics(self, company_data: CompanyExtractionData) -> None:
        """Calculate derived metrics for a company."""
        try:
            # Calculate total compensation by year
            for year, compensations in company_data.compensation_data.items():
                total_comp = sum(Decimal(str(comp["total_compensation"])) for comp in compensations)
                company_data.total_compensation_by_year[year] = total_comp

            # Calculate compensation vs tax ratios
            for year in company_data.tax_data.keys():
                tax_expense = company_data.tax_data[year].get("total_tax_expense", 0)
                total_comp = float(company_data.total_compensation_by_year.get(year, 0))

                if tax_expense and tax_expense > 0:
                    ratio = total_comp / tax_expense
                    company_data.compensation_vs_tax_ratios[year] = ratio
                else:
                    company_data.compensation_vs_tax_ratios[year] = None

        except Exception as e:
            logger.warning(
                "Failed to calculate metrics",
                cik=company_data.cik,
                error=str(e)
            )

    async def process_all_companies(
        self,
        checkpoint: AnalysisCheckpoint,
        save_frequency: int = 5,
        progress_callback: Optional[callable] = None
    ) -> AnalysisCheckpoint:
        """Process all pending companies in the checkpoint."""

        pending_companies = checkpoint.get_pending_companies()
        logger.info(
            "Processing companies",
            pending=len(pending_companies),
            completed=checkpoint.completed_companies,
            failed=checkpoint.failed_companies
        )

        companies_processed = 0

        for company_data in pending_companies:
            # Extract data for this company
            success = await self.extract_company_data(checkpoint, company_data.cik)

            companies_processed += 1

            # Progress callback
            if progress_callback:
                progress_callback(
                    checkpoint.completed_companies + checkpoint.failed_companies,
                    checkpoint.total_companies
                )

            # Save checkpoint periodically
            if companies_processed % save_frequency == 0:
                self._checkpoint_manager.save_checkpoint(checkpoint)
                logger.info(
                    "Checkpoint saved",
                    processed=companies_processed,
                    completed=checkpoint.completed_companies,
                    failed=checkpoint.failed_companies
                )

        # Final checkpoint save
        self._checkpoint_manager.save_checkpoint(checkpoint)

        logger.info(
            "All companies processed",
            total=checkpoint.total_companies,
            completed=checkpoint.completed_companies,
            failed=checkpoint.failed_companies,
            success_rate=f"{checkpoint.success_rate:.1f}%"
        )

        return checkpoint

    def get_checkpoint_manager(self) -> CheckpointManager:
        """Get the checkpoint manager instance."""
        return self._checkpoint_manager