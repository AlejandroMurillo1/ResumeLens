from pathlib import Path

from src.core.models.models import CandidateReport, ClassificationResult

class ResumeLensPipeline:
    def __init__(
        self,
        loader_factory,
        extract_all,
        normalizer,
        projector,
        profiles,
        automaton_factory,
    ) -> None:
        self._loader_factory = loader_factory
        self._extract_all = extract_all
        self._normalizer = normalizer
        self._projector = projector
        self._profiles = profiles
        # Built once, here, not per `process()` call.
        self._automatons = {
            profile.name: automaton_factory.build(profile) for profile in profiles
        }

    def process(self, file_path: str | Path) -> CandidateReport:
        path = Path(file_path)
        text = self._loader_factory.get_loader(path).load(path)
        raw_profile = self._extract_all(text)

        canonical_skills: list[str] = []
        unrecognized_skills: list[str] = []
        for raw_skill in raw_profile.raw_skills:
            try:
                canonical = self._normalizer.normalize(raw_skill)
            except ValueError:
                unrecognized_skills.append(raw_skill)
                continue
            if canonical is None:
                unrecognized_skills.append(raw_skill)
            else:
                canonical_skills.append(canonical)

        deduped_skills = list(dict.fromkeys(canonical_skills))  # order-preserving dedupe

        classifications = []
        for profile in self._profiles:
            sequence = self._projector.project(deduped_skills, profile)
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
            skills=tuple(deduped_skills),
            classifications=tuple(classifications),
            unrecognized_skills=tuple(unrecognized_skills),
        )