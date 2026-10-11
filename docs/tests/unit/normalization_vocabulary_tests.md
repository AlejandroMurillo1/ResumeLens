# Normalization module (full vocabulary) — Test cases

Scope: `StrippingTransducer`, `SkillNormalizer` configured with a stripper,
`SkillNormalizer.normalize_skills`, the full `VOCABULARY`
(`src/core/normalization/vocabulary.py`) and its alignment with Stage 1
(`ContentExtractor`) and with the profiles. Implemented in
`src/test/normalization_vocabulary_tests.py`.

The original cases for `CaseFoldingTransducer` and the bare `SkillNormalizer`
are in [`normalization_tests.md`](normalization_tests.md) and are unchanged.

Processing order of the default normalizer (`build_default_normalizer()`):

```
raw -> strip() -> StrippingTransducer -> CaseFoldingTransducer -> vocabulary FST -> token | None
```

Shared fixtures:

- `stripper`: a fresh `StrippingTransducer()`.
- `normalizer`: `build_default_normalizer()` (stripper + case folder + full vocabulary).
- `SURFACE_FORMS`: 96 `(raw, canonical)` pairs covering every variant the extractor can return.

## `StrippingTransducer`

Collapses each run of separators (space, `.`, `-`, `_`, `/`) into one space,
drops separators at both ends, leaves letters and digits (and their case)
untouched, and rejects any other character.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| STR-01 | Separators collapse, everything else is kept (parametrized, 13 cases) | `apply(raw)` for the pairs listed below | The expected output listed below |
| STR-02 | Case is not changed | `apply("JaVa-ScRiPt")` | `"JaVa ScRiPt"` |
| STR-03 | Character outside the alphabet | `apply(raw)` for `"C++"`, `"C#"`, `"Ñandú"`, `"a@b"`, `"R&D"` (parametrized) | Raises `ValueError` matching `"Unexpected character"` |
| STR-04 | Idempotence | `apply(apply(" .React--js/ "))` | Equals `apply(" .React--js/ ")` |

Pairs for STR-01:

| Input | Output |
|---|---|
| `React.js` | `React js` |
| `Node.js` | `Node js` |
| `scikit-learn` | `scikit learn` |
| `snake_case` | `snake case` |
| `GitLab CI/CD` | `GitLab CI CD` |
| `"  Amazon   Web  Services "` | `Amazon Web Services` |
| `..React..` | `React` |
| `a - b` | `a b` |
| `k8s` | `k8s` |
| `PowerBI` | `PowerBI` |
| `Python 3.11` | `Python 3 11` |
| `""` | `""` |
| `...` | `""` |

## `SkillNormalizer` with and without the stripper

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| NSTR-01 | Without a stripper (original two-argument signature) behaviour is unchanged | Vocabulary `{"REACT": ["REACT", "REACT JS"]}`, `SkillNormalizer(CaseFoldingTransducer(), vocab)` | `normalize("react") == "REACT"`; `normalize("React.js")` raises `ValueError` |
| NSTR-02 | With a stripper, punctuation is normalized | Same vocabulary, `SkillNormalizer(CaseFoldingTransducer(), vocab, StrippingTransducer())` | `normalize("React.js") == "REACT"` |
| NSTR-03 | Empty after cleaning | `normalizer.normalize(raw)` for `""`, `"   "`, `"..."`, `" - "` (parametrized) | `None` |
| NSTR-04 | Unknown skill with valid characters | `normalizer.normalize(raw)` for `"GitHub"`, `"Dockerfile"`, `"Java"`, `"Excellent"` (parametrized) | `None` |
| NSTR-05 | Character outside the alphabet still raises | `normalizer.normalize("C++")` | Raises `ValueError` |

## Default vocabulary

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| VOC-01 | Each surface form maps to its canonical token (parametrized, 96 cases) | `normalizer.normalize(raw)` for each pair of `SURFACE_FORMS` (table below) | The canonical token |
| VOC-02 | Every spelling is in post-cleaning form | Each spelling of `VOCABULARY` | Matches `[A-Z0-9]+( [A-Z0-9]+)*`: upper case, single spaces, no punctuation |
| VOC-03 | No spelling is shared between two tokens | `VOCABULARY` | Each spelling has exactly one owner |
| VOC-04 | Ambiguous vocabulary is rejected when the FST is built | `build_vocabulary_fst({"A": ["X"], "B": ["X"]})` | Raises `ValueError` matching `"both"` |
| VOC-05 | Vocabulary and profiles use the same tokens | `VOCABULARY` keys vs. the union of `Profile.vocabulary` over `ProfileRegistry().get_all()` | The two sets are equal (43 tokens) |

Surface forms covered by VOC-01:

| Canonical token | Surface forms |
|---|---|
| `JAVASCRIPT` | `JS`, `JavaScript`, `java script`, `ECMAScript` |
| `TYPESCRIPT` | `TypeScript`, `type-script` |
| `PYTHON` | `Python`, `Python3`, `Python 3`, `Python-3`, `Python 3.11`, `Python3.8` |
| `REACT` | `React`, `React.js`, `ReactJS`, `React js`, `React-js` |
| `ANGULAR` | `AngularJS`, `Angular.js` |
| `VUE` | `Vue.js`, `VueJS` |
| `NODE_JS` | `Node.js`, `NodeJS`, `node js`, `Node` |
| `DJANGO` | `Django` |
| `SPRING_BOOT` | `Spring Boot`, `SpringBoot`, `spring-boot` |
| `REST_API` | `REST API`, `RESTful APIs`, `REST-API`, `REST`, `RESTful` |
| `SQL` | `SQL` |
| `NOSQL` | `NoSQL`, `No-SQL` |
| `POSTGRESQL` | `PostgreSQL`, `Postgres`, `Postgre SQL` |
| `MYSQL` | `MySQL`, `My-SQL` |
| `MONGODB` | `Mongo`, `MongoDB`, `Mongo DB` |
| `ORACLE` | `Oracle`, `Oracle DB` |
| `REDIS` | `Redis` |
| `CASSANDRA` | `Cassandra`, `Casandra` |
| `PANDAS` | `Pandas` |
| `NUMPY` | `NumPy`, `Num-Py` |
| `SCIKIT_LEARN` | `sklearn`, `scikit-learn`, `Scikit Learn` |
| `TENSORFLOW` | `TensorFlow` |
| `PYTORCH` | `PyTorch` |
| `MACHINE_LEARNING` | `Machine Learning`, `machine-learning`, `ML` |
| `STATISTICS` | `Statistics`, `Statistical Analysis` |
| `AWS` | `AWS`, `Amazon Web Services` |
| `AZURE` | `Azure` |
| `GCP` | `GCP`, `Google Cloud`, `Google Cloud Platform` |
| `DOCKER` | `Docker` |
| `KUBERNETES` | `k8s`, `Kubernetes` |
| `ANSIBLE` | `Ansible` |
| `TERRAFORM` | `Terraform` |
| `CLOUDFORMATION` | `CloudFormation`, `Cloud-Formation` |
| `JENKINS` | `Jenkins` |
| `GITHUB_ACTIONS` | `GitHub Actions`, `github-actions` |
| `GITLAB` | `GitLab`, `GitLab CI`, `GitLab CI/CD`, `GitLab-CI`, `GitLabCI/CD` |
| `LINUX` | `Linux` |
| `GIT` | `Git` |
| `EXCEL` | `Excel`, `MS Excel`, `Microsoft Excel`, `ms-excel` |
| `POWER_BI` | `Power BI`, `PowerBI`, `power-bi` |
| `TABLEAU` | `Tableau` |
| `LOOKER` | `Looker` |
| `R` | `R` |

## `SkillNormalizer.normalize_skills`

Returns `NormalizedSkills(recognized, unrecognized)`; never raises on unknown
or malformed input.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| NSK-01 | Recognized tokens are deduplicated, in first-seen order | `["git", "JS", "JavaScript", "GIT", "Docker"]` | `recognized == ("GIT", "JAVASCRIPT", "DOCKER")`; `unrecognized == ()` |
| NSK-02 | Unrecognized skills are separated and deduplicated ignoring case | `["GitHub", "git", "github", "  Java  "]` | `recognized == ("GIT",)`; `unrecognized == ("GitHub", "Java")` |
| NSK-03 | Out-of-alphabet input goes to `unrecognized` instead of raising | `["C++", "Python"]` | `recognized == ("PYTHON",)`; `unrecognized == ("C++",)` |
| NSK-04 | Blank entries are ignored | `["", "   ", "..."]` | `recognized == ()`; `unrecognized == ("...",)` |
| NSK-05 | Empty input | `[]` | Both tuples are empty |

## Stage 1 → Stage 2 alignment

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| E2E-01 | Everything the extractor returns is recognized, and every vocabulary token is reachable | `ContentExtractor().extract_skills(ALL_SKILLS_TEXT)`, where the text lists one surface form per token in a *Skills* section, passed to `normalize_skills` | `unrecognized == ()` and `set(recognized) == set(VOCABULARY)` |

## Notes

- NSK-04 documents a quirk: `"..."` is kept in `unrecognized` because it is
  not blank before cleaning, while `""` and `"   "` are dropped. Only the
  `strip()` of the raw text decides whether an entry is reported.
- `PYTHON` spellings include minor versions `3.0` to `3.19` (`Python 3.11`,
  `Python3.11`). A minor version of 20 or higher (`Python 3.25`) is returned by
  the extractor but reported as unrecognized. A patch number (`Python 3.11.2`)
  never reaches the normalizer, because the extractor stops at the minor version.
- E2E-01 couples the two stages on purpose. When a pattern is added to
  `_SKILL_PATTERNS` in the extractor, its spellings must be added to
  `vocabulary.py`; this test is what notices if that is forgotten.
- Suggested alignment with the formal design: `StrippingTransducer` is a
  deterministic FST `M = (Q, Σ, Γ, δ, ω, q0, F)` with `Q = {start, word,
  pending}`, `q0 = start` and `F = Q`. Its full definition is in the class
  docstring.
- Run with `pytest src/test/normalization_vocabulary_tests.py` from the
  repository root.
