from pathlib import Path

from src.core.models.models import CandidateReport, ClassificationResult

class ResumeLensPipeline:
    def __init__(self, loader_factory, extractor, normalizer, projector, classifier, profiles):
        self._loader_factory = loader_factory
        self._extractor = extractor
        self._normalizer = normalizer
        self._projector = projector
        self._classifier = classifier
        self._profiles = profiles

    def process(self, file_path: str | Path) -> CandidateReport:
        path = Path(file_path)
        text = self._loader_factory.get_loader(path).load(path)
        raw_profile = self._extractor.extract(text)

        normalized = self._normalizer.normalize_skills(raw_profile.raw_skills)

        classifications = [
            self._classifier.classify(
                self._projector.project(normalized.recognized, profile),
                profile,
            )
            for profile in self._profiles
        ]

        return CandidateReport(
            contact=raw_profile.contact,
            education=raw_profile.education,
            experience=raw_profile.experience,
            certifications=raw_profile.certifications,
            skills=normalized.recognized,
            classifications=tuple(classifications),
            unrecognized_skills=normalized.unrecognized,
        )