"""Stage 3 building blocks: the finite automaton of a profile.

A profile is a sequence of skill groups. After projection, a candidate is a
word over the profile's tokens, already in canonical order (group order, then
token order inside the group). The automaton built here accepts exactly the
canonical words that satisfy every group:

* ``REQUIRED`` group: all of its tokens appear;
* ``ANY_OF`` group:   at least one of its tokens appears;
* ``OPTIONAL`` group: no condition.

Formal definition (a partial DFA, ``M = (Q, Sigma, delta, q0, F)``). Number the
groups ``g = 0..n-1`` and the tokens of group ``g`` as ``(g, 1)..(g, k_g)``.

* ``Q = {q(0,0)} U {q(g,p) : 0 <= g < n, 1 <= p <= k_g}``; ``q(g,p)`` means
  "the last token read is token ``p`` of group ``g``"; ``q0 = q(0,0)``.
* ``Sigma`` is the vocabulary of the profile.
* ``sat(g,p)`` holds when group ``g`` is satisfied after reading up to its
  token ``p``: ``p == k_g`` for REQUIRED, ``p >= 1`` for ANY_OF, always for
  OPTIONAL.
* ``F = {q(g,p) : sat(g,p) and every group after g is OPTIONAL}``.
* ``delta(q(g,p), t)``, with ``t`` being token ``q`` of group ``h``:
  - ``q(g,q)`` if ``h == g`` and ``q > p`` (and ``q == p + 1`` if the group is
    REQUIRED, since a skipped token could never be read later);
  - ``q(h,q)`` if ``h > g``, ``sat(g,p)``, every group strictly between ``g``
    and ``h`` is OPTIONAL, and ``q == 1`` when ``h`` is REQUIRED;
  - undefined otherwise (the missing transitions stand for an implicit dead
    state).
"""

from __future__ import annotations

from collections.abc import Iterable

from pyformlang.finite_automaton import DeterministicFiniteAutomaton

from src.core.models.models import GroupRule, Profile


def _state(group: int, position: int) -> str:
    return f"q{group}_{position}"


def build_dfa(profile: Profile) -> DeterministicFiniteAutomaton:
    """Build the DFA of *profile* (construction described in the module docstring).

    Raises:
        ValueError: if a group has no tokens or a token appears in two groups.
    """
    groups = profile.groups
    owner: dict[str, tuple[int, int]] = {}
    for g, group in enumerate(groups):
        if not group.tokens:
            raise ValueError(f"Group {group.label!r} of {profile.name!r} has no tokens")
        for p, token in enumerate(group.tokens, start=1):
            if token in owner:
                raise ValueError(
                    f"Token {token!r} is listed in more than one group of {profile.name!r}"
                )
            owner[token] = (g, p)

    rules = [group.rule for group in groups]
    sizes = [len(group.tokens) for group in groups]
    n = len(groups)

    def sat(g: int, p: int) -> bool:
        if rules[g] is GroupRule.REQUIRED:
            return p == sizes[g]
        if rules[g] is GroupRule.ANY_OF:
            return p >= 1
        return True

    def only_optional(first: int, last: int) -> bool:
        """True if every group in ``range(first, last)`` is OPTIONAL."""
        return all(rules[m] is GroupRule.OPTIONAL for m in range(first, last))

    dfa = DeterministicFiniteAutomaton()
    dfa.add_start_state(_state(0, 0))
    if n == 0:
        dfa.add_final_state(_state(0, 0))
        return dfa

    states = [(0, 0)] + [(g, p) for g in range(n) for p in range(1, sizes[g] + 1)]
    for g, p in states:
        if sat(g, p) and only_optional(g + 1, n):
            dfa.add_final_state(_state(g, p))
        for token, (h, q) in owner.items():
            if h == g and q > p and (rules[g] is not GroupRule.REQUIRED or q == p + 1):
                dfa.add_transition(_state(g, p), token, _state(h, q))
            elif (
                h > g
                and sat(g, p)
                and only_optional(g + 1, h)
                and (rules[h] is not GroupRule.REQUIRED or q == 1)
            ):
                dfa.add_transition(_state(g, p), token, _state(h, q))
    return dfa


class Automaton:
    """The recognizer of one profile, wrapping a ``pyformlang`` DFA."""

    def __init__(self, profile: Profile) -> None:
        """Build the automaton of *profile* (see :func:`build_dfa`)."""
        self._profile_name = profile.name
        self._alphabet = frozenset(profile.vocabulary)
        self._dfa = build_dfa(profile)

    @property
    def profile_name(self) -> str:
        """Name of the profile this automaton recognizes."""
        return self._profile_name

    @property
    def alphabet(self) -> frozenset[str]:
        """The tokens the automaton can read."""
        return self._alphabet

    @property
    def num_states(self) -> int:
        """Number of states of the DFA (the implicit dead state is not counted)."""
        return len(self._dfa.states)

    def accepts(self, sequence: Iterable[str]) -> bool:
        """Return whether *sequence* is accepted.

        The sequence must be a projected word: only profile tokens, without
        repeats, in canonical order. Anything else is rejected, including a
        valid set of tokens written in a different order.
        """
        word = list(sequence)
        if any(token not in self._alphabet for token in word):
            return False
        return bool(self._dfa.accepts(word))
