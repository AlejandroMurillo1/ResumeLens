"""Canonical skill vocabulary: canonical token -> accepted spellings.

Spellings are written in the form the vocabulary FST actually sees, i.e. after
``StrippingTransducer`` (runs of ``space . - _ /`` become one space) and
``CaseFoldingTransducer`` (upper case). So ``scikit-learn`` is listed as
``SCIKIT LEARN`` and ``React.js`` as ``REACT JS``; ``ReactJS`` stays ``REACTJS``.

The canonical tokens are exactly those used by the profiles in
``src/core/profiles/definitions.py``, and the spellings cover every variant that
``ContentExtractor.extract_skills`` can return. When you add a pattern to the
extractor, add its spellings here.
"""

from __future__ import annotations

from itertools import product


def _cross(*groups: list[str]) -> list[str]:
    """Concatenate one choice from each group (cartesian product)."""
    return ["".join(parts) for parts in product(*groups)]


# The extractor accepts "Python", "Python3", "Python 3" and "Python 3.<minor>".
_PYTHON_VERSIONS = [
    spelling
    for minor in range(20)
    for spelling in (f"PYTHON 3 {minor}", f"PYTHON3 {minor}")
]

VOCABULARY: dict[str, list[str]] = {
    # Languages
    "JAVASCRIPT": ["JAVASCRIPT", "JAVA SCRIPT", "JS", "ECMASCRIPT"],
    "TYPESCRIPT": ["TYPESCRIPT", "TYPE SCRIPT"],
    "PYTHON": ["PYTHON", "PYTHON3", "PYTHON 3", *_PYTHON_VERSIONS],
    # Front end
    "REACT": ["REACT", "REACTJS", "REACT JS"],
    "ANGULAR": ["ANGULAR", "ANGULARJS", "ANGULAR JS"],
    "VUE": ["VUE", "VUEJS", "VUE JS"],
    # Back end
    "NODE_JS": ["NODE", "NODEJS", "NODE JS"],
    "DJANGO": ["DJANGO"],
    "SPRING_BOOT": ["SPRINGBOOT", "SPRING BOOT"],
    "REST_API": [
        "REST", "RESTFUL",
        *_cross(["REST", "RESTFUL"], ["", " "], ["API", "APIS"]),
    ],
    # Databases
    "SQL": ["SQL"],
    "NOSQL": ["NOSQL", "NO SQL"],
    "POSTGRESQL": ["POSTGRES", "POSTGRESQL", "POSTGRE SQL"],
    "MYSQL": ["MYSQL", "MY SQL"],
    "MONGODB": ["MONGO", "MONGODB", "MONGO DB"],
    "ORACLE": ["ORACLE", "ORACLEDB", "ORACLE DB"],
    "REDIS": ["REDIS"],
    "CASSANDRA": ["CASSANDRA", "CASANDRA"],
    # Data / ML
    "PANDAS": ["PANDAS"],
    "NUMPY": ["NUMPY", "NUM PY"],
    "SCIKIT_LEARN": ["SCIKITLEARN", "SCIKIT LEARN", "SKLEARN"],
    "TENSORFLOW": ["TENSORFLOW", "TENSOR FLOW"],
    "PYTORCH": ["PYTORCH", "PY TORCH"],
    "MACHINE_LEARNING": ["MACHINE LEARNING", "ML"],
    "STATISTICS": ["STATISTICS", "STATISTICAL ANALYSIS"],
    # Cloud / DevOps
    "AWS": ["AWS", "AMAZON WEB SERVICES"],
    "AZURE": ["AZURE"],
    "GCP": ["GCP", "GOOGLE CLOUD", "GOOGLE CLOUD PLATFORM"],
    "DOCKER": ["DOCKER"],
    "KUBERNETES": ["KUBERNETES", "K8S"],
    "ANSIBLE": ["ANSIBLE"],
    "TERRAFORM": ["TERRAFORM"],
    "CLOUDFORMATION": ["CLOUDFORMATION", "CLOUD FORMATION"],
    "JENKINS": ["JENKINS"],
    "GITHUB_ACTIONS": ["GITHUBACTIONS", "GITHUB ACTIONS"],
    "GITLAB": ["GITLAB", "GITLAB CI", "GITLABCI", "GITLAB CI CD", "GITLABCI CD"],
    "LINUX": ["LINUX"],
    "GIT": ["GIT"],
    # BI / analysis tools
    "EXCEL": ["EXCEL", "MS EXCEL", "MICROSOFT EXCEL"],
    "POWER_BI": ["POWERBI", "POWER BI"],
    "TABLEAU": ["TABLEAU"],
    "LOOKER": ["LOOKER"],
    "R": ["R"],
}
