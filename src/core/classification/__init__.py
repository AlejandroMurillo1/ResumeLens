"""Stage 3: finite-automaton classification of candidates against profiles.

``ClassificationResult`` lives in ``src.core.models.models`` and is
re-exported here.
"""

from src.core.models.models import ClassificationResult

from .automaton import Automaton, build_dfa
from .profile_classifier import ProfileClassifier

__all__ = ["Automaton", "ProfileClassifier", "ClassificationResult", "build_dfa"]
