# Extraction module — Test cases

Scope: `ContentExtractor` (`src/core/extraction/content_extractor.py`), which
turns résumé plain text into a `RawProfile` using only the `re` module.
Implemented in `src/test/extraction_tests.py`.

Public methods under test: `find_section`, `extract_contact`,
`extract_education`, `extract_experience`, `extract_certifications`,
`extract_skills` and `extract`. The extractor never raises on missing data:
absent fields are `""` (strings) or `()` (tuples).

Shared fixtures:

- `extractor`: a fresh `ContentExtractor()` per test.
- `SAMPLE_CV`: a complete Markdown résumé for *Jane Doe* with a header line
  `jane.doe@example.com \| +57 300 123 4567` and the sections *Summary*,
  *Technical Skills* (`Python, JS, React.js, Node.js, PostgreSQL, sklearn, Git, R`),
  *Experience* (2 bullets), *Education* (1 line) and *Certifications* (2 bullets).

## `find_section`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| EXT-SEC-01 | Section body stops at the next known header | `SAMPLE_CV`, header `"Education"` | Returns `"B.Sc. Computer Science, Universidad del Valle, 2018"` (stops before *Certifications*) |
| EXT-SEC-02 | Header matching is case-insensitive | `SAMPLE_CV`, headers `"education"`, `"EDUCATION"`, `"Education"` (parametrized) | All three find the section; body contains `"Universidad del Valle"` |
| EXT-SEC-03 | Header decorations | `"Education:\nMIT"`, `"EDUCATION\nMIT"`, `"## Education\nMIT"`, `"**Education**\nMIT"`, `"**Education:**\nMIT"` (parametrized) | Every variant returns `"MIT"` |
| EXT-SEC-04 | Inline content after the colon | `"Skills: Python, SQL\n"`, header `"Skills"` | Returns `"Python, SQL"` |
| EXT-SEC-05 | Section not present | `"Education\nMIT"`, header `"Experience"` | Returns `""` |
| EXT-SEC-06 | Empty text, or empty header | `""` with `"Education"`; `SAMPLE_CV` with `""` | Returns `""` in both cases |
| EXT-SEC-07 | Header word used inside a sentence is not a header | `"Experience with Python\nEducation\nMIT"`, header `"Experience"` | Returns `""` (the line is not a header line) |
| EXT-SEC-08 | Windows line endings | `"Education\r\nMIT\r\n"` | Returns `"MIT"` |
| EXT-SEC-09 | Header not in the known list | `"Hobbies\nChess\nEducation\nMIT"`, header `"Hobbies"` | Returns `"Chess"`; the requested header is treated as a delimiter too |
| EXT-SEC-10 | Spanish headers | `"Educación\nUniversidad Nacional\nExperiencia\nDev"` | `extract_education` → `("Universidad Nacional",)`; `extract_experience` → `("Dev",)` |

## `extract_contact`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| EXT-CON-01 | Full contact block | `SAMPLE_CV` | `ContactInfo(name="Jane Doe", email="jane.doe@example.com", phone="+57 300 123 4567")` |
| EXT-CON-02 | Phone number formats | `"John Smith\nTel: <phone>\n"` with `+57 300 123 4567`, `(300) 123-4567`, `300-123-4567`, `+1 (415) 555-2671`, `3001234567`, `300.123.4567` (parametrized) | `phone` equals the number exactly as written |
| EXT-CON-03 | Date range is not a phone number | `"John Smith\n2018 - 2021\n"` | `phone == ""` |
| EXT-CON-04 | Labelled name | `"Name: María Pérez\n"` | `name == "María Pérez"` |
| EXT-CON-05 | Accented name | `"José Núñez\njose@x.co\n"` | `name == "José Núñez"` |
| EXT-CON-06 | Title and header lines are skipped when looking for the name | `"Resume\nSummary\nAda Lovelace\n"` | `name == "Ada Lovelace"` |
| EXT-CON-07 | No contact data | `""` | `ContactInfo(name="", email="", phone="")` |
| EXT-CON-08 | E-mail with `+`, dots and hyphenated domain | `"a+b.c@sub.dom-ain.org"` | `email == "a+b.c@sub.dom-ain.org"` |

## `extract_education`, `extract_experience`, `extract_certifications`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| EXT-ENT-01 | Education entries | `SAMPLE_CV` | `("B.Sc. Computer Science, Universidad del Valle, 2018",)` |
| EXT-ENT-02 | Experience entries, bullets removed | `SAMPLE_CV` | `("Senior Developer at ACME (2019 - 2022)", "Built REST APIs with Django and Docker on AWS")` |
| EXT-ENT-03 | Certification entries, `*` bullets removed | `SAMPLE_CV` | `("AWS Certified Cloud Practitioner", "Scrum Master")` |
| EXT-ENT-04 | Blank lines and rule lines are dropped | `"Experience\n----------\n\n- Dev\n\n"` | `("Dev",)` |
| EXT-ENT-05 | Sections missing | `"nothing here"` | `extract_experience` and `extract_certifications` both return `()` |

## `extract_skills`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| EXT-SKL-01 | Each variant is returned as the candidate wrote it | `"I know <term>"` for each term in the list below (parametrized, 26 cases) | A one-element tuple containing exactly `<term>` |
| EXT-SKL-02 | Case-insensitive, duplicates collapse | `"docker and DOCKER and Docker"` | `("docker",)` (first spelling kept) |
| EXT-SKL-03 | `SQL` is not matched inside other databases | `"PostgreSQL MySQL NoSQL"` | `("PostgreSQL", "MySQL", "NoSQL")` |
| EXT-SKL-04 | Plain `SQL` is matched | `"Strong SQL skills"` | `("SQL",)` |
| EXT-SKL-05 | `Git` is not matched inside `GitHub` / `GitLab` | `"GitHub and GitLab"`; `"Git and GitHub"` | `("GitLab",)`; `("Git",)` |
| EXT-SKL-06 | `JS` is not matched inside framework names | `"Node.js"`; `"React.js"` | `("Node.js",)`; `("React.js",)` |
| EXT-SKL-07 | `Excellent` is not `Excel` | `"Excellent communicator"` | `()` |
| EXT-SKL-08 | Single-letter `R` is trusted only inside the skills section | `"Skills\nPython, R, SQL\n"`; `"Worked on R&D and plan R"` | `("Python", "SQL", "R")`; `()` |
| EXT-SKL-09 | Order of first appearance, then de-duplication | `"Docker, Python, docker, PYTHON, Git"` | `("Docker", "Python", "Git")` |
| EXT-SKL-10 | De-duplication ignores `.`, `-` and spaces, but not distinct variants | `"React.js and ReactJS and React js"`; `"React and React.js"` | `("React.js",)`; `("React", "React.js")` |
| EXT-SKL-11 | Skills mentioned outside the skills section are found | `SAMPLE_CV` | Result contains `"Django"` (it only appears in an experience bullet) |
| EXT-SKL-12 | No skills | `""`; `"I like cooking"` | `()` in both cases |

Terms covered by EXT-SKL-01: `JS`, `JavaScript`, `java script`, `React.js`,
`ReactJS`, `Node.js`, `NodeJS`, `sklearn`, `scikit-learn`, `Scikit Learn`,
`Spring Boot`, `PostgreSQL`, `Postgres`, `Power BI`, `PowerBI`,
`Amazon Web Services`, `GitHub Actions`, `k8s`, `CloudFormation`,
`TensorFlow`, `PyTorch`, `RESTful APIs`, `MS Excel`, `TypeScript`, `Vue.js`,
`Python3`.

## `extract`

| ID | Scenario | Fixture | Expected result |
|---|---|---|---|
| EXT-FULL-01 | Full résumé | `SAMPLE_CV` | Returns a `RawProfile`: name `"Jane Doe"`, e-mail `"jane.doe@example.com"`, 2 experience entries, 2 certifications, 1 education entry; `raw_skills` contains `Python`, `JS`, `React.js`, `Node.js`, `PostgreSQL`, `sklearn`, `Git`, `R`, `Django`, `Docker`, `AWS` and does **not** contain `SQL` (it only occurs inside `PostgreSQL`) |
| EXT-FULL-02 | Empty text | `""` | `RawProfile(contact=ContactInfo("", "", ""), education=(), experience=(), certifications=(), raw_skills=())` |
| EXT-FULL-03 | Idempotence | `SAMPLE_CV` extracted twice | Both results are equal |

## Notes

- Skills are returned as **surface forms**, not canonical tokens. `React` and
  `React.js` stay distinct on purpose (EXT-SKL-10): unifying them is the job of
  the Stage 2 transducers, so this catalogue must stay aligned with the
  normalisation vocabulary.
- EXT-SKL-08 documents an ordering quirk: single-letter skills found in the
  skills section are appended **after** the rest, so `R` appears last even when
  it is written before `SQL`. Canonical ordering is applied later in the
  pipeline.
- A phone number is accepted only if it has 9 to 15 digits and is not a
  year range (EXT-CON-02, EXT-CON-03).
- All tests are pure-string tests: they use inline strings and `SAMPLE_CV`,
  with no files on disk and no `tmp_path`.
- Run with `pytest src/test/extraction_tests.py` from the repository root
  (`pytest.ini` sets `pythonpath = .` and `python_files = *_tests.py`).
