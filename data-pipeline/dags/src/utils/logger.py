"""
Logger for the LinkedLens Vector Integration.
"""

import sys
from pathlib import Path

from loguru import logger

from src.config.settings import settings

# Remove default logger
logger.remove()

# Determine log level
log_level = settings.logging.level.upper()

# Configure console logger
logger.add(
    sys.stderr,
    format=settings.logging.format,
    level=log_level,
    colorize=True,
)

# Add file logger if path is specified
if settings.logging.file_path:
    # Create directory if it doesn't exist
    log_file = Path(settings.logging.file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Add file logger
    logger.add(
        log_file,
        format=settings.logging.format,
        level=log_level,
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="1 month",  # Keep logs for 1 month
    )

logger.info("Logger initialized with level: {}", log_level)