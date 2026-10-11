"""Registry of the professional profiles known to ResumeLens."""

from __future__ import annotations

from src.core.models.models import Profile

from .definitions import build_default_profiles


class ProfileRegistry:
    """Stores the supported profiles and looks them up by name."""

    def __init__(self) -> None:
        """Create the registry and load the default profiles."""
        self._profiles: dict[str, Profile] = {}
        self.load_profiles()

    def load_profiles(self) -> None:
        """(Re)load the four default profiles, replacing current contents."""
        self._profiles = {
            profile.name.casefold(): profile for profile in build_default_profiles()
        }

    def get_by_name(self, name: str) -> Profile:
        """Return the profile called *name* (case-insensitive).

        Raises:
            KeyError: if no profile has that name.
        """
        try:
            return self._profiles[name.strip().casefold()]
        except KeyError:
            available = ", ".join(p.name for p in self._profiles.values())
            raise KeyError(f"Unknown profile {name!r}. Available: {available}") from None

    def get_all(self) -> list[Profile]:
        """Return every registered profile, in registration order."""
        return list(self._profiles.values())
