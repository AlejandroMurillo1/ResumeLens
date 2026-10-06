"""Professional profiles, skill groups and the registry that serves them.

``Profile``, ``SkillGroup`` and ``GroupRule`` live in
``src.core.models.models`` and are re-exported here.
"""

from src.core.models.models import GroupRule, Profile, SkillGroup

from .profile_registry import ProfileRegistry

__all__ = ["ProfileRegistry", "Profile", "SkillGroup", "GroupRule"]
