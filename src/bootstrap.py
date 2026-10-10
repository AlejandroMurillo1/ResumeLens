# src/bootstrap.py
import streamlit as st

from core.ingestion.loader_factory import LoaderFactory
from core.normalization import CaseFoldingTransducer, build_vocabulary_fst, SkillNormalizer, VOCABULARY
from core.dsl.validator import DSLValidator
from core.pipeline.orchestrator import ResumeLensPipeline

from core.fake_objects import fake_extract_all, FAKE_PROFILES, FakeAutomatonFactory


@st.cache_resource
def build_pipeline() -> ResumeLensPipeline:
    case_folder = CaseFoldingTransducer()
    vocabulary_fst = build_vocabulary_fst(VOCABULARY)
    normalizer = SkillNormalizer(case_folder, vocabulary_fst)

    profiles = FAKE_PROFILES                      # reemplazar por ProfileRegistry().get_all()
    automaton_factory = FakeAutomatonFactory()     # reemplazar por el AutomatonFactory real
    extract_all = fake_extract_all                 # reemplazar por extraction.extract_all

    dsl_validator = DSLValidator(valid_profile_names=[p.name for p in profiles])

    return ResumeLensPipeline(
        loader_factory=LoaderFactory,
        extract_all=extract_all,
        normalizer=normalizer,
        profiles=profiles,
        automaton_factory=automaton_factory,
        dsl_validator=dsl_validator
    )