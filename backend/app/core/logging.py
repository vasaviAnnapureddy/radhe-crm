"""One log format for the whole backend.

Rule: never log passwords, tokens, connection strings or customer phone numbers.
"""
import logging

from app.core.config import get_settings


def setup_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%d %b %Y %H:%M:%S",
    )
    # SQLAlchemy can print every query with its values; keep it quiet.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
