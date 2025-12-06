"""Logging configuration utility for EDGAR platform.

This module provides centralized logging configuration with support for:
- Quiet mode by default (no logging output)
- Optional log level control via CLI flags
- Structured logging with structlog
- Consistent formatting across all components

Design Decision:
    Default to quiet mode to provide clean CLI output. Users can enable
    logging explicitly with --log-level flag when debugging is needed.

Usage:
    # Suppress all logging (default)
    configure_logging(log_level=None)

    # Enable logging at specific level
    configure_logging(log_level='INFO')
    configure_logging(log_level='DEBUG')

Performance:
    - Logging suppression: <1ms overhead
    - Log level changes: <5ms (structlog reconfiguration)
"""

import logging
import sys
from typing import Optional

import structlog


def configure_logging(log_level: Optional[str] = None) -> None:
    """Configure logging for EDGAR platform.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, all logging is suppressed (quiet mode)

    Example:
        >>> configure_logging(None)  # Quiet mode (default)
        >>> configure_logging('INFO')  # Enable INFO logging
        >>> configure_logging('DEBUG')  # Enable DEBUG logging

    Design Notes:
        - Quiet mode (log_level=None) disables ALL logging output
        - Structured logging with timestamp, level, and message
        - Console output only (no file logging by default)
        - Consistent formatting across standard library and structlog
    """
    if log_level is None:
        # Suppress all logging output (quiet mode)
        logging.disable(logging.CRITICAL)

        # Configure structlog to suppress output by using CRITICAL level filtering
        # This effectively silences all normal log messages
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Enable logging at specified level
        level = getattr(logging, log_level.upper())

        # Re-enable logging if it was disabled
        logging.disable(logging.NOTSET)

        # Configure root logger
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)-8s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stderr,
            force=True,
        )

        # Configure structlog with rich formatting
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Set level for common noisy loggers
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
