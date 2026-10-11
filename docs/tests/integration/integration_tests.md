# ResumeLens Pipeline — Test cases

Scope: `ResumeLensPipeline.process()`, exercised end to end with every real
module (`ingestion`, `extraction`, `normalization`, `projection`,
`classification`) – not mock ones. Each case is a full synthetic résumé (contact,
education, experience, skills) processed through the pipeline; the
assertion checks only the `ClassificationResult.accepted` value for the one
profile the case targets.

Two cases per profile: one that satisfies every group (`ACCEPTED`) and one
that is the positive case with a single group emptied out (`REJECTED`).
Negative cases alternate between removing a `REQUIRED` group's token and
emptying an `ANY_OF` group entirely, so both rejection mechanisms are
exercised.

## Full Stack Developer

| ID | Scenario | Skills listed | Expected result |
|---|---|---|---|
| INT-FS-01 | Accepted: at least one token present in every group | `JavaScript, React, Node.js, REST API, PostgreSQL, MongoDB, Git` | `accepted = True` |
| INT-FS-02 | Rejected: `REST API` removed, leaving the `REQUIRED` "REST APIs" group empty | `JavaScript, React, Node.js, PostgreSQL, MongoDB, Git` | `accepted = False` |

## Machine Learning Engineer

| ID | Scenario | Skills listed | Expected result |
|---|---|---|---|
| INT-ML-01 | Accepted: at least one token present in every group | `Python, Pandas, Scikit-learn, TensorFlow, Machine Learning, SQL, Git` | `accepted = True` |
| INT-ML-02 | Rejected: `Pandas` removed, leaving the `ANY_OF` "Data processing" group empty (no Pandas/Numpy) | `Python, Scikit-learn, TensorFlow, Machine Learning, SQL, Git` | `accepted = False` |

## Cloud Engineer

| ID | Scenario | Skills listed | Expected result |
|---|---|---|---|
| INT-CE-01 | Accepted: at least one token present in every group | `AWS, Docker, Terraform, Jenkins, Linux, Git` | `accepted = True` |
| INT-CE-02 | Rejected: `Linux` removed, leaving the `REQUIRED` "Operating system" group empty | `AWS, Docker, Terraform, Jenkins, Git` | `accepted = False` |

## Data Analyst

| ID | Scenario | Skills listed | Expected result |
|---|---|---|---|
| INT-DA-01 | Accepted: at least one token present in every group | `SQL, Excel, Tableau, Pandas` | `accepted = True` |
| INT-DA-02 | Rejected: `Tableau` removed, leaving the `ANY_OF` "Visualization" group empty (no Power BI/Tableau/Looker) | `SQL, Excel, Pandas` | `accepted = False` |

## Fixture (shared across all 8 cases)

Every case uses the same résumé template, varying only the `SKILLS` line:

```
Jane Doe
jane.doe@email.com | +1 555 234 5678

EDUCATION
BSc Computer Science, Tech University, 2021

EXPERIENCE
Backend Developer, Acme Corp, 2021-2024

SKILLS
<skills listed above>
```

Written to a temporary `.txt` file and passed to
`ResumeLensPipeline.process()`. The pipeline is built once (module-scoped
fixture) with `ContentExtractor`, `build_default_normalizer()`,
`ProfileProjector`, and `ProfileClassifier` — the real implementations of
every stage, no test doubles.

## Notes

- None of the four profiles use an `OPTIONAL` group in the current
  definitions, so in practice every `ANY_OF` group still needs at least one
  matching token for the automaton to reach an accepting state — omitting
  an `ANY_OF` group entirely rejects the candidate just as omitting a
  `REQUIRED` one does. INT-ML-02 and INT-DA-02 demonstrate this.
- Each case only asserts the targeted profile's result. A "reject" case
  may still be `ACCEPTED` under a different profile; that is expected and
  not checked here.
- `SQL` in Data Analyst satisfies two groups at once ("Query language"
  `REQUIRED` and "Relational database" `ANY_OF`), per
  `ProfileProjector`'s rule that a token listed in more than one group is
  placed at its first position and counted once.