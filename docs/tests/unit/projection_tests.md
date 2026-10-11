# Projection module — Test cases

Scope: `ProfileProjector` (`src/core/projection/profile_projector.py`).
`project(tokens, profile) -> tuple[str, ...]` takes the canonical tokens of a
candidate and returns the word that the classifier will evaluate for that
profile: only tokens of the profile's vocabulary, each once, in canonical
order (group order first, then token order inside the group). Implemented in
`src/test/projection_tests.py`.

Shared fixtures:

- `projector`: a fresh `ProfileProjector()`.
- `registry`: a fresh `ProfileRegistry()` with the four default profiles.

Relevant profile facts used below (from `src/core/profiles/definitions.py`):

- Full Stack Developer group order: Language, Frontend framework, Backend
  framework, REST APIs, Relational database, Non-relational database,
  Version control.
- Data Analyst's first group is `Relational database` with tokens `SQL`, `POSTGRESQL`, `ORACLE`, `MYSQL`, in that order.

## Filtering, ordering and duplicates

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRJ-01 | Tokens outside the profile vocabulary are dropped | Full Stack, `["DOCKER", "GIT"]` | `("GIT",)` |
| PRJ-02 | Order follows the groups of the profile, not the input | Full Stack, `["GIT", "REACT", "SQL", "DOCKER", "NODE_JS", "JAVASCRIPT", "REST_API"]` | `("JAVASCRIPT", "REACT", "NODE_JS", "REST_API", "SQL", "GIT")` |
| PRJ-03 | Order inside one group follows the profile | Full Stack, `["VUE", "ANGULAR", "REACT"]` | `("REACT", "ANGULAR", "VUE")` |
| PRJ-04 | Duplicates are removed | Full Stack, `["GIT", "GIT", "SQL", "GIT"]` | `("SQL", "GIT")` |
| PRJ-05 | Empty input | Cloud Engineer, `[]` | `()` |
| PRJ-06 | No token in common with the profile | Machine Learning Engineer, `["LOOKER", "TABLEAU"]` | `()` |
| PRJ-07 | Return type | Cloud Engineer, `["GIT"]` | The result is a `tuple` |
| PRJ-08 | Any iterable is accepted | Cloud Engineer, the tokens `GIT`, `DOCKER` given as a tuple, a set and a generator | `("DOCKER", "GIT")` for all three |
| PRJ-09 | Tokens must already be canonical | Cloud Engineer, `["git", "Git", "docker"]` | `()` (matching is exact and case-sensitive) |
| PRJ-10 | The input is not modified | Cloud Engineer, `["GIT", "DOCKER", "GIT"]` | The list is unchanged after the call |

## One candidate, four profiles

Candidate used by PRJ-11: `["PYTHON", "SQL", "GIT", "PANDAS", "EXCEL", "DOCKER", "LINUX"]`.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRJ-11 | The same tokens give a different word per profile (parametrized, 4 cases) | The candidate above projected onto each profile | Full Stack `("SQL", "GIT")`; Machine Learning Engineer `("PYTHON", "PANDAS", "SQL", "GIT")`; Cloud Engineer `("DOCKER", "LINUX", "GIT")`; Data Analyst `("SQL", "EXCEL", "PYTHON", "PANDAS")` |
| PRJ-12 | Order inside the relational group follows the profile | Data Analyst, `["MYSQL", "SQL", "POSTGRESQL"]` | `("SQL", "POSTGRESQL", "MYSQL")` |
| PRJ-13 | Full vocabulary in reverse order | Each of the four profiles, `reversed(profile.vocabulary)` | `profile.vocabulary` itself |

## Order independence

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRJ-14 | Every permutation of the input gives the same word | Full Stack, the 120 permutations of `["GIT", "REACT", "NODE_JS", "SQL", "JAVASCRIPT"]` | A single result: `("JAVASCRIPT", "REACT", "NODE_JS", "SQL", "GIT")` |

## Stages 1 → 2 → projection

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| PRJ-15 | A real skills line goes through extraction, normalization and projection | `"Skills\nGit, React.js, Node.js, PostgreSQL, Docker, JS, REST APIs\n"` → `ContentExtractor.extract_skills` → `build_default_normalizer().normalize_skills(...).recognized` → `project` | Full Stack: `("JAVASCRIPT", "REACT", "NODE_JS", "REST_API", "POSTGRESQL", "GIT")`; Cloud Engineer: `("DOCKER", "GIT")` |

## Notes

- Projection does not use `GroupRule`. A token belongs to one group only, so no token needs special handling. Whether a word satisfies `REQUIRED`
  and `ANY_OF` groups is decided by the classifier, not here.
- PRJ-13 is a property check: because the projector sorts by first position in
  the vocabulary, projecting the whole vocabulary in any order must give the
  vocabulary itself.
- PRJ-15 couples three stages. If an extractor pattern, a vocabulary spelling
  or a profile token changes, this is the case that notices a mismatch.
- Run with `pytest src/test/projection_tests.py` from the repository root.
