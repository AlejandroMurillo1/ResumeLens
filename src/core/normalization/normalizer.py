from collections.abc import Iterable
from dataclasses import dataclass

from pyformlang.fst import FST

from src.core.normalization.transducers import CaseFoldingTransducer, Transducer

@dataclass(frozen=True)
class NormalizedSkills:
    """Outcome of normalising a list of raw skills."""

    recognized: tuple[str, ...]    # canonical tokens, deduplicated, first-seen order
    unrecognized: tuple[str, ...]  # raw skills with no canonical form, deduplicated

class SkillNormalizer:
    def __init__(
        self,
        case_folder: CaseFoldingTransducer,
        vocabulary: FST,
        stripper: Transducer | None = None,
    ) -> None:
        self._case_folder = case_folder
        self._vocabulary = vocabulary
        self._stripper = stripper

    def normalize(self, raw: str) -> str | None:
        cleaned = raw.strip()
        if self._stripper is not None:
            cleaned = self._stripper.apply(cleaned)
        cleaned = self._case_folder.apply(cleaned)
        if not cleaned:
            return None
        results = list(self._vocabulary.translate([cleaned]))
        if not results:
            return None
        return results[0][0]

    def normalize_skills(self, raws: Iterable[str]) -> NormalizedSkills:
        """Normalise every raw skill, never raising on unknown input.

        Text outside the transducers' alphabet (``C++``, ``Ñandú``) counts as
        unrecognised instead of propagating ``ValueError``.
        """
        recognized: list[str] = []
        unrecognized: list[str] = []
        seen_unrecognized: set[str] = set()
        for raw in raws:
            try:
                token = self.normalize(raw)
            except ValueError:
                token = None
            if token is not None:
                if token not in recognized:
                    recognized.append(token)
                continue
            text = raw.strip()
            if text and text.casefold() not in seen_unrecognized:
                seen_unrecognized.add(text.casefold())
                unrecognized.append(text)
        return NormalizedSkills(tuple(recognized), tuple(unrecognized))
