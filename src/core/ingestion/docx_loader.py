from pathlib import Path

import docx 

from src.core.ingestion.file_loader import FileLoader, IngestionError


class DocxLoader(FileLoader):
    def load(self, path: Path) -> str:
        try:
            document = docx.Document(str(path))
        except Exception as exc:
            raise IngestionError(f"Could not read {path} as .docx") from exc
        return "\n".join(paragraph.text for paragraph in document.paragraphs)