from pathlib import Path

from src.core.models.models import CandidateReport, ClassificationResult

class ResumeLensPipeline:
    def __init__(
        self,
        loader_factory,
        extractor,          # ContentExtractor-like: .extract(text) -> RawProfile
        normalizer,          # SkillNormalizer-like: .normalize_skills(raws) -> NormalizedSkills
        projector,           # still a fake today
        profiles,
        automaton_factory,   # still a fake today
    ) -> None:
        self._loader_factory = loader_factory
        self._extractor = extractor
        self._normalizer = normalizer
        self._projector = projector
        self._profiles = profiles
        self._automatons = {p.name: automaton_factory.build(p) for p in profiles}

    def process(self, file_path: str | Path) -> CandidateReport:
        path = Path(file_path)
        text = self._loader_factory.get_loader(path).load(path)
        raw_profile = self._extractor.extract(text)

        normalized = self._normalizer.normalize_skills(raw_profile.raw_skills)

        classifications = []
        for profile in self._profiles:
            sequence = self._projector.project(list(normalized.recognized), profile)
            accepted = self._automatons[profile.name].accepts(sequence)
            classifications.append(
                ClassificationResult(
                    profile_name=profile.name,
                    accepted=accepted,
                    sequence=tuple(sequence),
                )
            )

        return CandidateReport(
            contact=raw_profile.contact,
            education=raw_profile.education,
            experience=raw_profile.experience,
            certifications=raw_profile.certifications,
            skills=normalized.recognized,
            classifications=tuple(classifications),
            unrecognized_skills=normalized.unrecognized,
        )