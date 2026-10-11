"""Stage 1: regex-based extraction.

The data classes live in ``src.core.models.models`` (single source of truth);
they are re-exported here to match the package layout of the class diagram.
"""

from src.core.models.models import ContactInfo, RawProfile

from .content_extractor import ContentExtractor

__all__ = ["ContentExtractor", "ContactInfo", "RawProfile"]
