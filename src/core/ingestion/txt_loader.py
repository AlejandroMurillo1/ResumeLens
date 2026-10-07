from pathlib import Path

from src.core.ingestion.file_loader import FileLoader, IngestionError


class TxtLoader(FileLoader):
    def load(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise IngestionError(f"Could not decode {path} as UTF-8") from exc