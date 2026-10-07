from pathlib import Path

from src.core.ingestion.docx_loader import DocxLoader
from src.core.ingestion.file_loader import FileLoader, UnsupportedFileFormatError
from src.core.ingestion.md_loader import MdLoader
from src.core.ingestion.pdf_loader import PdfLoader
from src.core.ingestion.txt_loader import TxtLoader


class LoaderFactory:
    _loaders: dict[str, FileLoader] = {
        ".txt": TxtLoader(),
        ".md": MdLoader(),
        ".pdf": PdfLoader(),
        ".docx": DocxLoader()
    }

    @classmethod
    def get_loader(cls, path: Path) -> FileLoader:
        suffix: str = path.suffix.lower()
        try:
            return cls._loaders[suffix]
        except KeyError:
            raise UnsupportedFileFormatError(
                f"Unsupported file format: '{suffix}'"
            ) from None