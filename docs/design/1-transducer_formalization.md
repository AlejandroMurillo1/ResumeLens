*# Finite State Transducers — Formal Design

Every transducer in this document is a Mealy-type finite state transducer,
formally defined as a 7-tuple:

$$M = (Q, \Sigma, \Gamma, \delta, \omega, q_0, F)$$

where $Q$ is the set of states, $\Sigma$ the input alphabet, $\Gamma$ the
output alphabet, $\delta: Q \times \Sigma \to Q$ the transition function,
$\omega: Q \times \Sigma \to \Gamma$ the output function, $q_0 \in Q$ the
start state, and $F \subseteq Q$ the set of final states. The only exception
is the stripping transducer of §2, whose output function is generalized to
$\omega: Q \times \Sigma \to \Gamma^{*}$ (see there).

## 1. Methodology

Three tiers of transducers are used, applied in sequence:

$$\text{raw} \;\xrightarrow{\text{trim}}\; \xrightarrow{\ \text{Tier 0: stripping}\ } \xrightarrow{\ \text{Tier 1: case folding}\ } \xrightarrow{\ \text{Tier 2: token}\ } \text{canonical token}$$

`trim` is Python's `str.strip()`: it removes surrounding whitespace of any
kind (including tabs and line breaks, which are outside the alphabet of
Tier 0) before the first transducer runs.

**Tier 0 — stripping (shared).** A generic transducer that collapses every
run of separator characters (`space . - _ /`) into a single space and drops
separators at both ends. It makes spelling variants such as `React.js`,
`React-js` and `React js` reach the later tiers as the same string.

**Tier 1 — case folding (shared).** A generic transducer that normalizes
letter case for any input string, before it reaches any token-specific
transducer. It is defined once and reused for every skill.

**Tier 2 — token transducers (one per canonical skill).** Each canonical
skill token (e.g. `REACT`, `AWS`) has its own transducer that recognizes a
fixed, finite set of accepted spellings and echoes them, character by
character, as that canonical token. Because Tiers 0 and 1 already ran, every
Tier-2 transducer can assume its input is uppercase and that separators are
single interior spaces. Spellings are therefore written in that form:
`scikit-learn` is the spelling `SCIKIT LEARN`, and `React.js` is `REACT JS`.

**General construction for a token transducer.** Given a canonical token
and its set of accepted spellings $\{s_1, \dots, s_k\}$ (each already in the
form above), the transducer is built as follows: for each spelling
$s_i = c_1 c_2 \dots c_{m_i}$, create a dedicated path of $m_i$ fresh states
branching from the shared start state $q_0$:

$$q_0 \xrightarrow{c_1 : c_1} q_{i,1} \xrightarrow{c_2 : c_2} q_{i,2} \xrightarrow{\ \dots\ } q_{i,m_i}$$

with $\delta(q_{i,j-1}, c_j) = q_{i,j}$ and $\omega(q_{i,j-1}, c_j) = c_j$
(the output simply echoes the input character). $Q$ is $\{q_0\}$ plus every
path's states; $\Sigma = \Gamma$ is the set of distinct characters appearing
across all accepted spellings; $F$ is the set of every path's last state.

Listing a token's accepted spellings therefore fully determines its 7-tuple
by this construction, so the tables in §4 give only the canonical token and
its accepted spellings — $Q$, $\Sigma$, $\Gamma$, $\delta$, $\omega$ and $F$
follow mechanically from that.

**The union must be a function.** The vocabulary is the union of all token
transducers. For that union to map each input to at most one canonical
token, no spelling may be accepted by two different token transducers.
`build_vocabulary_fst` checks this when the vocabulary is built and raises
`ValueError` otherwise.

**On state minimization.** Where two spellings of the same token share a
prefix or suffix (e.g. `REACT` and `REACTJS`), the construction above does
**not** merge their paths into a shared chain of states. This keeps every
transducer trivial to build and verify directly from its list of accepted
spellings, at the cost of not being state-minimal. The accepted language is
identical either way.

**Implementation note.** The Python implementation (`pyformlang.fst.FST`)
builds Tiers 0 and 1 at character level, as defined below. Each token
transducer, however, is built with input symbols set to *whole accepted
spellings* rather than individual characters — i.e. a 2-state transducer
($q_0 \xrightarrow{s_i\,:\,\text{TOKEN}} q_1$ per accepted spelling) instead
of the character-level construction above. This is a deliberate
implementation simplification: it is formally still a valid FST accepting
the same language, just not reflecting the per-character structure used for
this formal design. The character-level construction in this document is
the one that should be referenced for the 7-tuple definitions and diagrams.

## 2. Tier 0 — `StrippingTransducer` (shared)

Applied to every raw skill string, after `trim` and before case folding.

- $Q = \{q_s, q_w, q_p\}$ — *start* (nothing emitted yet), *word* (last
  emitted character is not a space) and *pending* (a separator run follows a
  word and its space has not been emitted yet)
- $\Sigma = L \cup D \cup S$, where $L$ is the uppercase and lowercase Latin
  letters, $D$ the digits `0`–`9` and $S = \{\text{space}, \texttt{.},
  \texttt{-}, \texttt{\_}, \texttt{/}\}$ the separators
- $\Gamma = L \cup D \cup \{\text{space}\}$
- $q_0 = q_s$
- $F = Q$

**Output function.** This transducer must emit nothing for some inputs and
two symbols for another, so $\omega$ maps into strings,
$\omega: Q \times \Sigma \to \Gamma^{*}$ (with $\varepsilon$ the empty
string), which makes it a generalized sequential machine rather than a strict
Mealy machine. The rest of the 7-tuple is as defined above.

| State | Input | $\delta$ (next state) | $\omega$ (output) |
|---|---|---|---|
| $q_s$ | $s \in S$ | $q_s$ | $\varepsilon$ |
| $q_s$ | $c \in L \cup D$ | $q_w$ | $c$ |
| $q_w$ | $s \in S$ | $q_p$ | $\varepsilon$ |
| $q_w$ | $c \in L \cup D$ | $q_w$ | $c$ |
| $q_p$ | $s \in S$ | $q_p$ | $\varepsilon$ |
| $q_p$ | $c \in L \cup D$ | $q_w$ | space, then $c$ |

The space is emitted lazily, on the transition from $q_p$ back to $q_w$.
That is what removes separators at the end of the text without a second
pass: a trailing run leaves the machine in $q_p$, where nothing is pending to
print.

**Example trace** for `React.js`:

| Read | R | e | a | c | t | `.` | j | s |
|---|---|---|---|---|---|---|---|---|
| State after | $q_w$ | $q_w$ | $q_w$ | $q_w$ | $q_w$ | $q_p$ | $q_w$ | $q_w$ |
| Output | `R` | `e` | `a` | `c` | `t` | $\varepsilon$ | ` j` | `s` |

Result: `React js`.

**Properties.**
- Deterministic and total on $\Sigma$; since $F = Q$ it never rejects a
  string over $\Sigma$.
- The output has no leading or trailing space and never two consecutive
  spaces.
- Idempotent: applying it to its own output changes nothing.
- It does not change letter case; that is Tier 1's job.
- A character outside $\Sigma$ (e.g. `+`, `#`, `@`, `&`, accented letters)
  has no transition, so the machine is undefined on it. The implementation
  surfaces this as an explicit `ValueError`, same as Tier 1.

## 3. Tier 1 — `CaseFoldingTransducer` (shared)

Applied to every raw skill string after Tier 0 and before any token
transducer runs.

- $Q = \{q_0\}$
- $\Sigma$ = uppercase and lowercase Latin letters, digits `0`–`9`, and the
  space character
- $\Gamma$ = uppercase Latin letters, digits `0`–`9`, and the space
  character
- $\delta(q_0, c) = q_0$ for every $c \in \Sigma$ (single state, total
  function)
- $\omega(q_0, c) = \text{upper}(c)$ for letters; $\omega(q_0, c) = c$ for
  digits and space (passed through unchanged)
- $q_0 = q_0$
- $F = \{q_0\}$

This transducer never rejects a string; it only maps every character in its
alphabet to its canonical form. A character outside $\Sigma$ (e.g. `#`,
`+`) has no defined transition, so the transducer is undefined on it — the
implementati*on surfaces this as an explicit error rather than silently
ignoring the character. Separators such as `.` never reach this tier in the
default pipeline, because Tier 0 already turned them into spaces; they do
reach it when the normalizer is built without a stripper.

## 4. Tier 2 — token transducers

One transducer per canonical token, 43 in total: exactly the tokens used by
the four profiles (Full Stack Developer, Machine Learning Engineer, Cloud
Engineer and Data Analyst). The 136 accepted spellings cover every variant
that the extraction stage (`ContentExtractor.extract_skills`) can return.

$\lvert Q\rvert$ is computed as $1 + \sum_i m_i$ over the accepted
spellings' lengths, per the general construction in §1.

### Languages

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `JAVASCRIPT` | `JAVASCRIPT`, `JAVA SCRIPT`, `JS`, `ECMASCRIPT` | 34 |
| `TYPESCRIPT` | `TYPESCRIPT`, `TYPE SCRIPT` | 22 |
| `PYTHON` | `PYTHON`, `PYTHON3`, `PYTHON 3`, and `PYTHON 3 N`, `PYTHON3 N` for every minor version $N \in \{0, \dots, 19\}$ | 422 |

### Front end

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `REACT` | `REACT`, `REACTJS`, `REACT JS` | 21 |
| `ANGULAR` | `ANGULAR`, `ANGULARJS`, `ANGULAR JS` | 27 |
| `VUE` | `VUE`, `VUEJS`, `VUE JS` | 15 |

### Back end

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `NODE_JS` | `NODE`, `NODEJS`, `NODE JS` | 18 |
| `DJANGO` | `DJANGO` | 7 |
| `SPRING_BOOT` | `SPRINGBOOT`, `SPRING BOOT` | 22 |
| `REST_API` | `REST`, `RESTFUL`, `RESTAPI`, `RESTAPIS`, `REST API`, `REST APIS`, `RESTFULAPI`, `RESTFULAPIS`, `RESTFUL API`, `RESTFUL APIS` | 88 |

### Databases

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `SQL` | `SQL` | 4 |
| `NOSQL` | `NOSQL`, `NO SQL` | 12 |
| `POSTGRESQL` | `POSTGRES`, `POSTGRESQL`, `POSTGRE SQL` | 30 |
| `MYSQL` | `MYSQL`, `MY SQL` | 12 |
| `MONGODB` | `MONGO`, `MONGODB`, `MONGO DB` | 21 |
| `ORACLE` | `ORACLE`, `ORACLEDB`, `ORACLE DB` | 24 |
| `REDIS` | `REDIS` | 6 |
| `CASSANDRA` | `CASSANDRA`, `CASANDRA` | 18 |

### Data and machine learning

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `PANDAS` | `PANDAS` | 7 |
| `NUMPY` | `NUMPY`, `NUM PY` | 12 |
| `SCIKIT_LEARN` | `SCIKITLEARN`, `SCIKIT LEARN`, `SKLEARN` | 31 |
| `TENSORFLOW` | `TENSORFLOW`, `TENSOR FLOW` | 22 |
| `PYTORCH` | `PYTORCH`, `PY TORCH` | 16 |
| `MACHINE_LEARNING` | `MACHINE LEARNING`, `ML` | 19 |
| `STATISTICS` | `STATISTICS`, `STATISTICAL ANALYSIS` | 31 |

### Cloud and DevOps

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `AWS` | `AWS`, `AMAZON WEB SERVICES` | 23 |
| `AZURE` | `AZURE` | 6 |
| `GCP` | `GCP`, `GOOGLE CLOUD`, `GOOGLE CLOUD PLATFORM` | 37 |
| `DOCKER` | `DOCKER` | 7 |
| `KUBERNETES` | `KUBERNETES`, `K8S` | 14 |
| `ANSIBLE` | `ANSIBLE` | 8 |
| `TERRAFORM` | `TERRAFORM` | 10 |
| `CLOUDFORMATION` | `CLOUDFORMATION`, `CLOUD FORMATION` | 30 |
| `JENKINS` | `JENKINS` | 8 |
| `GITHUB_ACTIONS` | `GITHUBACTIONS`, `GITHUB ACTIONS` | 28 |
| `GITLAB` | `GITLAB`, `GITLAB CI`, `GITLABCI`, `GITLAB CI CD`, `GITLABCI CD` | 47 |
| `LINUX` | `LINUX` | 6 |
| `GIT` | `GIT` | 4 |

### BI and analysis tools

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `EXCEL` | `EXCEL`, `MS EXCEL`, `MICROSOFT EXCEL` | 29 |
| `POWER_BI` | `POWERBI`, `POWER BI` | 16 |
| `TABLEAU` | `TABLEAU` | 8 |
| `LOOKER` | `LOOKER` | 7 |
| `R` | `R` | 2 |

**Scope decisions reflected above:**
- Separator variants are accepted wherever the extractor can return them:
  `React.js`, `Node.js`, `scikit-learn`, `Spring Boot` and `GitLab CI/CD`
  all reach Tier 2 as spellings with single spaces or none.
- Abbreviations are accepted when they are common in résumés: `JS`, `K8S`,
  `ML`, `SKLEARN`.
- Spelling errors that the extractor deliberately accepts are listed
  (`CASANDRA`).
- Bare `NODE`, `REST` and `RESTFUL` are valid spellings; deciding when such a
  word is really the skill is left to the extractor, which only returns them
  in exact case.
- `PYTHON` accepts minor versions up to 3.19.

## 5. Global alphabet summary

Across every Tier-2 transducer in §4, the combined input/output alphabet is:

$$\Sigma_{\text{tokens}} = \Gamma_{\text{tokens}} = \{A, \dots, Z\} \cup \{0, \dots, 9\} \cup \{\text{space}\}$$

All 26 letters occur. Digits appear in `K8S` and in the `PYTHON` version
spellings. The space appears in the multi-word spellings (`AMAZON WEB
SERVICES`, `REACT JS`, ...). This is exactly the set of characters that the
output of Tiers 0 and 1 can contain, so every string those tiers produce is a
candidate input for Tier 2.

## 6. Known limitations

- Tier 0 treats `.`, `-`, `_`, `/` and space as the same separator, so
  `Node.js`, `Node-js` and `Node js` cannot be told apart. This is intended.
- Characters outside the alphabets of Tiers 0 and 1 (`+`, `#`, `&`, `@`,
  non-ASCII letters) make those transducers undefined. `C++` and `C#` are
  therefore reported as unrecognized, never normalized.
- `PYTHON` recognizes minor versions only up to 3.19.
- Ambiguous words (`ORACLE`, `REACT`, `PANDAS`) and the single letter `R` are
  valid spellings here. Telling the skill from the ordinary word is the job of
  the extraction stage, not of the transducers.
- The transducers are not state-minimal (see §1).
