# Finite State Transducers — Formal Design

Every transducer in this document is a Mealy-type finite state transducer,
formally defined as a 7-tuple:

$$M = (Q, \Sigma, \Gamma, \delta, \omega, q_0, F)$$

where $Q$ is the set of states, $\Sigma$ the input alphabet, $\Gamma$ the
output alphabet, $\delta: Q \times \Sigma \to Q$ the transition function,
$\omega: Q \times \Sigma \to \Gamma$ the output function, $q_0 \in Q$ the
start state, and $F \subseteq Q$ the set of final states.

## 1. Methodology

Two tiers of transducers are used, applied in sequence.

**Tier 1 — case folding (shared).** A single, generic transducer normalizes
letter case for any input string, before it reaches any token-specific
transducer. It is defined once and reused for every skill.

**Tier 2 — token transducers (one per canonical skill).** Each canonical
skill token (e.g. `REACT`, `AWS`) has its own transducer that recognizes a
fixed, finite set of accepted spellings and echoes them, letter by letter,
as that canonical token. Because Tier 1 already runs first, every Tier-2
transducer can assume its input is already uppercase — it only needs one
transition per letter, not a pair for each case.

**General construction for a token transducer.** Given a canonical token
and its set of accepted spellings $\{s_1, \dots, s_k\}$ (each already
uppercase), the transducer is built as follows: for each spelling
$s_i = c_1 c_2 \dots c_{m_i}$, create a dedicated path of $m_i$ fresh states
branching from the shared start state $q_0$:

$$q_0 \xrightarrow{c_1 : c_1} q_{i,1} \xrightarrow{c_2 : c_2} q_{i,2} \xrightarrow{\ \dots\ } q_{i,m_i}$$

with $\delta(q_{i,j-1}, c_j) = q_{i,j}$ and $\omega(q_{i,j-1}, c_j) = c_j$
(the output simply echoes the input letter). $Q$ is $\{q_0\}$ plus every
path's states; $\Sigma = \Gamma$ is the set of distinct characters appearing
across all accepted spellings; $F$ is the set of every path's last state.

Listing a token's accepted spellings therefore fully determines its 7-tuple
by this construction, so the tables below give only the canonical token and
its accepted spellings — $Q$, $\Sigma$, $\Gamma$, $\delta$, $\omega$ and $F$
follow mechanically from that.

**On state minimization.** Where two spellings of the same token share a
prefix or suffix (e.g. `REACT` and `REACTJS`), the construction above does
**not** merge their paths into a shared chain of states. This keeps every
transducer trivial to build and verify directly from its list of accepted
spellings, at the cost of not being state-minimal. The accepted language is
identical either way.

**Implementation note.** The Python implementation (`pyformlang.fst.FST`)
builds each token transducer with input symbols set to *whole accepted
spellings* rather than individual characters — i.e. a 2-state transducer
($q_0 \xrightarrow{s_i\,:\,\text{TOKEN}} q_1$ per accepted spelling) instead
of the character-level construction above. This is a deliberate
implementation simplification: it is formally still a valid FST accepting
the same language, just not reflecting the per-character structure used for
this formal design. The character-level construction in this document is
the one that should be referenced for the 7-tuple definitions and diagrams.

## 2. Tier 1 — `CaseFoldingTransducer` (shared)

Applied to every raw skill string before any token transducer runs.

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
alphabet to its canonical form. A character outside $\Sigma$ (e.g. `.`,
`#`, `+`) has no defined transition, so the transducer is undefined on it —
the implementation surfaces this as an explicit error rather than silently
ignoring the character.

## 3. Tier 2 — Full Stack Developer token transducers

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `JAVASCRIPT` | `JAVASCRIPT`, `JS` | 13 |
| `TYPESCRIPT` | `TYPESCRIPT`, `TS` | 13 |
| `REACT` | `REACT`, `REACTJS`, `REACTTS` | 20 |
| `VUE` | `VUE` | 4 |
| `ANGULAR` | `ANGULAR` | 8 |
| `NODEJS` | `NODEJS` | 7 |
| `DJANGO` | `DJANGO` | 7 |
| `SPRINGBOOT` | `SPRINGBOOT` | 11 |
| `SQL` | `SQL` | 4 |
| `NOSQL` | `NOSQL` | 6 |
| `REST_API` | `RESTAPI` | 8 |
| `GIT` | `GIT` | 4 |

$\lvert Q\rvert$ is computed as $1 + \sum_i m_i$ over the accepted
spellings' lengths, per the general construction in §1.

**Scope decisions reflected above:**
- `NODEJS`, `DJANGO`, `SPRINGBOOT` accept only their exact literal spelling
  — no separator variants (`Node.js`, `Spring Boot`) are recognized. This
  is intentional, not an omission.
- `JAVASCRIPT`/`TYPESCRIPT` additionally accept the common abbreviations
  `JS`/`TS`, and `REACT` additionally accepts the `.js`/`.ts`-style suffix
  forms `REACTJS`/`REACTTS`.

## 4. Tier 2 — Cloud Engineer token transducers

| Canonical token | Accepted spellings | $\lvert Q\rvert$ |
|---|---|---|
| `AWS` | `AWS` | 4 |
| `AZURE` | `AZURE` | 6 |
| `GCP` | `GCP` | 4 |
| `DOCKER` | `DOCKER` | 7 |
| `KUBERNETES` | `KUBERNETES`, `K8S` | 14 |
| `TERRAFORM` | `TERRAFORM` | 10 |
| `ANSIBLE` | `ANSIBLE` | 8 |
| `CLOUDFORMATION` | `CLOUDFORMATION` | 15 |
| `GITHUB_ACTIONS` | `ACTIONS` | 8 |
| `GITLAB` | `LAB` | 4 |
| `JENKINS` | `JENKINS` | 8 |
| `LINUX` | `LINUX` | 6 |

**Scope decisions reflected above:**
- `TERRAFORM`, `ANSIBLE`, `CLOUDFORMATION`, `JENKINS` accept only their
  exact literal spelling, same policy as the Backend group above.
- `KUBERNETES` additionally accepts the common abbreviation `K8S` (so
  $\Sigma$ for this transducer includes the digit `8`).
- `GITHUB_ACTIONS` and `GITLAB` are intentionally recognized through short
  fragments (`ACTIONS`, `LAB`) rather than the full product names, by
  design.

## 5. Global alphabet summary

Across every Tier-2 transducer in §3 and §4, the combined input/output
alphabet is:

$$\Sigma_{\text{tokens}} = \Gamma_{\text{tokens}} = \{A, \dots, Z\} \cup \{8\}$$

The digit `8` is the only non-letter symbol needed, and it appears
exclusively in `KUBERNETES`'s `K8S` spelling.

## 6. Known limitations

- `REST_API` currently recognizes only the unseparated form `RESTAPI`.
  Hyphenated (`REST-API`) or pluralized (`RESTAPIS`) forms are not yet
  covered.
- Tokens restricted to their exact literal spelling (`NODEJS`, `DJANGO`,
  `SPRINGBOOT`, `TERRAFORM`, `ANSIBLE`, `CLOUDFORMATION`, `JENKINS`) will
  not recognize spacing or punctuation variants of their name. This is a
  deliberate scope decision given the project's time constraints, not an
  oversight.