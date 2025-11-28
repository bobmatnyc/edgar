"""Dependency injection container."""

from dependency_injector import containers, providers

from edgar_analyzer.config.settings import ConfigService
from edgar_analyzer.services.cache_service import CacheService
from edgar_analyzer.services.company_service import CompanyService
from edgar_analyzer.services.data_extraction_service import DataExtractionService
from edgar_analyzer.services.edgar_api_service import EdgarApiService
from edgar_analyzer.services.enhanced_report_service import EnhancedReportService
from edgar_analyzer.services.historical_analysis_service import HistoricalAnalysisService
from edgar_analyzer.services.llm_service import LLMService
from edgar_analyzer.services.parallel_processing_service import ParallelProcessingService
from edgar_analyzer.services.report_service import ReportService
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer
from edgar_analyzer.services.example_parser import ExampleParser
from edgar_analyzer.services.prompt_generator import PromptGenerator


class Container(containers.DeclarativeContainer):
    """Application dependency injection container."""

    # Configuration
    config = providers.Singleton(ConfigService)

    # Core services
    cache_service = providers.Singleton(
        CacheService,
        config=config
    )

    edgar_api_service = providers.Singleton(
        EdgarApiService,
        config=config,
        cache_service=cache_service
    )

    llm_service = providers.Singleton(
        LLMService
    )

    company_service = providers.Singleton(
        CompanyService,
        config=config,
        edgar_api_service=edgar_api_service,
        cache_service=cache_service
    )

    data_extraction_service = providers.Singleton(
        DataExtractionService,
        edgar_api_service=edgar_api_service,
        company_service=company_service,
        cache_service=cache_service,
        llm_service=llm_service
    )

    parallel_processing_service = providers.Singleton(
        ParallelProcessingService,
        max_concurrent=5,  # Conservative for SEC API
        rate_limit_delay=0.1
    )

    historical_analysis_service = providers.Singleton(
        HistoricalAnalysisService,
        edgar_api_service=edgar_api_service,
        data_extraction_service=data_extraction_service,
        company_service=company_service,
        cache_service=cache_service
    )

    report_service = providers.Singleton(
        ReportService,
        data_extraction_service=data_extraction_service,
        config=config
    )

    enhanced_report_service = providers.Singleton(
        EnhancedReportService,
        data_extraction_service=data_extraction_service,
        historical_analysis_service=historical_analysis_service,
        config=config
    )

    # Example Parser services (Phase 1 MVP)
    schema_analyzer = providers.Singleton(
        SchemaAnalyzer
    )

    example_parser = providers.Singleton(
        ExampleParser,
        schema_analyzer=schema_analyzer
    )

    prompt_generator = providers.Singleton(
        PromptGenerator
    )

    # CLI commands wiring
    wiring_config = containers.WiringConfiguration(
        modules=[
            "edgar_analyzer.cli.main",
        ]
    )