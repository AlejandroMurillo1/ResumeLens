from pathlib import Path

import pdfplumber

from src.core.ingestion.file_loader import FileLoader, IngestionError


class PdfLoader(FileLoader):
    def load(self, path: Path) -> str:
        try:
            with pdfplumber.open(str(path)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
        except FileNotFoundError:
            raise
        except Exception as exc:
            raise IngestionError(f"Could not read {path} as .pdf") from exc
        return "\n".join(pages)