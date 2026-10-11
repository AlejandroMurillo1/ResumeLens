from dataclasses import dataclass

import streamlit as st

from src.core.ingestion.loader_factory import LoaderFactory
from src.core.extraction.content_extractor import ContentExtractor
from src.core.normalization import build_default_normalizer
from src.core.profiles import ProfileRegistry
from src.core.projection import ProfileProjector
from src.core.classification import ProfileClassifier
from src.core.dsl import DSLValidator, GRAMMAR_PATH
from src.core.pipeline.orchestrator import ResumeLensPipeline


@dataclass(frozen=True)
class AppResources:
    pipeline: ResumeLensPipeline
    dsl_validator: DSLValidator


@st.cache_resource
def build_resources() -> AppResources:
    profiles = ProfileRegistry().get_all()

    pipeline = ResumeLensPipeline(
        loader_factory=LoaderFactory,
        extractor=ContentExtractor(),
        normalizer=build_default_normalizer(),
        projector=ProfileProjector(),
        classifier=ProfileClassifier(),
        profiles=profiles,
    )

    dsl_validator = DSLValidator(
        grammar_path=GRAMMAR_PATH,
        valid_profile_names=tuple(p.name for p in profiles),
    )

    return AppResources(pipeline=pipeline, dsl_validator=dsl_validator)