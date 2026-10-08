# Normalization module — Test cases

Scope: `CaseFoldingTransducer` and `SkillNormalizer` (which composes
`CaseFoldingTransducer` with a vocabulary `FST` built by
`build_vocabulary_fst`). `SkillNormalizer.normalize(raw: str) -> str | None`
returns the canonical token, `None` if `raw` is valid but matches no known
vocabulary entry, and **raises `ValueError`** if `raw` contains a character
outside `CaseFoldingTransducer`'s alphabet (letters, digits, and space).

## Shared fixture

```python
VOCABULARY = {
    "GIT": ["GIT"],
    "DOCKER": ["DOCKER"],
    "TERRAFORM": ["TERRAFORM"],
    "JAVASCRIPT": ["JAVASCRIPT", "JS"],
    "TYPESCRIPT": ["TYPESCRIPT", "TS"],
    "KUBERNETES": ["KUBERNETES", "K8S"],
    "REACT": ["REACT", "REACTJS", "REACTTS"],
    "ANGULAR": ["ANGULAR"],
    "SPRINGBOOT": ["SPRINGBOOT"],
}

@pytest.fixture(scope="module")
def normalizer():
    return SkillNormalizer(CaseFoldingTransducer(), build_vocabulary_fst(VOCABULARY))
```

All `SkillNormalizer` test cases below use this `normalizer` fixture unless
noted otherwise.

## `SkillNormalizer` — success cases

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| NORM-01 | Lowercase input | `normalizer.normalize("git")` | `"GIT"` |
| NORM-02 | Uppercase input | `normalizer.normalize("DOCKER")` | `"DOCKER"` |
| NORM-03 | Mixed-case input | `normalizer.normalize("TerraForm")` | `"TERRAFORM"` |
| NORM-04 | Known abbreviation, parametrized over `("JS", "JAVASCRIPT")`, `("TS", "TYPESCRIPT")`, `("K8S", "KUBERNETES")` | `normalizer.normalize(raw)` | matching canonical token |
| NORM-05 | Variant with accepted suffix | `normalizer.normalize("ReactJS")` | `"REACT"` |
| NORM-06 | Leading/trailing whitespace trimmed | `normalizer.normalize("  git  ")` | `"GIT"` |

## `SkillNormalizer` — failure: valid characters, not in vocabulary

These exercise strings made only of characters in
`CaseFoldingTransducer`'s alphabet (letters, digits, space), so no exception
is raised — the string is simply unrecognized.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| NORM-07 | Near-miss spelling, parametrized over `"reactt"`, `"anguler"` | `normalizer.normalize(raw)` | `None` |
| NORM-08 | Internal space, valid characters but not a recognized combined token *(rejected by design — Backend/IaC tokens only accept the exact name, no space/dot variants)* | `normalizer.normalize("spring boot")` | `None` |
| NORM-09 | Empty string | `normalizer.normalize("")` | `None` |

## `SkillNormalizer` — failure: character outside the alphabet

These contain a character `CaseFoldingTransducer` has no transition for
(not a letter, digit, or space), so the normalizer raises instead of
returning `None`. Callers (the pipeline) are responsible for catching this.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| NORM-10 | Character outside the alphabet, parametrized over `"c#"`, `"node+"`, `"node.js"` | `normalizer.normalize(raw)` | Raises `ValueError` |


## `CaseFoldingTransducer` — isolated unit tests

Covers the shared transducer directly, independent of any vocabulary.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| CF-01 | Lowercase letters fold to uppercase | `CaseFoldingTransducer().apply("git")` | `"GIT"` |
| CF-02 | Uppercase letters pass through unchanged | `CaseFoldingTransducer().apply("GIT")` | `"GIT"` |
| CF-03 | Digits pass through unchanged | `CaseFoldingTransducer().apply("k8s")` | `"K8S"` |
| CF-04 | Space passes through unchanged | `CaseFoldingTransducer().apply("spring boot")` | `"SPRING BOOT"` |
| CF-05 | Character outside the alphabet, parametrized over `"#"`, `"+"`, `"."` | `CaseFoldingTransducer().apply(raw)` | Raises `ValueError` |

## Cross-token isolation (vocabulary union)

Confirms `build_vocabulary_fst`'s union of per-token FSTs doesn't let one
token's accepted spellings leak into another's result.

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| ISO-01 | Two unrelated tokens normalize independently | `normalizer.normalize("docker")` and `normalizer.normalize("terraform")` | `"DOCKER"` and `"TERRAFORM"` respectively, never cross-matched |
| ISO-02 | A short abbreviation doesn't accidentally match a different token's entry | `normalizer.normalize("js")` | `"JAVASCRIPT"` only (not `"TYPESCRIPT"` or any other token) |

## Notes

- `None` vs. raised `ValueError` is a deliberate distinction, not an
  oversight: `None` means "valid characters, just not a known skill" (a
  normal, expected outcome for arbitrary CV text); `ValueError` means "this
  isn't even a well-formed candidate string" (an alphabet violation). The
  pipeline catches `ValueError` where it iterates `raw_skills` and routes it
  to `unrecognized_skills`, same as a `None` result.

- NORM-08 and NORM-10 both involve a form that was intentionally left
  unsupported, but for different reasons: NORM-08's `"spring boot"` fails
  only because no vocabulary entry has that exact two-word string (a
  vocabulary gap); NORM-10's `"node.js"` fails because `.` isn't a symbol
  the normalizer can process at all (an alphabet gap). Keeping them in
  separate tables makes that distinction explicit instead of burying it in
  a single mixed "rejected" bucket.