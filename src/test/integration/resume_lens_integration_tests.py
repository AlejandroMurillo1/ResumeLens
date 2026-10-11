import tempfile
from pathlib import Path

import pytest

from src.core.ingestion.loader_factory import LoaderFactory
from src.core.extraction.content_extractor import ContentExtractor
from src.core.normalization import build_default_normalizer
from src.core.profiles import ProfileRegistry
from src.core.projection import ProfileProjector
from src.core.classification import ProfileClassifier
from src.core.pipeline.orchestrator import ResumeLensPipeline
from src.core.models.models import CandidateReport

FULL_STACK_DEVELOPER = "Full Stack Developer"
MACHINE_LEARNING_ENGINEER = "Machine Learning Engineer"
CLOUD_ENGINEER = "Cloud Engineer"
DATA_ANALYST = "Data Analyst"

_HEADER = """\
Jane Doe
jane.doe@email.com | +1 555 234 5678

EDUCATION
BSc Computer Science, Tech University, 2021

EXPERIENCE
Backend Developer, Acme Corp, 2021-2024

SKILLS
{skills}
"""

CASES = [
    # (id, profile under test, skills line, expected accepted)
    (
        "full_stack-accept",
        FULL_STACK_DEVELOPER,
        "JavaScript, React, Node.js, REST API, PostgreSQL, MongoDB, Git",
        True,
    ),
    (
        "full_stack-reject-missing_required_rest_api",
        FULL_STACK_DEVELOPER,
        "JavaScript, React, Node.js, PostgreSQL, MongoDB, Git",
        False,
    ),
    (
        "ml_engineer-accept",
        MACHINE_LEARNING_ENGINEER,
        "Python, Pandas, Scikit-learn, TensorFlow, Machine Learning, SQL, Git",
        True,
    ),
    (
        "ml_engineer-reject-missing_any_of_data_processing",
        MACHINE_LEARNING_ENGINEER,
        "Python, Scikit-learn, TensorFlow, Machine Learning, SQL, Git",
        False,
    ),
    (
        "cloud_engineer-accept",
        CLOUD_ENGINEER,
        "AWS, Docker, Terraform, Jenkins, Linux, Git",
        True,
    ),
    (
        "cloud_engineer-reject-missing_required_linux",
        CLOUD_ENGINEER,
        "AWS, Docker, Terraform, Jenkins, Git",
        False,
    ),
    (
        "data_analyst-accept",
        DATA_ANALYST,
        "SQL, Excel, Tableau, Pandas",
        True,
    ),
    (
        "data_analyst-reject-missing_any_of_visualization",
        DATA_ANALYST,
        "SQL, Excel, Pandas",
        False,
    ),
]


@pytest.fixture(scope="module")
def pipeline() -> ResumeLensPipeline:
    profiles = ProfileRegistry().get_all()
    return ResumeLensPipeline(
        loader_factory=LoaderFactory,
        extractor=ContentExtractor(),
        normalizer=build_default_normalizer(),
        projector=ProfileProjector(),
        classifier=ProfileClassifier(),
        profiles=profiles,
    )


def _process(pipeline: ResumeLensPipeline, skills: str) -> CandidateReport:
    text = _HEADER.format(skills=skills)
    with tempfile.NamedTemporaryFile(
        suffix=".txt", mode="w", delete=False, encoding="utf-8"
    ) as f:
        f.write(text)
        path = Path(f.name)
    return pipeline.process(path)


def _accepted(report: CandidateReport, profile_name: str) -> bool:
    return next(
        c.accepted for c in report.classifications if c.profile_name == profile_name
    )


@pytest.mark.parametrize(
    "case_id, profile_name, skills, expected",
    CASES,
    ids=[c[0] for c in CASES],
)
def test_pipeline_classification(pipeline, case_id, profile_name, skills, expected):
    report = _process(pipeline, skills)
    assert _accepted(report, profile_name) is expected