"""Unit tests for the profiles package."""

import pytest

from src.core.models.models import GroupRule, Profile, SkillGroup
from src.core.profiles import ProfileRegistry
from src.core.profiles.definitions import (
    CLOUD_ENGINEER, DATA_ANALYST, FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER,
)

ALL_NAMES = [FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER, CLOUD_ENGINEER, DATA_ANALYST]

RELATIONAL_DB = ("SQL", "POSTGRESQL", "ORACLE", "MYSQL")
NON_RELATIONAL_DB = ("NOSQL", "MONGODB", "REDIS", "CASSANDRA")


@pytest.fixture
def registry() -> ProfileRegistry:
    return ProfileRegistry()


def _group(profile: Profile, label: str) -> SkillGroup:
    return next(g for g in profile.groups if g.label == label)


def _labels(profile: Profile) -> list[str]:
    return [g.label for g in profile.groups]


def _required(profile: Profile) -> set[str]:
    return {t for g in profile.groups if g.rule is GroupRule.REQUIRED for t in g.tokens}


class TestRegistry:
    def test_loads_four_profiles_in_order(self, registry):
        assert [p.name for p in registry.get_all()] == ALL_NAMES

    def test_get_all_returns_profiles_and_a_fresh_list(self, registry):
        profiles = registry.get_all()
        assert all(isinstance(p, Profile) for p in profiles)
        profiles.clear()
        assert len(registry.get_all()) == 4

    @pytest.mark.parametrize("name", ALL_NAMES)
    def test_get_by_name(self, registry, name):
        assert registry.get_by_name(name).name == name

    def test_get_by_name_is_case_and_space_insensitive(self, registry):
        assert registry.get_by_name("  cloud ENGINEER ").name == CLOUD_ENGINEER

    def test_unknown_name_raises_key_error(self, registry):
        with pytest.raises(KeyError, match="Unknown profile"):
            registry.get_by_name("Astronaut")

    def test_load_profiles_is_idempotent(self, registry):
        registry.load_profiles()
        registry.load_profiles()
        assert len(registry.get_all()) == 4


class TestProfileDefinitions:
    def test_every_profile_has_groups_with_tokens(self, registry):
        for profile in registry.get_all():
            assert profile.groups
            for group in profile.groups:
                assert group.tokens and isinstance(group.rule, GroupRule)

    def test_tokens_are_uppercase_identifiers(self, registry):
        for profile in registry.get_all():
            for token in profile.vocabulary:
                assert token == token.upper() and " " not in token

    def test_group_labels_are_unique_inside_a_profile(self, registry):
        for profile in registry.get_all():
            assert len(_labels(profile)) == len(set(_labels(profile))), profile.name

    def test_no_token_repeated_inside_a_profile(self, registry):
        """The classifier requires each token to belong to a single group."""
        for profile in registry.get_all():
            vocab = profile.vocabulary
            assert len(vocab) == len(set(vocab)), profile.name

    def test_no_token_repeated_inside_a_group(self, registry):
        for profile in registry.get_all():
            for group in profile.groups:
                assert len(group.tokens) == len(set(group.tokens)), (profile.name, group.label)

    def test_relational_group_is_identical_wherever_it_appears(self, registry):
        for name in (FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER, DATA_ANALYST):
            group = _group(registry.get_by_name(name), "Relational database")
            assert group.rule is GroupRule.ANY_OF
            assert group.tokens == RELATIONAL_DB

    def test_full_stack(self, registry):
        p = registry.get_by_name(FULL_STACK_DEVELOPER)
        assert _labels(p) == [
            "Language", "Frontend framework", "Backend framework", "REST APIs",
            "Relational database", "Non-relational database", "Version control",
        ]
        assert _group(p, "Language").tokens == ("JAVASCRIPT", "TYPESCRIPT")
        assert _group(p, "Frontend framework").tokens == ("REACT", "ANGULAR", "VUE")
        assert _group(p, "Backend framework").tokens == ("NODE_JS", "DJANGO", "SPRING_BOOT")
        assert _group(p, "Backend framework").rule is GroupRule.ANY_OF
        assert _group(p, "Relational database").tokens == RELATIONAL_DB
        non_rel = _group(p, "Non-relational database")
        assert non_rel.tokens == NON_RELATIONAL_DB
        assert non_rel.rule is GroupRule.ANY_OF
        assert _required(p) == {"REST_API", "GIT"}

    def test_machine_learning(self, registry):
        p = registry.get_by_name(MACHINE_LEARNING_ENGINEER)
        assert _labels(p) == [
            "Language", "Data processing", "Classical ML", "Deep learning",
            "Model development", "Relational database", "Version control",
        ]
        assert _group(p, "Language").tokens == ("PYTHON",)
        assert _group(p, "Data processing").tokens == ("PANDAS", "NUMPY")
        assert _group(p, "Deep learning").rule is GroupRule.ANY_OF
        assert _required(p) == {"PYTHON", "SCIKIT_LEARN", "MACHINE_LEARNING", "GIT"}
        assert "SQL" not in _required(p)  # SQL is satisfiable by any relational DB

    def test_cloud(self, registry):
        p = registry.get_by_name(CLOUD_ENGINEER)
        assert _group(p, "Cloud provider").tokens == ("AWS", "AZURE", "GCP")
        assert _group(p, "CI/CD").tokens == ("JENKINS", "GITHUB_ACTIONS", "GITLAB")
        assert _required(p) == {"LINUX", "GIT"}

    def test_data_analyst(self, registry):
        p = registry.get_by_name(DATA_ANALYST)
        assert _labels(p) == [
            "Relational database", "Analysis tool", "Visualization", "Analysis library",
        ]
        assert _group(p, "Analysis tool").tokens == ("EXCEL", "PYTHON", "R")
        assert _group(p, "Visualization").tokens == ("POWER_BI", "TABLEAU", "LOOKER")
        assert _group(p, "Analysis library").tokens == ("PANDAS", "STATISTICS")

    def test_data_analyst_has_only_any_of_groups(self, registry):
        p = registry.get_by_name(DATA_ANALYST)
        assert all(g.rule is GroupRule.ANY_OF for g in p.groups)
        assert _required(p) == set()
        assert p.vocabulary.count("SQL") == 1  # any relational database covers SQL

    def test_vocabulary_is_flattened_in_group_order(self, registry):
        p = registry.get_by_name(CLOUD_ENGINEER)
        assert p.vocabulary[:3] == ("AWS", "AZURE", "GCP")
        assert p.vocabulary[-1] == "GIT"

    def test_full_stack_vocabulary_includes_both_database_kinds(self, registry):
        vocab = registry.get_by_name(FULL_STACK_DEVELOPER).vocabulary
        assert vocab.index("MYSQL") < vocab.index("NOSQL")  # relational before non-relational
        assert {"MONGODB", "REDIS", "CASSANDRA", "POSTGRESQL"} <= set(vocab)

    def test_profiles_are_immutable(self, registry):
        with pytest.raises(Exception):
            registry.get_by_name(CLOUD_ENGINEER).name = "x"  # type: ignore[misc]
