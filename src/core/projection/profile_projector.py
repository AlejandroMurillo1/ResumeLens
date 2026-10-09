"""Projection: from a candidate's canonical tokens to the word a profile evaluates.

Stage 2 produces the *set* of canonical tokens a candidate has, in the order
the candidate happened to write them. The classifier of Stage 3 reads a *word*
over the profile's alphabet, so each profile needs its own view of the
candidate:

1. **filter**: keep only the tokens that belong to the profile's vocabulary;
2. **deduplicate**: keep each token once;
3. **sort canonically**: order them by their position in the profile
   (group order first, then token order inside the group).

The result does not depend on the order of the input, which is the property
the canonical ordering exists to guarantee.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.core.models.models import Profile


class ProfileProjector:
    """Projects canonical tokens onto the vocabulary and order of a profile."""

    def __init__(self) -> None:
        """Create a projector. It is stateless; instances are reusable."""

    def project(self, tokens: Iterable[str], profile: Profile) -> tuple[str, ...]:
        """Return the tokens of *profile* found in *tokens*, in canonical order.

        Tokens must already be canonical (``NODE_JS``, not ``node.js``); a token
        that is not in the profile's vocabulary, including a mis-cased one, is
        dropped. A token that a profile lists in more than one group (for
        example ``SQL`` in *Data Analyst*) is placed at its **first** position
        and appears once.
        """
        rank: dict[str, int] = {}
        for position, token in enumerate(profile.vocabulary):
            rank.setdefault(token, position)
        present = {token for token in tokens if token in rank}
        return tuple(sorted(present, key=rank.__getitem__))
