from src.core.models.models import (
    RawProfile,
    ContactInfo,
    Profile,
    SkillGroup,
    GroupRule,
    ClassificationResult
)


def fake_extract_all(text: str) -> RawProfile:
    return RawProfile(
        contact=ContactInfo(name="Test Candidate", email="test@test.com", phone="000"),
        education=("BSc Computer Science",),
        experience=("Backend intern, 6 months",),
        certifications=(),
        raw_skills=("git", "react", "aws", "nosql"),
    )


FAKE_PROFILES = (
    Profile(
        name="Cloud Engineer",
        groups=(SkillGroup("Cloud platform", GroupRule.ANY_OF, ("AWS", "AZURE", "GCP")),),
    ),
    Profile(
        name="Full Stack Developer",
        groups=(SkillGroup("Version control", GroupRule.REQUIRED, ("GIT",)),),
    ),
)


class FakeAutomatonFactory:
    @staticmethod
    def build(self, profile: Profile):
        return _FakeAutomaton()


class _FakeAutomaton:
    @staticmethod
    def accepts(self, sequence: list[str]) -> bool:
        return len(sequence) > 0  # placeholder: "aceptado si hay algo que evaluar"

class FakeProjector:
    @staticmethod
    def project(self, tokens: list[str], profile) -> list[str]:
        return [t for t in tokens if t in profile.vocabulary]