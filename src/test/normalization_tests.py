import pytest
from src.core.normalization import CaseFoldingTransducer, build_vocabulary_fst, SkillNormalizer

VOCABULARY = {
    "GIT": ["GIT"],
    "DOCKER": ["DOCKER"],
    "TERRAFORM": ["TERRAFORM"],
    "JAVASCRIPT": ["JAVASCRIPT", "JS"],
    "TYPESCRIPT": ["TYPESCRIPT", "TS"],
    "KUBERNETES": ["KUBERNETES", "K8S"],
    "REACT": ["REACT", "REACTJS", "REACTTS"],
    "ANGULAR": ["ANGULAR"],
    "SPRINGBOOT": ["SPRINGBOOT"],
}


@pytest.fixture(scope="module")
def normalizer():
    return SkillNormalizer(CaseFoldingTransducer(), build_vocabulary_fst(VOCABULARY))


class TestSkillNormalizer:
    def test_lowercase(self, normalizer):
        assert normalizer.normalize("git") == "GIT"

    def test_uppercase(self, normalizer):
        assert normalizer.normalize("DOCKER") == "DOCKER"

    def test_mixed_case(self, normalizer):
        assert normalizer.normalize("TerraForm") == "TERRAFORM"

    @pytest.mark.parametrize(
        "raw, expected",
        [("JS", "JAVASCRIPT"), ("TS", "TYPESCRIPT"), ("K8S", "KUBERNETES")],
    )
    def test_abbreviation(self, normalizer, raw, expected):
        assert normalizer.normalize(raw) == expected

    def test_suffix_variant(self, normalizer):
        assert normalizer.normalize("ReactJS") == "REACT"

    def test_surrounding_whitespace_is_trimmed(self, normalizer):
        assert normalizer.normalize("  git  ") == "GIT"

    @pytest.mark.parametrize("raw", ["reactt", "anguler"])
    def test_near_miss_spelling_is_unrecognized(self, normalizer, raw):
        assert normalizer.normalize(raw) is None

    def test_internal_space_is_rejected_by_design(self, normalizer):
        assert normalizer.normalize("spring boot") is None

    def test_internal_dot_raises_value_error(self, normalizer):
        with pytest.raises(ValueError):
            normalizer.normalize("node.js")

    @pytest.mark.parametrize("raw", ["c#", "node+"])
    def test_character_outside_alphabet_raises_value_error(self, normalizer, raw):
        with pytest.raises(ValueError):
            normalizer.normalize(raw)

    def test_empty_string_is_unrecognized(self, normalizer):
        assert normalizer.normalize("") is None