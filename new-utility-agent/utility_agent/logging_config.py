import logging
import structlog
from .config import Config
import sys

def setup_logging():
    """Sets up basic logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:     %(message)s",
        stream=sys.stdout,
    )

