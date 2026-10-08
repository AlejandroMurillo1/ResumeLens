from pyformlang.fst import FST

from src.core.normalization.transducers import CaseFoldingTransducer


class SkillNormalizer:
    def __init__(self, case_folder: CaseFoldingTransducer, vocabulary: FST) -> None:
        self._case_folder = case_folder
        self._vocabulary = vocabulary

    def normalize(self, raw: str) -> str | None:
        cleaned = self._case_folder.apply(raw.strip())
        results = list(self._vocabulary.translate([cleaned]))
        if not results:
            return None
        return results[0][0]