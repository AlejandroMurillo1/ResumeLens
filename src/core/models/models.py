from dataclasses import dataclass
from enum import Enum, auto


# --- extraction -------------------------------------------------------

@dataclass(frozen=True)
class ContactInfo:
    name: str
    email: str
    phone: str


@dataclass(frozen=True)
class RawProfile:
    contact: ContactInfo
    education: tuple[str, ...]
    experience: tuple[str, ...]
    certifications: tuple[str, ...]
    raw_skills: tuple[str, ...]


# --- profiles -----------------------------------------------------------

class GroupRule(Enum):
    REQUIRED = auto()
    ANY_OF = auto()
    OPTIONAL = auto()


@dataclass(frozen=True)
class SkillGroup:
    label: str          # human-readable, for docs/reports only
    rule: GroupRule
    tokens: tuple[str, ...]  # fixed order = total order within this group


@dataclass(frozen=True)
class Profile:
    name: str
    groups: tuple[SkillGroup, ...]  # fixed order = category_order

    @property
    def vocabulary(self) -> tuple[str, ...]:
        """All tokens across all groups, flattened, in order. Used by
        ProfileProjector to filter and order a candidate's tokens."""
        return tuple(token for group in self.groups for token in group.tokens)


# --- classification -------------------------------------------------------

@dataclass(frozen=True)
class ClassificationResult:
    profile_name: str
    accepted: bool
    sequence: tuple[str, ...]  # the filtered, ordered sequence that was evaluated


# --- pipeline -----------------------------------------------------------

@dataclass(frozen=True)
class CandidateReport:
    contact: ContactInfo
    education: tuple[str, ...]
    experience: tuple[str, ...]
    certifications: tuple[str, ...]
    skills: tuple[str, ...]  # recognized canonical tokens, deduplicated
    classifications: tuple[ClassificationResult, ...]  # one per profile
    unrecognized_skills: tuple[str, ...]


# --- dsl -----------------------------------------------------------------

class DSLErrorKind(Enum):
    SYNTAX = auto()
    SEMANTIC = auto()


@dataclass(frozen=True)
class DSLError(Exception):
    kind: DSLErrorKind
    message: str
    line: int | None = None
    column: int | None = None