"""Unit tests for ProfileProjector."""

import itertools

import pytest

from src.core.extraction import ContentExtractor
from src.core.normalization import build_default_normalizer
from src.core.profiles import ProfileRegistry
from src.core.profiles.definitions import (
    CLOUD_ENGINEER, DATA_ANALYST, FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER,
)
from src.core.projection import ProfileProjector


@pytest.fixture
def projector() -> ProfileProjector:
    return ProfileProjector()


@pytest.fixture
def registry() -> ProfileRegistry:
    return ProfileRegistry()


class TestProject:
    def test_tokens_outside_the_vocabulary_are_dropped(self, projector, registry):
        full_stack = registry.get_by_name(FULL_STACK_DEVELOPER)
        assert projector.project(["DOCKER", "GIT"], full_stack) == ("GIT",)

    def test_orders_by_group_then_by_position_inside_the_group(self, projector, registry):
        full_stack = registry.get_by_name(FULL_STACK_DEVELOPER)
        tokens = ["GIT", "REACT", "SQL", "DOCKER", "NODE_JS", "JAVASCRIPT", "REST_API"]
        assert projector.project(tokens, full_stack) == (
            "JAVASCRIPT", "REACT", "NODE_JS", "REST_API", "SQL", "GIT",
        )

    def test_order_inside_one_group_follows_the_profile_not_the_input(self, projector, registry):
        full_stack = registry.get_by_name(FULL_STACK_DEVELOPER)
        assert projector.project(["VUE", "ANGULAR", "REACT"], full_stack) == (
            "REACT", "ANGULAR", "VUE",
        )

    def test_duplicates_are_removed(self, projector, registry):
        full_stack = registry.get_by_name(FULL_STACK_DEVELOPER)
        assert projector.project(["GIT", "GIT", "SQL", "GIT"], full_stack) == ("SQL", "GIT")

    def test_empty_input(self, projector, registry):
        assert projector.project([], registry.get_by_name(CLOUD_ENGINEER)) == ()

    def test_no_token_in_common_gives_empty_word(self, projector, registry):
        ml = registry.get_by_name(MACHINE_LEARNING_ENGINEER)
        assert projector.project(["LOOKER", "TABLEAU"], ml) == ()

    def test_returns_a_tuple(self, projector, registry):
        assert isinstance(projector.project(["GIT"], registry.get_by_name(CLOUD_ENGINEER)), tuple)

    def test_accepts_any_iterable(self, projector, registry):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        expected = ("DOCKER", "GIT")
        assert projector.project(("GIT", "DOCKER"), cloud) == expected
        assert projector.project({"GIT", "DOCKER"}, cloud) == expected
        assert projector.project((t for t in ("GIT", "DOCKER")), cloud) == expected

    def test_tokens_must_be_canonical(self, projector, registry):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        assert projector.project(["git", "Git", "docker"], cloud) == ()

    def test_input_is_not_modified(self, projector, registry):
        tokens = ["GIT", "DOCKER", "GIT"]
        projector.project(tokens, registry.get_by_name(CLOUD_ENGINEER))
        assert tokens == ["GIT", "DOCKER", "GIT"]


class TestPerProfile:
    CANDIDATE = ["PYTHON", "SQL", "GIT", "PANDAS", "EXCEL", "DOCKER", "LINUX"]

    @pytest.mark.parametrize("profile_name, expected", [
        (FULL_STACK_DEVELOPER, ("SQL", "GIT")),
        (MACHINE_LEARNING_ENGINEER, ("PYTHON", "PANDAS", "SQL", "GIT")),
        (CLOUD_ENGINEER, ("DOCKER", "LINUX", "GIT")),
        (DATA_ANALYST, ("SQL", "EXCEL", "PYTHON", "PANDAS")),
    ])
    def test_same_candidate_gives_a_different_word_per_profile(
        self, projector, registry, profile_name, expected
    ):
        assert projector.project(self.CANDIDATE, registry.get_by_name(profile_name)) == expected

    def test_token_listed_in_two_groups_appears_once_at_its_first_position(self, projector, registry):
        data_analyst = registry.get_by_name(DATA_ANALYST)
        assert data_analyst.vocabulary.count("SQL") == 2  # documents the premise
        assert projector.project(["POSTGRESQL", "SQL"], data_analyst) == ("SQL", "POSTGRESQL")

    def test_full_vocabulary_in_reverse_gives_the_profile_order_without_repeats(self, projector, registry):
        for profile in registry.get_all():
            reversed_vocab = list(reversed(profile.vocabulary))
            assert projector.project(reversed_vocab, profile) == tuple(dict.fromkeys(profile.vocabulary))


class TestOrderIndependence:
    def test_every_permutation_gives_the_same_word(self, projector, registry):
        full_stack = registry.get_by_name(FULL_STACK_DEVELOPER)
        tokens = ["GIT", "REACT", "NODE_JS", "SQL", "JAVASCRIPT"]
        results = {projector.project(p, full_stack) for p in itertools.permutations(tokens)}
        assert results == {("JAVASCRIPT", "REACT", "NODE_JS", "SQL", "GIT")}


class TestPipelineIntegration:
    CV_SKILLS = "Skills\nGit, React.js, Node.js, PostgreSQL, Docker, JS, REST APIs\n"

    def _canonical_tokens(self):
        raw = ContentExtractor().extract_skills(self.CV_SKILLS)
        return build_default_normalizer().normalize_skills(raw).recognized

    def test_extraction_normalization_projection(self, projector, registry):
        tokens = self._canonical_tokens()
        assert projector.project(tokens, registry.get_by_name(FULL_STACK_DEVELOPER)) == (
            "JAVASCRIPT", "REACT", "NODE_JS", "REST_API", "POSTGRESQL", "GIT",
        )
        assert projector.project(tokens, registry.get_by_name(CLOUD_ENGINEER)) == ("DOCKER", "GIT")
