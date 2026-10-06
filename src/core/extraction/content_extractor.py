"""Stage 1 of the ResumeLens pipeline: regex-based information extraction.

The extractor turns the plain text of a résumé into a :class:`RawProfile`.
It works on *surface forms*: skills are returned exactly as the candidate
wrote them (``JS``, ``React.js``, ``sklearn``). Mapping them to canonical
tokens is the job of Stage 2 (finite-state transducers), so the variants
recognised here must stay aligned with the normalisation vocabulary.

Only the standard :mod:`re` module is used.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.core.models.models import ContactInfo, RawProfile

# --------------------------------------------------------------------------
# Section headers
# --------------------------------------------------------------------------

EDUCATION_HEADERS: tuple[str, ...] = (
    "education", "academic background", "academic qualifications",
    "educación", "educacion", "formación académica", "formacion academica",
    "formación", "estudios",
)
EXPERIENCE_HEADERS: tuple[str, ...] = (
    "experience", "work experience", "professional experience",
    "employment history", "work history",
    "experiencia", "experiencia profesional", "experiencia laboral",
)
CERTIFICATION_HEADERS: tuple[str, ...] = (
    "certifications", "certificates", "licenses & certifications",
    "licenses and certifications", "certificaciones", "certificados",
)
SKILL_HEADERS: tuple[str, ...] = (
    "technical skills", "skills", "skills & tools", "core competencies",
    "technologies", "tech stack",
    "habilidades", "habilidades técnicas", "competencias técnicas",
    "competencias", "tecnologías",
)
# Headers that are never extracted but delimit the sections above.
_OTHER_HEADERS: tuple[str, ...] = (
    "summary", "professional summary", "profile", "objective", "projects",
    "languages", "interests", "references", "contact", "awards",
    "publications", "volunteering", "volunteer experience",
    "perfil", "resumen", "proyectos", "idiomas", "intereses", "referencias",
    "contacto", "premios",
)
_KNOWN_HEADERS: frozenset[str] = frozenset(
    EDUCATION_HEADERS + EXPERIENCE_HEADERS + CERTIFICATION_HEADERS
    + SKILL_HEADERS + _OTHER_HEADERS
)


def _header_pattern(headers: frozenset[str]) -> re.Pattern[str]:
    """Regex matching a *header line*.

    Accepts optional Markdown ``#`` / ``**`` decoration, any letter case and an
    optional colon followed by inline content (``Skills: Python, SQL``).
    Group ``h`` is the header text, group ``rest`` the inline content.
    """
    alternatives = "|".join(
        sorted((re.escape(h) for h in headers), key=len, reverse=True)
    )
    return re.compile(
        r"^[ \t]*(?:\#{1,6}[ \t]*)?(?:\*\*|__)?"
        rf"(?P<h>{alternatives})"
        r"(?:\*\*|__)?[ \t]*(?::(?:\*\*|__)?[ \t]*(?P<rest>.*))?$",
        re.IGNORECASE | re.MULTILINE,
    )


_ANY_HEADER_RE = _header_pattern(_KNOWN_HEADERS)

# --------------------------------------------------------------------------
# Contact patterns
# --------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Digits plus common separators; validated afterwards by digit count.
_PHONE_RE = re.compile(r"(?<![\w@])\+?\(?\d[\d \t().-]{7,}\d(?!\w)")
_DATE_RANGE_RE = re.compile(r"(?:\d{4}\s*[-–.]\s*)+\d{4}")
_NAME_LABEL_RE = re.compile(r"^(?:name|nombre)\s*:\s*(?P<n>.+)$", re.IGNORECASE)
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '’.-]+[^\W\d_]+){0,4}$")
_NOT_A_NAME = frozenset(
    {"resume", "résumé", "cv", "curriculum vitae", "curriculum", "currículum vitae"}
)
_MIN_PHONE_DIGITS, _MAX_PHONE_DIGITS = 9, 15

_BULLET_RE = re.compile(r"^\s*(?:[-*•·▪‣●◦○■]|\d+[.)])\s+")

# --------------------------------------------------------------------------
# Skill catalogue
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class _SkillPattern:
    """One recogniser: *name* is documentation only (never returned)."""

    name: str
    regex: re.Pattern[str]
    skills_section_only: bool = False


def _p(name: str, body: str, *, section_only: bool = False) -> _SkillPattern:
    """Build a pattern with token boundaries.

    The look-behind rejects a preceding word char, ``.``, ``+``, ``#`` or ``-``
    (so ``JS`` does not match inside ``Node.js`` and ``SQL`` not inside
    ``PostgreSQL``/``T-SQL``). The look-ahead rejects a following word char,
    ``+`` or ``#`` (so ``Git`` does not match ``GitHub``).
    """
    regex = re.compile(
        rf"(?<![\w.+#-])(?:{body})(?![\w+#])", re.IGNORECASE
    )
    return _SkillPattern(name, regex, section_only)


_SKILL_PATTERNS: tuple[_SkillPattern, ...] = (
    # Languages
    _p("JAVASCRIPT", r"java[\s-]?script|js|ecmascript"),
    _p("TYPESCRIPT", r"type[\s-]?script"),
    _p("PYTHON", r"python(?:[\s-]?3(?:\.\d+)?)?"),
    # Front end
    _p("REACT", r"react(?:[\s.-]?js)?"),
    _p("ANGULAR", r"angular(?:[\s.-]?js)?"),
    _p("VUE", r"vue(?:[\s.-]?js)?"),
    # Back end
    _p("NODE_JS", r"node[\s.-]?js|(?-i:Node)"),
    _p("DJANGO", r"django"),
    _p("SPRING_BOOT", r"spring[\s-]?boot"),
    _p("REST_API", r"rest(?:ful)?[\s-]?apis?|(?-i:REST|RESTful)"),
    # Databases
    _p("SQL", r"sql"),
    _p("NOSQL", r"no[\s-]?sql"),
    _p("POSTGRESQL", r"postgres(?:ql)?|postgre[\s-]?sql"),
    _p("MYSQL", r"my[\s-]?sql"),
    _p("MONGODB", r"mongo(?:[\s-]?db)?"),
    _p("ORACLE", r"oracle(?:[\s-]?db)?"),
    _p("REDIS", r"redis"),
    _p("CASSANDRA", r"cass?andra"),
    # Data / ML
    _p("PANDAS", r"pandas"),
    _p("NUMPY", r"num[\s-]?py"),
    _p("SCIKIT_LEARN", r"scikit[\s-]?learn|sklearn"),
    _p("TENSORFLOW", r"tensor[\s-]?flow"),
    _p("PYTORCH", r"py[\s-]?torch"),
    _p("MACHINE_LEARNING", r"machine[\s-]learning|(?-i:ML)"),
    _p("STATISTICS", r"statistics|statistical[\s-]analysis"),
    # Cloud / DevOps
    _p("AWS", r"aws|amazon[\s-]web[\s-]services"),
    _p("AZURE", r"azure"),
    _p("GCP", r"gcp|google[\s-]cloud(?:[\s-]platform)?"),
    _p("DOCKER", r"docker"),
    _p("KUBERNETES", r"kubernetes|k8s"),
    _p("ANSIBLE", r"ansible"),
    _p("TERRAFORM", r"terraform"),
    _p("CLOUDFORMATION", r"cloud[\s-]?formation"),
    _p("JENKINS", r"jenkins"),
    _p("GITHUB_ACTIONS", r"github[\s-]?actions"),
    _p("GITLAB", r"gitlab(?:[\s-]?ci(?:/cd)?)?"),
    _p("LINUX", r"linux"),
    _p("GIT", r"git"),
    # BI / analysis tools
    _p("EXCEL", r"(?:ms|microsoft)[\s-]excel|(?-i:Excel)"),
    _p("POWER_BI", r"power[\s-]?bi"),
    _p("TABLEAU", r"tableau"),
    _p("LOOKER", r"looker"),
    # Single letter: only trusted inside the skills section.
    _SkillPattern(
        "R",
        re.compile(r"(?<![\w.&+#'-])R(?![\w+#&'-])"),
        skills_section_only=True,
    ),
)


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _dedup_key(value: str) -> str:
    return re.sub(r"[\s._-]", "", value).casefold()


class ContentExtractor:
    """Regex-based extractor producing a :class:`RawProfile` from résumé text."""

    def __init__(self) -> None:
        """Create an extractor. It is stateless; instances are reusable."""

    # ------------------------------------------------------------ sections

    def find_section(self, header: str, text: str) -> str:
        """Return the body of the section titled *header*, or ``""``.

        The match is case-insensitive and tolerant to Markdown decoration and
        a trailing colon. The section ends at the next known header. Content
        written on the header line (``Skills: Python, SQL``) is included.
        """
        text = _normalize_newlines(text)
        target = header.strip().casefold()
        if not target:
            return ""
        pattern = _header_pattern(_KNOWN_HEADERS | {target})
        matches = list(pattern.finditer(text))
        for i, match in enumerate(matches):
            if match.group("h").casefold() != target:
                continue
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = f"{match.group('rest') or ''}\n{text[match.end():end]}"
            return body.strip()
        return ""

    def _first_section(self, headers: tuple[str, ...], text: str) -> str:
        for header in headers:
            section = self.find_section(header, text)
            if section:
                return section
        return ""

    @staticmethod
    def _entries(section: str) -> tuple[str, ...]:
        """One entry per non-empty line, bullets removed."""
        entries: list[str] = []
        for line in section.splitlines():
            line = _BULLET_RE.sub("", line).strip()
            if re.search(r"\w", line):  # skips blank lines and '-----' rules
                entries.append(line)
        return tuple(entries)

    # ------------------------------------------------------------- contact

    def extract_contact(self, text: str) -> ContactInfo:
        """Extract name, e-mail and phone number. Missing fields are ``""``."""
        text = _normalize_newlines(text)
        return ContactInfo(
            name=self._extract_name(text),
            email=self._extract_email(text),
            phone=self._extract_phone(text),
        )

    @staticmethod
    def _extract_email(text: str) -> str:
        match = _EMAIL_RE.search(text)
        return match.group(0) if match else ""

    @staticmethod
    def _extract_phone(text: str) -> str:
        for match in _PHONE_RE.finditer(text):
            candidate = match.group(0).strip()
            digits = re.sub(r"\D", "", candidate)
            if not _MIN_PHONE_DIGITS <= len(digits) <= _MAX_PHONE_DIGITS:
                continue
            if _DATE_RANGE_RE.fullmatch(candidate):
                continue
            return candidate
        return ""

    @staticmethod
    def _extract_name(text: str) -> str:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:10]
        for line in lines:
            labelled = _NAME_LABEL_RE.match(line)
            if labelled:
                return labelled.group("n").strip(" *_")
        for line in lines:
            candidate = line.lstrip("#").strip().strip("*_").strip()
            if candidate.casefold() in _NOT_A_NAME:
                continue
            if _ANY_HEADER_RE.match(candidate):
                continue
            if _NAME_RE.fullmatch(candidate):
                return candidate
        return ""

    # ------------------------------------------------- education and others

    def extract_education(self, text: str) -> tuple[str, ...]:
        """Return the education entries (one per line of the section)."""
        return self._entries(self._first_section(EDUCATION_HEADERS, text))

    def extract_experience(self, text: str) -> tuple[str, ...]:
        """Return the experience entries (one per role line or bullet)."""
        return self._entries(self._first_section(EXPERIENCE_HEADERS, text))

    def extract_certifications(self, text: str) -> tuple[str, ...]:
        """Return the certification entries (one per line of the section)."""
        return self._entries(self._first_section(CERTIFICATION_HEADERS, text))

    # -------------------------------------------------------------- skills

    def extract_skills(self, text: str) -> tuple[str, ...]:
        """Return the skills mentioned in *text*, as written by the candidate.

        The whole résumé is scanned (skills also appear in experience bullets),
        except ambiguous single-letter skills such as ``R``, which are only
        accepted inside the skills section. Results keep the order of first
        appearance and are de-duplicated ignoring case and ``.``/``-``/space.
        """
        text = _normalize_newlines(text)
        hits: list[tuple[int, int, str]] = []
        for pattern in _SKILL_PATTERNS:
            if pattern.skills_section_only:
                continue
            for m in pattern.regex.finditer(text):
                hits.append((m.start(), m.end(), m.group(0)))

        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        ordered: list[str] = []
        last_end = -1
        for start, end, value in hits:  # drop overlaps, keep the longest
            if start >= last_end:
                ordered.append(value)
                last_end = end

        skills_section = self._first_section(SKILL_HEADERS, text)
        for pattern in _SKILL_PATTERNS:
            if pattern.skills_section_only and skills_section:
                ordered.extend(
                    m.group(0) for m in pattern.regex.finditer(skills_section)
                )

        seen: set[str] = set()
        unique: list[str] = []
        for value in ordered:
            key = _dedup_key(value)
            if key not in seen:
                seen.add(key)
                unique.append(value)
        return tuple(unique)

    # --------------------------------------------------------------- facade

    def extract(self, text: str) -> RawProfile:
        """Run every extraction and assemble the :class:`RawProfile`."""
        return RawProfile(
            contact=self.extract_contact(text),
            education=self.extract_education(text),
            experience=self.extract_experience(text),
            certifications=self.extract_certifications(text),
            raw_skills=self.extract_skills(text),
        )
