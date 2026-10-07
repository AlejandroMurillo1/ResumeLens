from src.core.normalization.normalizer import SkillNormalizer
from src.core.normalization.transducers import CaseFoldingTransducer, build_vocabulary_fst

VOCABULARY = {
    "GIT": ["GIT"],
    "JAVASCRIPT": ["JAVASCRIPT", "JS"],
    "AWS": ["AWS", "AMAZON WEB SERVICES"],
}

case_folder = CaseFoldingTransducer()
vocabulary_fst = build_vocabulary_fst(VOCABULARY)
normalizer = SkillNormalizer(case_folder, vocabulary_fst)

assert normalizer.normalize("javascript") == "JAVASCRIPT"
assert normalizer.normalize("JS") == "JAVASCRIPT"
assert normalizer.normalize("aws") == "AWS"
assert normalizer.normalize("Amazon Web Services") == "AWS"

assert normalizer.normalize("git") == "GIT"
assert normalizer.normalize("GIT") == "GIT"
assert normalizer.normalize("GitHub") is None