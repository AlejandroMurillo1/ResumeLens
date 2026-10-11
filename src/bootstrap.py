# src/bootstrap.py
import streamlit as st

from src.core.ingestion.loader_factory import LoaderFactory
from src.core.extraction.content_extractor import ContentExtractor
from src.core.normalization import build_default_normalizer
from src.core.profiles import ProfileRegistry
from src.core.dsl import DSLValidator
from src.core.pipeline.orchestrator import ResumeLensPipeline

from src.core.fake_objects import FakeProjector, FakeAutomatonFactory  # projection/classification: pendientes


@st.cache_resource
def build_pipeline() -> ResumeLensPipeline:
    profiles = ProfileRegistry().get_all()

    dsl_validator = DSLValidator(
        grammar_path="candidate.tx",  # ajusta a la ruta real en tu repo
        valid_profile_names=tuple(p.name for p in profiles),
    )

    return ResumeLensPipeline(
        loader_factory=LoaderFactory,
        extractor=ContentExtractor(),
        normalizer=build_default_normalizer(),
        projector=FakeProjector(),               # TODO: reemplazar cuando llegue projection
        automaton_factory=FakeAutomatonFactory(), # TODO: reemplazar cuando llegue classification
        profiles=profiles,
    )