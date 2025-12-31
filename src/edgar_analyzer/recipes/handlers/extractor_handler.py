"""Extractor step handler for executing EDGAR data extractors.

This handler executes extractor steps (SCTAdapter, TaxAdapter) by:
1. Looking up the extractor class in the registry
2. Resolving input parameters from context
3. Calling the extractor's extract() method for each filing
4. Collecting and mapping results to step outputs
"""

from typing import Any

import structlog

from edgar_analyzer.extractors.fortune100.sct_adapter import SCTAdapter
from edgar_analyzer.extractors.fortune100.tax_adapter import TaxAdapter
from edgar_analyzer.recipes.context import ExecutionContext
from edgar_analyzer.recipes.schema import Step

logger = structlog.get_logger(__name__)


# Registry of available extractors
# Maps extractor class names to their implementations
EXTRACTOR_REGISTRY: dict[str, type] = {
    "SCTAdapter": SCTAdapter,
    "TaxAdapter": TaxAdapter,
}


class ExtractorHandler:
    """Handler for executing extractor steps in recipes.

    Extractors process SEC filings to extract structured data (executive compensation,
    tax data, etc.). This handler manages the extraction process for each filing.

    Example recipe step:
        - name: extract_tax_tables
          type: extractor
          extractor:
            extractor: TaxAdapter
            filing_type: "10-K"
          inputs:
            filings: $steps.fetch_10k_filings.filings
          outputs:
            - tax_data

    The handler expects inputs to contain:
    - filings: List of filing dicts with {cik, company, html, filing_date, etc.}
      OR
    - companies: List of company dicts (for backward compatibility)
    """

    async def execute(self, step: Step, context: ExecutionContext) -> dict[str, Any]:
        """Execute an extractor step.

        Args:
            step: Step configuration with extractor settings
            context: Execution context with parameters and step outputs

        Returns:
            Dictionary with extraction results:
            {
                "tax_data": [  # or "sct_data" depending on extractor
                    {
                        "company": "Apple Inc.",
                        "cik": "0000320193",
                        "executives": [...],  # for SCT
                        # or
                        "tax_years": [...],   # for Tax
                    }
                ],
                "success_count": 5,
                "failure_count": 2,
                "errors": [
                    {
                        "company": "Failed Corp",
                        "cik": "0001234567",
                        "error": "ValueError: No tax table found"
                    }
                ]
            }

        Raises:
            ValueError: If extractor config is invalid or extractor is unknown
        """
        if not step.extractor:
            raise ValueError(
                f"Step '{step.name}' is type 'extractor' but has no extractor config"
            )

        extractor_name = step.extractor.extractor
        filing_type = step.extractor.filing_type

        logger.info(
            "executing_extractor_step",
            step_name=step.name,
            extractor=extractor_name,
            filing_type=filing_type,
        )

        # Look up extractor class in registry
        if extractor_name not in EXTRACTOR_REGISTRY:
            raise ValueError(
                f"Unknown extractor '{extractor_name}'. "
                f"Available extractors: {list(EXTRACTOR_REGISTRY.keys())}"
            )

        extractor_class = EXTRACTOR_REGISTRY[extractor_name]

        # Resolve inputs from context
        resolved_inputs = {}
        if step.inputs:
            resolved_inputs = context.resolve_value(step.inputs)

        logger.debug(
            "resolved_extractor_inputs",
            step_name=step.name,
            inputs=resolved_inputs,
        )

        # Extract filings or companies from inputs
        filings = resolved_inputs.get("filings", [])
        companies = resolved_inputs.get("companies", [])

        # Determine what to process
        items_to_process = []
        if filings:
            items_to_process = filings
            logger.info("processing_filings", count=len(filings))
        elif companies:
            # For backward compatibility, support company list
            # Each company should have {cik, name, ticker}
            items_to_process = companies
            logger.info("processing_companies", count=len(companies))
        else:
            logger.warning(
                "no_filings_or_companies",
                step_name=step.name,
                inputs=list(resolved_inputs.keys()),
            )
            # Return empty results
            return {
                "extracted_data": [],
                "success_count": 0,
                "failure_count": 0,
                "errors": [],
            }

        # Process each filing/company
        extracted_data = []
        errors = []
        success_count = 0
        failure_count = 0

        for item in items_to_process:
            # Extract company metadata
            cik = item.get("cik", "")
            company = item.get("company") or item.get("name", "Unknown")
            html = item.get("html", "")
            filing_date = item.get("filing_date", "")
            fiscal_year_end = item.get("fiscal_year_end", "")

            logger.debug(
                "processing_item",
                company=company,
                cik=cik,
                filing_type=filing_type,
                has_html=bool(html),
            )

            # Skip if no HTML content
            if not html:
                logger.warning(
                    "skipping_item_no_html",
                    company=company,
                    cik=cik,
                )
                failure_count += 1
                errors.append(
                    {
                        "company": company,
                        "cik": cik,
                        "error": "No HTML content available",
                    }
                )
                continue

            try:
                # Instantiate extractor
                extractor = extractor_class(company=company, cik=cik)

                # Call extractor's extract() method
                result = await extractor.extract(
                    filing_type=filing_type,
                    html=html,
                    company=company,
                    cik=cik,
                    filing_date=filing_date,
                    fiscal_year_end=fiscal_year_end,
                )

                if result:
                    extracted_data.append(result)
                    success_count += 1
                    logger.info(
                        "extraction_successful",
                        company=company,
                        cik=cik,
                        extractor=extractor_name,
                    )
                else:
                    # Extractor returned None (invalid filing type or extraction failed)
                    failure_count += 1
                    errors.append(
                        {
                            "company": company,
                            "cik": cik,
                            "error": "Extractor returned None (invalid filing type or extraction failed)",
                        }
                    )
                    logger.warning(
                        "extraction_returned_none",
                        company=company,
                        cik=cik,
                        extractor=extractor_name,
                    )

            except Exception as e:
                # Log error and continue processing other filings
                failure_count += 1
                error_msg = f"{type(e).__name__}: {str(e)}"
                errors.append(
                    {
                        "company": company,
                        "cik": cik,
                        "error": error_msg,
                    }
                )
                logger.error(
                    "extraction_failed",
                    company=company,
                    cik=cik,
                    extractor=extractor_name,
                    error=error_msg,
                )

        # Map results to step outputs
        logger.info(
            "extractor_step_complete",
            step_name=step.name,
            success_count=success_count,
            failure_count=failure_count,
            total=len(items_to_process),
        )

        # Determine output key based on extractor type
        # For compatibility with existing recipes
        if extractor_name == "SCTAdapter":
            data_key = "sct_data"
        elif extractor_name == "TaxAdapter":
            data_key = "tax_data"
        else:
            data_key = "extracted_data"

        return {
            data_key: extracted_data,
            "success_count": success_count,
            "failure_count": failure_count,
            "errors": errors,
        }
