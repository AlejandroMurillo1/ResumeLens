from src.core.normalization.normalizer import NormalizedSkills, SkillNormalizer
from src.core.normalization.transducers import (
    CaseFoldingTransducer,
    StrippingTransducer,
    Transducer,
    build_vocabulary_fst,
)
from src.core.normalization.vocabulary import VOCABULARY


def build_default_normalizer() -> SkillNormalizer:
    """Normalizer wired with the full vocabulary: strip -> case fold -> lookup."""
    return SkillNormalizer(
        CaseFoldingTransducer(),
        build_vocabulary_fst(VOCABULARY),
        StrippingTransducer(),
    )


case_folder = CaseFoldingTransducer()
stripper = StrippingTransducer()
vocabulary_fst = build_vocabulary_fst(VOCABULARY)
normalizer = SkillNormalizer(case_folder, vocabulary_fst, stripper)

__all__ = [
    "VOCABULARY",
    "CaseFoldingTransducer",
    "NormalizedSkills",
    "SkillNormalizer",
    "StrippingTransducer",
    "Transducer",
    "build_default_normalizer",
    "build_vocabulary_fst",
    "normalizer",
]
