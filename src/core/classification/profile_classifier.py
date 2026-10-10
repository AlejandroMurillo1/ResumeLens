"""Stage 3: decide whether a projected candidate satisfies a profile."""

from __future__ import annotations

from collections.abc import Iterable

from src.core.models.models import ClassificationResult, Profile

from .automaton import Automaton


class ProfileClassifier:
    """Classifies projected token sequences against profiles.

    Automata are built once per profile and reused.
    """

    def __init__(self) -> None:
        """Create a classifier with an empty automaton cache."""
        self._automata: dict[Profile, Automaton] = {}

    def get_automaton(self, profile: Profile) -> Automaton:
        """Return the automaton of *profile*, building it on first use."""
        automaton = self._automata.get(profile)
        if automaton is None:
            automaton = Automaton(profile)
            self._automata[profile] = automaton
        return automaton

    def accepts(self, skills: Iterable[str], profile: Profile) -> bool:
        """Return whether the projected word *skills* satisfies *profile*."""
        return self.get_automaton(profile).accepts(skills)

    def classify(self, sequence: Iterable[str], profile: Profile) -> ClassificationResult:
        """Classify a projected word and keep the sequence that was evaluated."""
        word = tuple(sequence)
        return ClassificationResult(
            profile_name=profile.name,
            accepted=self.accepts(word, profile),
            sequence=word,
        )
