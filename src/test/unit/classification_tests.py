"""Unit tests for the Stage 3 automata and ProfileClassifier."""

import itertools
import random

import pytest

from src.core.classification import Automaton, ClassificationResult, ProfileClassifier
from src.core.extraction import ContentExtractor
from src.core.models.models import GroupRule, Profile, SkillGroup
from src.core.normalization import build_default_normalizer
from src.core.profiles import ProfileRegistry
from src.core.profiles.definitions import (
    CLOUD_ENGINEER, DATA_ANALYST, FULL_STACK_DEVELOPER, MACHINE_LEARNING_ENGINEER,
)
from src.core.projection import ProfileProjector

REQ, ANY, OPT = GroupRule.REQUIRED, GroupRule.ANY_OF, GroupRule.OPTIONAL


def _profile(*groups: tuple[GroupRule, tuple[str, ...]]) -> Profile:
    return Profile("T", tuple(SkillGroup(f"g{i}", rule, tokens) for i, (rule, tokens) in enumerate(groups)))


def _accepts(profile: Profile, word: list[str]) -> bool:
    return Automaton(profile).accepts(word)


@pytest.fixture
def classifier() -> ProfileClassifier:
    return ProfileClassifier()


@pytest.fixture
def registry() -> ProfileRegistry:
    return ProfileRegistry()


@pytest.fixture
def projector() -> ProfileProjector:
    return ProfileProjector()


# --------------------------------------------------------- group semantics

class TestGroupSemantics:
    def test_required_single_token(self):
        p = _profile((REQ, ("A",)))
        assert _accepts(p, ["A"])
        assert not _accepts(p, [])

    def test_required_group_needs_every_token(self):
        p = _profile((REQ, ("A", "B")))
        assert _accepts(p, ["A", "B"])
        assert not _accepts(p, ["A"])
        assert not _accepts(p, ["B"])

    def test_any_of_needs_at_least_one_token(self):
        p = _profile((ANY, ("A", "B", "C")))
        assert _accepts(p, ["B"])
        assert _accepts(p, ["A", "C"])
        assert _accepts(p, ["A", "B", "C"])
        assert not _accepts(p, [])

    def test_optional_group_never_blocks(self):
        p = _profile((OPT, ("A", "B")))
        assert _accepts(p, [])
        assert _accepts(p, ["B"])
        assert _accepts(p, ["A", "B"])

    def test_required_followed_by_optional(self):
        p = _profile((REQ, ("A",)), (OPT, ("B",)))
        assert _accepts(p, ["A"])
        assert _accepts(p, ["A", "B"])
        assert not _accepts(p, ["B"])

    def test_optional_group_in_the_middle_can_be_skipped(self):
        p = _profile((REQ, ("A",)), (OPT, ("B",)), (REQ, ("C",)))
        assert _accepts(p, ["A", "C"])
        assert _accepts(p, ["A", "B", "C"])
        assert not _accepts(p, ["A", "B"])

    def test_leading_optional_group_can_be_skipped(self):
        p = _profile((OPT, ("A",)), (REQ, ("B",)))
        assert _accepts(p, ["B"])
        assert _accepts(p, ["A", "B"])
        assert not _accepts(p, ["A"])

    def test_every_group_must_be_satisfied(self):
        p = _profile((ANY, ("A", "B")), (ANY, ("C", "D")))
        assert _accepts(p, ["A", "D"])
        assert not _accepts(p, ["A", "B"])
        assert not _accepts(p, ["C", "D"])

    def test_profile_without_groups_accepts_only_the_empty_word(self):
        p = Profile("empty", ())
        assert _accepts(p, [])
        assert not _accepts(p, ["A"])


class TestCanonicalWordsOnly:
    def test_order_must_follow_the_groups(self):
        p = _profile((ANY, ("A", "B")), (REQ, ("C",)))
        assert _accepts(p, ["A", "C"])
        assert not _accepts(p, ["C", "A"])

    def test_order_inside_a_group_must_follow_the_profile(self):
        p = _profile((ANY, ("A", "B")))
        assert _accepts(p, ["A", "B"])
        assert not _accepts(p, ["B", "A"])

    def test_repeated_token_is_rejected(self):
        p = _profile((ANY, ("A", "B")))
        assert not _accepts(p, ["A", "A"])

    def test_token_outside_the_alphabet_is_rejected(self):
        p = _profile((REQ, ("A",)))
        assert not _accepts(p, ["A", "ZZZ"])
        assert not _accepts(p, ["a"])


class TestInvalidProfiles:
    def test_token_in_two_groups_is_rejected(self):
        with pytest.raises(ValueError, match="more than one group"):
            Automaton(_profile((REQ, ("A",)), (ANY, ("A", "B"))))

    def test_group_without_tokens_is_rejected(self):
        with pytest.raises(ValueError, match="no tokens"):
            Automaton(_profile((ANY, ())))


# ------------------------------------------------------- the four profiles

OK_CANDIDATES = {
    FULL_STACK_DEVELOPER: ["JAVASCRIPT", "REACT", "NODE_JS", "REST_API", "POSTGRESQL", "MONGODB", "GIT"],
    MACHINE_LEARNING_ENGINEER: ["PYTHON", "PANDAS", "SCIKIT_LEARN", "TENSORFLOW", "MACHINE_LEARNING", "SQL", "GIT"],
    CLOUD_ENGINEER: ["AWS", "DOCKER", "TERRAFORM", "JENKINS", "LINUX", "GIT"],
    DATA_ANALYST: ["SQL", "EXCEL", "TABLEAU", "PANDAS"],
}


def _satisfies(present: set[str], profile: Profile) -> bool:
    """Independent oracle: the rules read directly on a set of tokens."""
    for group in profile.groups:
        hits = [token in present for token in group.tokens]
        if group.rule is GroupRule.REQUIRED and not all(hits):
            return False
        if group.rule is GroupRule.ANY_OF and not any(hits):
            return False
    return True


class TestDefaultProfiles:
    @pytest.mark.parametrize("profile_name", list(OK_CANDIDATES))
    def test_complete_candidate_is_accepted(self, classifier, registry, projector, profile_name):
        profile = registry.get_by_name(profile_name)
        word = projector.project(OK_CANDIDATES[profile_name], profile)
        assert classifier.accepts(word, profile)

    @pytest.mark.parametrize("profile_name", list(OK_CANDIDATES))
    def test_removing_any_non_optional_group_rejects_the_candidate(
        self, classifier, registry, projector, profile_name
    ):
        profile = registry.get_by_name(profile_name)
        for group in profile.groups:
            if group.rule is GroupRule.OPTIONAL:
                continue
            tokens = [t for t in OK_CANDIDATES[profile_name] if t not in group.tokens]
            word = projector.project(tokens, profile)
            assert not classifier.accepts(word, profile), (profile_name, group.label)

    def test_empty_candidate_is_rejected_everywhere(self, classifier, registry):
        assert not any(classifier.accepts([], p) for p in registry.get_all())

    def test_data_analyst_does_not_need_the_sql_token(self, classifier, registry, projector):
        da = registry.get_by_name(DATA_ANALYST)
        word = projector.project(["POSTGRESQL", "EXCEL", "LOOKER", "STATISTICS"], da)
        assert classifier.accepts(word, da)

    def test_data_analyst_needs_a_relational_database(self, classifier, registry, projector):
        da = registry.get_by_name(DATA_ANALYST)
        word = projector.project(["EXCEL", "LOOKER", "PANDAS"], da)
        assert not classifier.accepts(word, da)

    def test_full_stack_needs_both_kinds_of_database(self, classifier, registry, projector):
        fs = registry.get_by_name(FULL_STACK_DEVELOPER)
        only_relational = [t for t in OK_CANDIDATES[FULL_STACK_DEVELOPER] if t != "MONGODB"]
        assert not classifier.accepts(projector.project(only_relational, fs), fs)

    @pytest.mark.parametrize("profile_name", list(OK_CANDIDATES))
    def test_automaton_agrees_with_the_rules_on_many_candidates(
        self, classifier, registry, projector, profile_name
    ):
        """The DFA must accept exactly the projected sets that satisfy the rules."""
        profile = registry.get_by_name(profile_name)
        vocab = list(profile.vocabulary)
        if len(vocab) <= 13:
            subsets = (c for r in range(len(vocab) + 1) for c in itertools.combinations(vocab, r))
        else:
            rng = random.Random(0)
            subsets = (rng.sample(vocab, rng.randint(0, len(vocab))) for _ in range(3000))
        for subset in subsets:
            word = projector.project(subset, profile)
            assert classifier.accepts(word, profile) == _satisfies(set(subset), profile), subset

    @pytest.mark.parametrize("profile_name", list(OK_CANDIDATES))
    def test_state_count_is_one_plus_the_vocabulary(self, classifier, registry, profile_name):
        profile = registry.get_by_name(profile_name)
        assert classifier.get_automaton(profile).num_states == 1 + len(profile.vocabulary)


# --------------------------------------------------------- ProfileClassifier

class TestProfileClassifier:
    def test_get_automaton_is_cached_per_profile(self, classifier, registry):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        assert classifier.get_automaton(cloud) is classifier.get_automaton(cloud)
        assert classifier.get_automaton(cloud) is not classifier.get_automaton(
            registry.get_by_name(DATA_ANALYST)
        )

    def test_automaton_exposes_name_and_alphabet(self, classifier, registry):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        automaton = classifier.get_automaton(cloud)
        assert automaton.profile_name == CLOUD_ENGINEER
        assert automaton.alphabet == frozenset(cloud.vocabulary)

    def test_classify_returns_the_evaluated_sequence(self, classifier, registry, projector):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        word = projector.project(OK_CANDIDATES[CLOUD_ENGINEER], cloud)
        result = classifier.classify(word, cloud)
        assert result == ClassificationResult(CLOUD_ENGINEER, True, word)

    def test_classify_rejected_keeps_the_sequence(self, classifier, registry):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        result = classifier.classify(["GIT"], cloud)
        assert result == ClassificationResult(CLOUD_ENGINEER, False, ("GIT",))

    def test_classify_stores_the_sequence_as_a_tuple(self, classifier, registry):
        result = classifier.classify(["GIT"], registry.get_by_name(CLOUD_ENGINEER))
        assert isinstance(result.sequence, tuple)

    def test_accepts_takes_any_iterable(self, classifier, registry):
        cloud = registry.get_by_name(CLOUD_ENGINEER)
        word = ("AWS", "DOCKER", "TERRAFORM", "JENKINS", "LINUX", "GIT")
        assert classifier.accepts(word, cloud)
        assert classifier.accepts(iter(word), cloud)


# ------------------------------------------- Stages 1 -> 2 -> projection -> 3

class TestFullPipeline:
    CV_SKILLS = "Skills\nJS, React.js, Node.js, REST APIs, PostgreSQL, MongoDB, Git\n"

    def test_one_cv_against_the_four_profiles(self, classifier, registry, projector):
        raw = ContentExtractor().extract_skills(self.CV_SKILLS)
        tokens = build_default_normalizer().normalize_skills(raw).recognized
        verdicts = {
            profile.name: classifier.classify(projector.project(tokens, profile), profile).accepted
            for profile in registry.get_all()
        }
        assert verdicts == {
            FULL_STACK_DEVELOPER: True,
            MACHINE_LEARNING_ENGINEER: False,
            CLOUD_ENGINEER: False,
            DATA_ANALYST: False,
        }
