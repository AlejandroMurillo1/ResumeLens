"""Declarative definition of the four supported professional profiles.

Rule semantics (evaluated by the classifier, see ``src/core/classification``):

* ``REQUIRED``: every token of the group must be present;
* ``ANY_OF``:   at least one token of the group must be present;
* ``OPTIONAL``: the group imposes no condition.

Convention used below: a single qualification (``Git``, ``Linux``) is
``REQUIRED``; alternatives written with a slash (``React/Angular``) are
``ANY_OF``. *Data Analyst* has only ``ANY_OF`` groups: any relational database
(``SQL`` included) satisfies its database requirement.

Group order is the canonical category order used by projection and
classification; token order inside a group is the total order within that
group. A token must appear in at most one group of a profile, and every token
must exist in the normalisation vocabulary.
"""

from __future__ import annotations

from src.core.models.models import GroupRule, Profile, SkillGroup

FULL_STACK_DEVELOPER = "Full Stack Developer"
MACHINE_LEARNING_ENGINEER = "Machine Learning Engineer"
CLOUD_ENGINEER = "Cloud Engineer"
DATA_ANALYST = "Data Analyst"


def _group(label: str, rule: GroupRule, *tokens: str) -> SkillGroup:
    return SkillGroup(label=label, rule=rule, tokens=tuple(tokens))


def build_default_profiles() -> tuple[Profile, ...]:
    """Return the four profiles, in registration order."""
    any_of, required = GroupRule.ANY_OF, GroupRule.REQUIRED
    return (
        Profile(FULL_STACK_DEVELOPER, (
            _group("Language", any_of, "JAVASCRIPT", "TYPESCRIPT"),
            _group("Frontend framework", any_of, "REACT", "ANGULAR", "VUE"),
            _group("Backend framework", any_of, "NODE_JS", "DJANGO", "SPRING_BOOT"),
            _group("REST APIs", required, "REST_API"),
            _group("Relational database", any_of, "SQL", "POSTGRESQL", "ORACLE", "MYSQL"),
            _group("Non-relational database", any_of, "NOSQL", "MONGODB", "REDIS", "CASSANDRA"),
            _group("Version control", required, "GIT"),
        )),
        Profile(MACHINE_LEARNING_ENGINEER, (
            _group("Language", required, "PYTHON"),
            _group("Data processing", any_of, "PANDAS", "NUMPY"),
            _group("Classical ML", required, "SCIKIT_LEARN"),
            _group("Deep learning", any_of, "TENSORFLOW", "PYTORCH"),
            _group("Model development", required, "MACHINE_LEARNING"),
            _group("Relational database", any_of, "SQL", "POSTGRESQL", "ORACLE", "MYSQL"),
            _group("Version control", required, "GIT"),
        )),
        Profile(CLOUD_ENGINEER, (
            _group("Cloud provider", any_of, "AWS", "AZURE", "GCP"),
            _group("Containers", any_of, "DOCKER", "KUBERNETES"),
            _group("Infrastructure as code", any_of, "ANSIBLE", "TERRAFORM", "CLOUDFORMATION"),
            _group("CI/CD", any_of, "JENKINS", "GITHUB_ACTIONS", "GITLAB"),
            _group("Operating system", required, "LINUX"),
            _group("Version control", required, "GIT"),
        )),
        Profile(DATA_ANALYST, (
            _group("Relational database", any_of, "SQL", "POSTGRESQL", "ORACLE", "MYSQL"),
            _group("Analysis tool", any_of, "EXCEL", "PYTHON", "R"),
            _group("Visualization", any_of, "POWER_BI", "TABLEAU", "LOOKER"),
            _group("Analysis library", any_of, "PANDAS", "STATISTICS"),
        )),
    )
