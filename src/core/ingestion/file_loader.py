from abc import ABC, abstractmethod
from pathlib import Path


class IngestionError(Exception):
    """Base exception for anything that goes wrong while reading a file."""


class UnsupportedFileFormatError(IngestionError):
    """Raised when the file extension has no registered loader."""


class FileLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> str:
        """Return the plain-text content of the file at `path`."""
        raise NotImplementedError