"""
Logging Configuration
"""

import logging
import sys
from app.config import settings

# Create logger
logger = logging.getLogger("sherlocke_homes")
logger.setLevel(getattr(logging, settings.LOG_LEVEL))

# Create console handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(getattr(logging, settings.LOG_LEVEL))

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)
