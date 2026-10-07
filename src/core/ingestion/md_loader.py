from src.core.ingestion.txt_loader import TxtLoader


class MdLoader(TxtLoader):
    """Markdown is read as plain text on purpose: its headings are a
    reliable anchor for section detection in the extraction stage."""