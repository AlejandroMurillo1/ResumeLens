import tempfile

from src.core.classification import ProfileClassifier
from src.core.dsl.renderer import render_markdown
from src.core.ingestion.loader_factory import LoaderFactory
from src.core.extraction.content_extractor import ContentExtractor
from src.core.normalization import build_default_normalizer
from src.core.profiles import ProfileRegistry
from src.core.pipeline.orchestrator import ResumeLensPipeline
from src.core.dsl import DSLValidator, GRAMMAR_PATH, DSLError
from src.core.dsl.serializer import to_dsl
from src.core.projection import ProfileProjector

SAMPLE_CV = """\
Jane Doe
jane.doe@email.com | +1 555 234 5678

EDUCATION
BSc Computer Science, Tech University, 2021

EXPERIENCE
Backend Developer, Acme Corp, 2021-2024

SKILLS
Python, Django, React.js, JavaScript, PostgreSQL, MongoDB, REST API, Docker, AWS, Git
"""

with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
    f.write(SAMPLE_CV)
    path = f.name

profiles = ProfileRegistry().get_all()
pipeline = ResumeLensPipeline(
    loader_factory=LoaderFactory,
    extractor=ContentExtractor(),
    normalizer=build_default_normalizer(),
    projector=ProfileProjector(),
    classifier=ProfileClassifier(),
    profiles=profiles,
)

report = pipeline.process(path)
print("Contact:", report.contact)
print("Skills reconocidas:", report.skills)
print("No reconocidas:", report.unrecognized_skills)
for c in report.classifications:
    print(f"  {c.profile_name}: {'ACCEPTED' if c.accepted else 'REJECTED'} — {c.sequence}")

validator = DSLValidator(
    grammar_path=GRAMMAR_PATH,
    valid_profile_names=tuple(p.name for p in profiles),  # los 4 reales, no 2 fijos
)

try:
    dsl_text = to_dsl(report)
    model = validator.validate(dsl_text)
    print(render_markdown(model))
except DSLError as e:
    print(f"[{e.kind.name}] {e.message} (línea {e.line}, columna {e.column})")