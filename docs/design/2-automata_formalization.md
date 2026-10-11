# Finite Automata — Formal Design

The classifier of Stage 3 decides, for each profile, whether a candidate
satisfies the qualification pattern of that profile. Each profile gets a
deterministic finite automaton (DFA), formally a 5-tuple:

$$M = (Q, \Sigma, \delta, q_0, F)$$

where $Q$ is the set of states, $\Sigma$ the input alphabet, $\delta: Q \times
\Sigma \rightharpoonup Q$ the (partial) transition function, $q_0 \in Q$ the
start state and $F \subseteq Q$ the set of accepting states. The implementation
uses `pyformlang.finite_automaton.DeterministicFiniteAutomaton`.

## 1. Input: the projected word

The automaton does not read the candidate's skills in the order they were
written. The projection step (`ProfileProjector`) turns them into a **word**
over the profile's tokens: only tokens of the profile, each at most once, sorted
by their position in the profile. Let $\text{rank}(t)$ be the 1-based position
of token $t$ in the flattened vocabulary of the profile (group order first, then
token order inside each group). A projected word is a word whose letters have
**strictly increasing rank**.

Because the order is canonical, the condition "the candidate has the required
qualifications" becomes a property of a *sequence of groups* and can be checked
by a deterministic machine that only moves forward. No nondeterminism or
$\varepsilon$-transitions are needed, so a DFA is enough.

## 2. Group rules

A profile is a sequence of groups $G_0, \dots, G_{n-1}$. Group $G_g$ has a rule
$r_g$ and a list of tokens $(t_{g,1}, \dots, t_{g,k_g})$.

| Rule | A word satisfies the group when |
|---|---|
| `REQUIRED` | every token of the group appears |
| `ANY_OF` | at least one token of the group appears |
| `OPTIONAL` | always (the group imposes no condition) |

A word is accepted when it is a projected word and satisfies **every** group.
Hence

$$L(M) = \{\, w \in \Sigma^{*} \;:\; w \text{ has strictly increasing rank and } w \text{ satisfies } G_g \text{ for every } g \,\}.$$

A token must belong to at most one group of a profile; building the automaton
fails with `ValueError` otherwise.

## 3. Construction

Let $\text{sat}(g, p)$ say that group $g$ is satisfied once its tokens up to
position $p$ have been read:

$$\text{sat}(g,p) = \begin{cases} p = k_g & r_g = \text{REQUIRED} \\ p \ge 1 & r_g = \text{ANY\_OF} \\ \text{true} & r_g = \text{OPTIONAL} \end{cases}$$

and let $\text{skip}(a, b)$ say that every group strictly between $a$ and $b$ is
`OPTIONAL`.

- $Q = \{q_{0,0}\} \cup \{\, q_{g,p} : 0 \le g < n,\ 1 \le p \le k_g \,\}$. The state
  $q_{g,p}$ means "the last token read is token $p$ of group $g$"; $q_{0,0}$
  means "nothing read yet".
- $\Sigma$ is the vocabulary of the profile.
- $q_0 = q_{0,0}$.
- $F = \{\, q_{g,p} \in Q : \text{sat}(g,p) \ \wedge\ \text{skip}(g, n) \,\}$: the
  current group is satisfied and every later group is `OPTIONAL`.
- For a state $q_{g,p}$ and a token $t = t_{h,q}$:

$$\delta(q_{g,p}, t) = \begin{cases}
q_{g,q} & h = g,\ q > p,\ \text{and } q = p+1 \text{ if } r_g = \text{REQUIRED} \\
q_{h,q} & h > g,\ \text{sat}(g,p),\ \text{skip}(g,h),\ \text{and } q = 1 \text{ if } r_h = \text{REQUIRED} \\
\text{undefined} & \text{otherwise}
\end{cases}$$

The first case stays inside the group and moves forward. In a `REQUIRED` group
the next token must be the very next one, because a skipped token could never
be read later (the order only goes forward). The second case leaves the group:
it is allowed only if the group is satisfied and every group in between can be
skipped, and it enters a `REQUIRED` group at its first token.

The automaton is **partial**: a missing transition means rejection. Adding a
trap state would make it complete without changing the language. The number of
states is $1 + \lvert\Sigma\rvert$, and acceptance of a word $w$ takes
$O(\lvert w\rvert)$ steps.

**Why it is correct.** After reading a prefix, the state records the group and
position of the last token. Because ranks only grow, nothing before that token
can still change, so the state is enough to know which groups are already
satisfied (all those before $g$ were checked when leaving them, and $g$ itself
by $\text{sat}$) and which tokens may still come. The test suite checks this
claim directly: the DFA is compared with a direct reading of the group rules on
every subset of the vocabulary (a seeded sample for Full Stack Developer).

## 4. Worked example

Profile with three groups: $G_0$ = `ANY_OF` $\{A, B\}$, $G_1$ = `REQUIRED`
$\{C\}$, $G_2$ = `OPTIONAL` $\{D\}$. Its alphabet is $\{A, B, C, D\}$ and its
states are $q_{0,0}$ (start), $q_{0,1}$ ($A$), $q_{0,2}$ ($B$), $q_{1,1}$ ($C$)
and $q_{2,1}$ ($D$). Accepting states: $q_{1,1}$ and $q_{2,1}$ (reading $C$
satisfies $G_1$ and $G_2$ is optional).

| State | $A$ | $B$ | $C$ | $D$ |
|---|---|---|---|---|
| $q_{0,0}$ (start) | $q_{0,1}$ | $q_{0,2}$ | — | — |
| $q_{0,1}$ | — | $q_{0,2}$ | $q_{1,1}$ | — |
| $q_{0,2}$ | — | — | $q_{1,1}$ | — |
| $q_{1,1}$ (final) | — | — | — | $q_{2,1}$ |
| $q_{2,1}$ (final) | — | — | — | — |

Accepted: `A C`, `B C`, `A B C D`, `B C D`. Rejected: `C` (no token of $G_0$),
`A` (no $C$), `C A` (not in canonical order), `A A C` (repeated token).

## 5. The four profiles

| Profile | Groups | $\lvert\Sigma\rvert$ | $\lvert Q\rvert$ | Accepting states | Transitions |
|---|---|---|---|---|---|
| Full Stack Developer | 7 | 18 | 19 | 1 | 63 |
| Machine Learning Engineer | 7 | 12 | 13 | 1 | 25 |
| Cloud Engineer | 6 | 13 | 14 | 1 | 38 |
| Data Analyst | 4 | 12 | 13 | 2 | 44 |

Full Stack Developer has a `REQUIRED` group for REST APIs and for Git, and five
`ANY_OF` groups, two of them for databases: a candidate needs at least one
relational **and** one non-relational database. Data Analyst has only `ANY_OF`
groups, so any relational database (`SQL` included) satisfies its database
requirement.

## 6. Known limitations

- The automaton accepts only projected words. The same set of tokens in another
  order, with a repeat, or with a token of another profile is rejected. The
  classifier relies on the projection step for that.
- A token cannot appear in two groups of the same profile.
- `REQUIRED` with several tokens means *all* of them. The default profiles use
  it only with single-token groups.
- The classification is binary (`ACCEPTED` / `REJECTED`). It does not say which
  group was missing.
