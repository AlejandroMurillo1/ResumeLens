# Classification module — Test cases

Scope: `Automaton` and `build_dfa` (`src/core/classification/automaton.py`) and
`ProfileClassifier` (`src/core/classification/profile_classifier.py`). The
automaton of a profile accepts the projected words that satisfy every group of
the profile; the classifier builds and caches one automaton per profile and
returns `ClassificationResult(profile_name, accepted, sequence)`. The formal
construction is in `docs/design/2-automata_formalization.md`. Implemented in
`src/test/classification_tests.py`.

Group rules (`GroupRule`):

- `REQUIRED`: every token of the group appears.
- `ANY_OF`: at least one token of the group appears.
- `OPTIONAL`: no condition.

Conventions used below: a profile is written as a list of groups, e.g.
`[ANY_OF (A, B), REQUIRED (C)]`. Words are lists of tokens. "Accepted" means
`Automaton(profile).accepts(word)` is `True`.

Shared fixtures:

- `classifier`: a fresh `ProfileClassifier()`.
- `registry`: a fresh `ProfileRegistry()` with the four default profiles.
- `projector`: a fresh `ProfileProjector()`.
- `OK_CANDIDATES`: one complete candidate per default profile:
  - Full Stack Developer: `JAVASCRIPT, REACT, NODE_JS, REST_API, POSTGRESQL, MONGODB, GIT`
  - Machine Learning Engineer: `PYTHON, PANDAS, SCIKIT_LEARN, TENSORFLOW, MACHINE_LEARNING, SQL, GIT`
  - Cloud Engineer: `AWS, DOCKER, TERRAFORM, JENKINS, LINUX, GIT`
  - Data Analyst: `SQL, EXCEL, TABLEAU, PANDAS`

## Group semantics (custom profiles)

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CLS-01 | Single required token | `[REQUIRED (A)]` | `A` accepted; `[]` rejected |
| CLS-02 | A required group needs every token | `[REQUIRED (A, B)]` | `A B` accepted; `A` and `B` rejected |
| CLS-03 | `ANY_OF` needs at least one token | `[ANY_OF (A, B, C)]` | `B`, `A C` and `A B C` accepted; `[]` rejected |
| CLS-04 | `OPTIONAL` never blocks | `[OPTIONAL (A, B)]` | `[]`, `B` and `A B` accepted |
| CLS-05 | Required group followed by an optional one | `[REQUIRED (A), OPTIONAL (B)]` | `A` and `A B` accepted; `B` rejected |
| CLS-06 | An optional group in the middle can be skipped | `[REQUIRED (A), OPTIONAL (B), REQUIRED (C)]` | `A C` and `A B C` accepted; `A B` rejected |
| CLS-07 | A leading optional group can be skipped | `[OPTIONAL (A), REQUIRED (B)]` | `B` and `A B` accepted; `A` rejected |
| CLS-08 | Every group must be satisfied | `[ANY_OF (A, B), ANY_OF (C, D)]` | `A D` accepted; `A B` and `C D` rejected |
| CLS-09 | A profile without groups | `Profile("empty", ())` | `[]` accepted; `A` rejected |

## Canonical words only

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CLS-10 | Order must follow the groups | `[ANY_OF (A, B), REQUIRED (C)]` | `A C` accepted; `C A` rejected |
| CLS-11 | Order inside a group must follow the profile | `[ANY_OF (A, B)]` | `A B` accepted; `B A` rejected |
| CLS-12 | A repeated token is rejected | `[ANY_OF (A, B)]`, `A A` | Rejected |
| CLS-13 | A token outside the alphabet is rejected | `[REQUIRED (A)]`, `A ZZZ` and `a` | Both rejected (matching is exact and case-sensitive) |

## Invalid profiles

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CLS-14 | A token listed in two groups | `[REQUIRED (A), ANY_OF (A, B)]` | `Automaton(...)` raises `ValueError` matching `"more than one group"` |
| CLS-15 | A group without tokens | `[ANY_OF ()]` | `Automaton(...)` raises `ValueError` matching `"no tokens"` |

## The four default profiles

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CLS-16 | A complete candidate is accepted (parametrized, 4 profiles) | `OK_CANDIDATES[profile]` projected onto its profile | Accepted |
| CLS-17 | Removing every token of any non-optional group rejects the candidate (parametrized, 4 profiles) | For each `REQUIRED` or `ANY_OF` group of the profile: `OK_CANDIDATES[profile]` without that group's tokens, projected | Rejected, for every group |
| CLS-18 | The empty candidate is rejected by every profile | `[]` against each of the four profiles | Rejected |
| CLS-19 | Data Analyst does not need the `SQL` token | `POSTGRESQL, EXCEL, LOOKER, STATISTICS` projected onto Data Analyst | Accepted |
| CLS-20 | Data Analyst needs a relational database | `EXCEL, LOOKER, PANDAS` projected onto Data Analyst | Rejected |
| CLS-21 | Full Stack needs both a relational and a non-relational database | The Full Stack candidate without `MONGODB`, projected | Rejected |
| CLS-22 | The automaton agrees with the rules read directly (parametrized, 4 profiles) | Every subset of the vocabulary for Machine Learning Engineer, Cloud Engineer and Data Analyst (at most 13 tokens); 3000 seeded random subsets for Full Stack Developer (18 tokens). Each subset is projected and compared with an independent check that reads the group rules on the set of tokens | For every subset: accepted by the automaton if and only if the rules are satisfied |
| CLS-23 | State count (parametrized, 4 profiles) | `get_automaton(profile).num_states` | `1 + len(profile.vocabulary)` |

## `ProfileClassifier`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CLS-24 | Automata are cached per profile | `get_automaton` called twice for Cloud Engineer, then once for Data Analyst | Same object for the same profile; a different object for another profile |
| CLS-25 | The automaton exposes its profile name and alphabet | `get_automaton(Cloud Engineer)` | `profile_name == "Cloud Engineer"`; `alphabet == frozenset(profile.vocabulary)` |
| CLS-26 | `classify` keeps the evaluated sequence | Cloud Engineer, `OK_CANDIDATES` projected | `ClassificationResult("Cloud Engineer", True, word)` |
| CLS-27 | `classify` on a rejected word | Cloud Engineer, `["GIT"]` | `ClassificationResult("Cloud Engineer", False, ("GIT",))` |
| CLS-28 | The stored sequence is a tuple | Cloud Engineer, `["GIT"]` given as a list | `result.sequence` is a `tuple` |
| CLS-29 | `accepts` takes any iterable | Cloud Engineer, the complete candidate as a tuple and as an iterator | Accepted in both cases |

## Stages 1 → 2 → projection → 3

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CLS-30 | One résumé against the four profiles | `"Skills\nJS, React.js, Node.js, REST APIs, PostgreSQL, MongoDB, Git\n"` → extraction → normalization → projection → `classify` for each profile | Full Stack Developer accepted; Machine Learning Engineer, Cloud Engineer and Data Analyst rejected |

## Notes

- CLS-22 is the main correctness check of the construction. The reference it
  compares against is deliberately independent of the automaton (a few lines
  that read the rules on a set of tokens), so a bug in the DFA construction
  cannot cancel itself out.
- The automaton accepts only projected words (CLS-10 to CLS-13). The classifier
  relies on `ProfileProjector` to filter, deduplicate and sort the candidate's
  tokens first.
- CLS-21 reflects the current definition of Full Stack Developer, which has two
  separate `ANY_OF` database groups: a candidate needs one relational and one
  non-relational database. If the profile is changed to a single database group,
  this case and `CLS-16` must be updated.
- `build_dfa` and `Automaton` depend on `pyformlang`. Run with
  `pytest src/test/classification_tests.py` from the repository root.
