# Profiles module — Test cases

Scope: `ProfileRegistry` (`src/core/profiles/profile_registry.py`) and the
four default profiles declared in `src/core/profiles/definitions.py`
(`Profile`, `SkillGroup` and `GroupRule` live in `src/core/models/models.py`).
Implemented in `src/test/profiles_tests.py`.

Shared fixtures and helpers:

- `registry`: a fresh `ProfileRegistry()` per test (it loads the default
  profiles on construction).
- `_group(profile, label)`: returns the `SkillGroup` with that label.
- `_labels(profile)`: group labels in order.
- `_required(profile)`: the set of tokens in `REQUIRED` groups.
- `RELATIONAL_DB = ("SQL", "POSTGRESQL", "ORACLE", "MYSQL")` and
  `NON_RELATIONAL_DB = ("NOSQL", "MONGODB", "REDIS", "CASSANDRA")`.

## `ProfileRegistry`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRF-REG-01 | Default profiles are loaded in registration order | `registry` | `get_all()` names are `Full Stack Developer`, `Machine Learning Engineer`, `Cloud Engineer`, `Data Analyst` |
| PRF-REG-02 | `get_all()` returns `Profile` objects in a fresh list | `registry`; the returned list is cleared | Every item is a `Profile`; clearing the list does not affect the registry (`len(registry.get_all()) == 4`) |
| PRF-REG-03 | Lookup by exact name | `registry`, each of the 4 names (parametrized) | `get_by_name(name).name == name` |
| PRF-REG-04 | Lookup ignores case and surrounding spaces | `registry`, `"  cloud ENGINEER "` | Returns the `Cloud Engineer` profile |
| PRF-REG-05 | Unknown profile name | `registry`, `"Astronaut"` | Raises `KeyError` whose message contains `"Unknown profile"` |
| PRF-REG-06 | `load_profiles()` is idempotent | `registry`, `load_profiles()` called twice | `get_all()` still returns 4 profiles |

## Structural invariants (all profiles)

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRF-DEF-01 | Every profile and group is well formed | `registry` | Each profile has groups; each group has at least one token and a `GroupRule` |
| PRF-DEF-02 | Tokens are uppercase identifiers | `registry` | For every token in every `vocabulary`: `token == token.upper()` and it contains no spaces |
| PRF-DEF-03 | Group labels are unique inside a profile | `registry` | No label repeats within a profile |
| PRF-DEF-04 | No token repeated inside a profile | `registry` | `len(vocabulary) == len(set(vocabulary))` for every profile (the classifier requires each token to belong to a single group) |
| PRF-DEF-05 | No token repeated inside a single group | `registry` | Each group's tokens are unique |
| PRF-DEF-06 | `Relational database` group is identical wherever it appears | `registry`; Full Stack, ML Engineer and Data Analyst | Rule is `ANY_OF` and tokens equal `RELATIONAL_DB` in all three |
| PRF-DEF-07 | `vocabulary` flattens groups in order | `registry`, Cloud Engineer | First three tokens are `AWS`, `AZURE`, `GCP`; last token is `GIT` |
| PRF-DEF-08 | Profiles are immutable | `registry`, assign `name` on a profile | Assignment raises (frozen dataclass) |

## Profile contents

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRF-FS-01 | Full Stack Developer groups, tokens and rules | `registry` | Group order: `Language`, `Frontend framework`, `Backend framework`, `REST APIs`, `Relational database`, `Non-relational database`, `Version control`. Tokens: Language `JAVASCRIPT, TYPESCRIPT`; Frontend `REACT, ANGULAR, VUE`; Backend `NODE_JS, DJANGO, SPRING_BOOT` (`ANY_OF`); Relational `RELATIONAL_DB`; Non-relational `NON_RELATIONAL_DB` (`ANY_OF`). Required tokens are exactly `{"REST_API", "GIT"}` |
| PRF-FS-02 | Full Stack vocabulary covers both database kinds | `registry` | `MYSQL` comes before `NOSQL` in `vocabulary`; it contains `MONGODB`, `REDIS`, `CASSANDRA` and `POSTGRESQL` |
| PRF-ML-01 | Machine Learning Engineer groups, tokens and rules | `registry` | Group order: `Language`, `Data processing`, `Classical ML`, `Deep learning`, `Model development`, `Relational database`, `Version control`. Language is `PYTHON`; Data processing `PANDAS, NUMPY`; Deep learning is `ANY_OF`. Required tokens are exactly `{"PYTHON", "SCIKIT_LEARN", "MACHINE_LEARNING", "GIT"}`; `SQL` is **not** required |
| PRF-CLD-01 | Cloud Engineer tokens and rules | `registry` | Cloud provider `AWS, AZURE, GCP`; CI/CD `JENKINS, GITHUB_ACTIONS, GITLAB`; required tokens are exactly `{"LINUX", "GIT"}` |
| PRF-DA-01 | Data Analyst groups and tokens | `registry` | Group order: `Relational database`, `Analysis tool`, `Visualization`, `Analysis library`. Analysis tool `EXCEL, PYTHON, R`; Visualization `POWER_BI, TABLEAU, LOOKER`; Analysis library `PANDAS, STATISTICS` |
| PRF-DA-02 | Data Analyst has only `ANY_OF` groups | `registry` | Every group is `ANY_OF`; the set of required tokens is empty; `SQL` occurs exactly once in `vocabulary` (any relational database covers the SQL skill) |

## Notes

- **`SQL` in Data Analyst (PRF-DEF-04, PRF-DA-02).** The profile used to list
  `SQL` twice (a `REQUIRED` group and inside the relational group). The
  `Query language` group was removed, so `SQL` is now just one of the relational
  databases and the uniqueness check is strict.
- In the current definitions, single-qualification groups (`Git`, `Linux`,
  `REST_API`, `PYTHON`) are `REQUIRED`; no test enforces that convention, it is
  only asserted through the "required tokens" checks of each profile. Data
  Analyst has no `REQUIRED` group.
- Group order is the canonical category order used by later stages, so
  PRF-FS-01, PRF-ML-01 and PRF-DA-01 assert the full ordered list of labels,
  not just their membership.
- These tests only cover the **declaration** of the profiles. Whether every
  token exists in the normalisation vocabulary is not checked here and belongs
  to a cross-module test once Stage 2 is aligned.
- Run with `pytest src/test/profiles_tests.py` from the repository root.
