"""Tests for StrippingTransducer, the full vocabulary and normalize_skills."""

import re

import pytest

from src.core.extraction import ContentExtractor
from src.core.normalization import (
    VOCABULARY, CaseFoldingTransducer, SkillNormalizer, StrippingTransducer,
    build_default_normalizer, build_vocabulary_fst,
)
from src.core.profiles import ProfileRegistry


@pytest.fixture
def stripper() -> StrippingTransducer:
    return StrippingTransducer()


@pytest.fixture
def normalizer() -> SkillNormalizer:
    return build_default_normalizer()


# ------------------------------------------------------ StrippingTransducer

class TestStrippingTransducer:
    @pytest.mark.parametrize("raw, expected", [
        ("React.js", "React js"),
        ("Node.js", "Node js"),
        ("scikit-learn", "scikit learn"),
        ("snake_case", "snake case"),
        ("GitLab CI/CD", "GitLab CI CD"),
        ("  Amazon   Web  Services ", "Amazon Web Services"),
        ("..React..", "React"),
        ("a - b", "a b"),
        ("k8s", "k8s"),
        ("PowerBI", "PowerBI"),
        ("Python 3.11", "Python 3 11"),
        ("", ""),
        ("...", ""),
    ])
    def test_collapses_separators_and_keeps_everything_else(self, stripper, raw, expected):
        assert stripper.apply(raw) == expected

    def test_does_not_change_case(self, stripper):
        assert stripper.apply("JaVa-ScRiPt") == "JaVa ScRiPt"

    @pytest.mark.parametrize("raw", ["C++", "C#", "Ñandú", "a@b", "R&D"])
    def test_character_outside_alphabet_raises(self, stripper, raw):
        with pytest.raises(ValueError, match="Unexpected character"):
            stripper.apply(raw)

    def test_is_idempotent(self, stripper):
        once = stripper.apply(" .React--js/ ")
        assert stripper.apply(once) == once


# ------------------------------------------------ SkillNormalizer + stripper

class TestNormalizerWithStripper:
    def test_without_stripper_punctuation_still_raises(self):
        vocab = build_vocabulary_fst({"REACT": ["REACT", "REACT JS"]})
        bare = SkillNormalizer(CaseFoldingTransducer(), vocab)  # old signature
        assert bare.normalize("react") == "REACT"
        with pytest.raises(ValueError):
            bare.normalize("React.js")

    def test_with_stripper_punctuation_is_normalised(self):
        vocab = build_vocabulary_fst({"REACT": ["REACT", "REACT JS"]})
        n = SkillNormalizer(CaseFoldingTransducer(), vocab, StrippingTransducer())
        assert n.normalize("React.js") == "REACT"

    @pytest.mark.parametrize("raw", ["", "   ", "...", " - "])
    def test_empty_after_cleaning_is_unrecognized(self, normalizer, raw):
        assert normalizer.normalize(raw) is None

    @pytest.mark.parametrize("raw", ["GitHub", "Dockerfile", "Java", "Excellent"])
    def test_unknown_skill_returns_none(self, normalizer, raw):
        assert normalizer.normalize(raw) is None

    def test_character_outside_alphabet_still_raises(self, normalizer):
        with pytest.raises(ValueError):
            normalizer.normalize("C++")


# --------------------------------------------------------- default vocabulary

SURFACE_FORMS = [
    ("JS", "JAVASCRIPT"), ("JavaScript", "JAVASCRIPT"), ("java script", "JAVASCRIPT"),
    ("ECMAScript", "JAVASCRIPT"), ("TypeScript", "TYPESCRIPT"), ("type-script", "TYPESCRIPT"),
    ("Python", "PYTHON"), ("Python3", "PYTHON"), ("Python 3", "PYTHON"),
    ("Python-3", "PYTHON"), ("Python 3.11", "PYTHON"), ("Python3.8", "PYTHON"),
    ("React", "REACT"), ("React.js", "REACT"), ("ReactJS", "REACT"),
    ("React js", "REACT"), ("React-js", "REACT"),
    ("AngularJS", "ANGULAR"), ("Angular.js", "ANGULAR"),
    ("Vue.js", "VUE"), ("VueJS", "VUE"),
    ("Node.js", "NODE_JS"), ("NodeJS", "NODE_JS"), ("node js", "NODE_JS"), ("Node", "NODE_JS"),
    ("Django", "DJANGO"), ("Spring Boot", "SPRING_BOOT"), ("SpringBoot", "SPRING_BOOT"),
    ("spring-boot", "SPRING_BOOT"),
    ("REST API", "REST_API"), ("RESTful APIs", "REST_API"), ("REST-API", "REST_API"),
    ("REST", "REST_API"), ("RESTful", "REST_API"),
    ("SQL", "SQL"), ("NoSQL", "NOSQL"), ("No-SQL", "NOSQL"),
    ("PostgreSQL", "POSTGRESQL"), ("Postgres", "POSTGRESQL"), ("Postgre SQL", "POSTGRESQL"),
    ("MySQL", "MYSQL"), ("My-SQL", "MYSQL"),
    ("Mongo", "MONGODB"), ("MongoDB", "MONGODB"), ("Mongo DB", "MONGODB"),
    ("Oracle", "ORACLE"), ("Oracle DB", "ORACLE"),
    ("Redis", "REDIS"), ("Cassandra", "CASSANDRA"), ("Casandra", "CASSANDRA"),
    ("Pandas", "PANDAS"), ("NumPy", "NUMPY"), ("Num-Py", "NUMPY"),
    ("sklearn", "SCIKIT_LEARN"), ("scikit-learn", "SCIKIT_LEARN"), ("Scikit Learn", "SCIKIT_LEARN"),
    ("TensorFlow", "TENSORFLOW"), ("PyTorch", "PYTORCH"),
    ("Machine Learning", "MACHINE_LEARNING"), ("machine-learning", "MACHINE_LEARNING"),
    ("ML", "MACHINE_LEARNING"),
    ("Statistics", "STATISTICS"), ("Statistical Analysis", "STATISTICS"),
    ("AWS", "AWS"), ("Amazon Web Services", "AWS"), ("Azure", "AZURE"),
    ("GCP", "GCP"), ("Google Cloud", "GCP"), ("Google Cloud Platform", "GCP"),
    ("Docker", "DOCKER"), ("k8s", "KUBERNETES"), ("Kubernetes", "KUBERNETES"),
    ("Ansible", "ANSIBLE"), ("Terraform", "TERRAFORM"),
    ("CloudFormation", "CLOUDFORMATION"), ("Cloud-Formation", "CLOUDFORMATION"),
    ("Jenkins", "JENKINS"),
    ("GitHub Actions", "GITHUB_ACTIONS"), ("github-actions", "GITHUB_ACTIONS"),
    ("GitLab", "GITLAB"), ("GitLab CI", "GITLAB"), ("GitLab CI/CD", "GITLAB"),
    ("GitLab-CI", "GITLAB"), ("GitLabCI/CD", "GITLAB"),
    ("Linux", "LINUX"), ("Git", "GIT"),
    ("Excel", "EXCEL"), ("MS Excel", "EXCEL"), ("Microsoft Excel", "EXCEL"), ("ms-excel", "EXCEL"),
    ("Power BI", "POWER_BI"), ("PowerBI", "POWER_BI"), ("power-bi", "POWER_BI"),
    ("Tableau", "TABLEAU"), ("Looker", "LOOKER"), ("R", "R"),
]


class TestDefaultVocabulary:
    @pytest.mark.parametrize("raw, expected", SURFACE_FORMS)
    def test_surface_form_maps_to_canonical_token(self, normalizer, raw, expected):
        assert normalizer.normalize(raw) == expected

    def test_spellings_are_in_post_cleaning_form(self):
        """Every spelling must be reachable: upper case, [A-Z0-9 ], single spaces."""
        for canonical, spellings in VOCABULARY.items():
            for spelling in spellings:
                assert re.fullmatch(r"[A-Z0-9]+(?: [A-Z0-9]+)*", spelling), (canonical, spelling)

    def test_no_spelling_is_shared_between_tokens(self):
        owners: dict[str, str] = {}
        for canonical, spellings in VOCABULARY.items():
            for spelling in spellings:
                assert owners.setdefault(spelling, canonical) == canonical, spelling

    def test_ambiguous_vocabulary_is_rejected_at_build_time(self):
        with pytest.raises(ValueError, match="both"):
            build_vocabulary_fst({"A": ["X"], "B": ["X"]})

    def test_vocabulary_matches_profile_tokens_exactly(self):
        profile_tokens = {t for p in ProfileRegistry().get_all() for t in p.vocabulary}
        assert set(VOCABULARY) == profile_tokens


# ------------------------------------------------------------ normalize_skills

class TestNormalizeSkills:
    def test_recognized_are_deduplicated_in_first_seen_order(self, normalizer):
        result = normalizer.normalize_skills(["git", "JS", "JavaScript", "GIT", "Docker"])
        assert result.recognized == ("GIT", "JAVASCRIPT", "DOCKER")
        assert result.unrecognized == ()

    def test_unrecognized_are_separated_and_deduplicated(self, normalizer):
        result = normalizer.normalize_skills(["GitHub", "git", "github", "  Java  "])
        assert result.recognized == ("GIT",)
        assert result.unrecognized == ("GitHub", "Java")

    def test_out_of_alphabet_goes_to_unrecognized_instead_of_raising(self, normalizer):
        result = normalizer.normalize_skills(["C++", "Python"])
        assert result.recognized == ("PYTHON",)
        assert result.unrecognized == ("C++",)

    def test_blank_entries_are_ignored(self, normalizer):
        result = normalizer.normalize_skills(["", "   ", "..."])
        assert result.recognized == () and result.unrecognized == ("...",)

    def test_empty_input(self, normalizer):
        result = normalizer.normalize_skills([])
        assert result.recognized == () and result.unrecognized == ()


# ------------------------------------------------ Stage 1 -> Stage 2 alignment

ALL_SKILLS_TEXT = (
    "Skills\n"
    "JS, TypeScript, Python3.11, React.js, AngularJS, Vue.js, Node.js, Django, "
    "Spring Boot, RESTful APIs, SQL, NoSQL, PostgreSQL, MySQL, MongoDB, Oracle DB, "
    "Redis, Casandra, Pandas, NumPy, sklearn, TensorFlow, PyTorch, Machine Learning, "
    "Statistics, AWS, Azure, Google Cloud Platform, Docker, k8s, Ansible, Terraform, "
    "CloudFormation, Jenkins, GitHub Actions, GitLab CI/CD, Linux, Git, Excel, "
    "Power BI, Tableau, Looker, R\n"
)


class TestExtractionToNormalization:
    def test_every_extracted_skill_is_recognized_and_all_tokens_are_reachable(self, normalizer):
        raw = ContentExtractor().extract_skills(ALL_SKILLS_TEXT)
        result = normalizer.normalize_skills(raw)
        assert result.unrecognized == ()
        assert set(result.recognized) == set(VOCABULARY)
