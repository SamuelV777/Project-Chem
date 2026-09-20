# grading_guide.md — task-01

> **Author/grader-facing. Contains the answer. Never shown to the solver.**
> Grading here is derived from `STATE.md` / `golden/expected.json` — the answer locked at
> Step 1 — and **not** from anything in `problem.md`. If a future edit to the prompt ever
> disagrees with this file, this file wins and the prompt is the thing that gets fixed.

## 1. The answer being graded against

```
f(x) = (a*x^2 + b*x + c) mod m
m = 837296441503   (prime)
a = 1654397203
b = 402115669
c = 91027433
```

## 2. Submission format and policy

The solver submits four integers:

```json
{"m": <int>, "a": <int>, "b": <int>, "c": <int>}
```

**Policy: exact match on all four fields. No partial credit. No tolerance.**

- All four correct -> **PASS**. Anything else -> **FAIL**.
- Three-of-four is a FAIL and scores identically to a blank submission.
- The score is binary. There is no rubric, no weighting, and nothing to argue about.

### Normalisation the grader applies before comparing

| Accepted | Rejected |
|---|---|
| key order in any order | missing any of the four keys |
| surrounding whitespace, trailing newline | extra keys that contradict (e.g. a second `m`) |
| integer given as a decimal string (`"837296441503"`) | float / scientific notation that is not exactly integral (`8.37296441503e11` is only accepted if it converts to the exact integer with no loss) |
| value wrapped in prose, if a single unambiguous JSON object is extractable | two different candidate answers offered ("either X or Y") — that is a FAIL, not a choice for the grader to make |

**The grader never picks between alternatives.** A hedged submission is a failed submission.
Recovering the rule means committing to it.

### What is *not* graded

The query transcript, the method, the number of units spent, and the explanation are **not
graded**. A solver who stumbles onto all four values by a route the author did not anticipate
still passes. Conversely, a flawless write-up with one wrong integer still fails. The task is
scored on the recovered rule, full stop.

One consequence worth stating plainly: **do not grade by re-checking the submission against the
solver's own probes.** Every near-miss in section 3 is consistent with the evidence its author
collected — that is precisely what makes them near-misses. Compare against
`golden/expected.json`, never against the transcript.

## 3. Near-miss table

Every row below is a **FAIL**. The rows are ordered roughly by how likely a real solver is to
land there. Values are exact, computed from the locked answer.

### 3a. The modulus — where nearly all failures live

| # | Submitted `m` | `a,b,c` | How a solver gets here | Precise reason it is wrong |
|---|---|---|---|---|
| NM-1 | omitted / `null` / `"unknown"` / `"not observable"` | correct | Probed only low inputs, saw a perfect integer quadratic with third difference `0`, concluded the reduction never fires and there is nothing to report. | The modulus is a required field. It is not unobservable — it is unobservable *in the region they chose to look at*. This is the intended trap and is expected to be the single most common failure. |
| NM-2 | `43461535867` | correct | "No wrapping seen, so `m` must exceed everything I observed; the smallest prime above my largest output is the minimal consistent choice." Largest output from a `0..5` sweep is `43461535853`. | Consistent with their six observations and with *nothing else*. A single probe at `x >= 23` refutes it: outputs there exceed it, and it does not divide any third difference. Minimality is not evidence. |
| NM-3 | `1674592883006` (`2m`) | correct | Took `gcd(P(x1)-f(x1), P(x2)-f(x2))` over two large probes and reported it raw. Measured: the gcd lands on `m*d`, `d > 1`, in 160/400 random large pairs. | It is a *multiple* of the modulus, not the modulus. It is also composite, which violates the stated prime constraint — the constraint exists precisely so this is detectable without more probes. Strip the small cofactor. |
| NM-3' | `2511889324509` (`3m`), `3349185766012` (`4m`), `4186482207515` (`5m`), `5023778649018` (`6m`), `5861075090521` (`7m`) | correct | Same as NM-3 with a different probe pair. | Same as NM-3. Any `d*m` for small `d` is a FAIL; the table lists the observed ones so the grader recognises the family on sight. |
| NM-4 | `837296441519` | correct | Recovered `m` correctly, then "rounded to the nearest prime" or re-derived it sloppily. This is the next prime above the true modulus. | Off by 16. Exact match; no tolerance. The true modulus is already prime — nothing needed rounding. |
| NM-5 | `1099511627776` (`2^40`) | any | Guessed a round modulus on the theory that these systems use power-of-two moduli. | Composite, so it violates the stated prime constraint, and it divides no third difference. A guess, not a recovery. |
| NM-6 | `837296441502` or `837296441504` | correct | Off-by-one in a search around a correctly-computed candidate. | Both composite; neither reproduces the outputs. |
| NM-7 | a modulus derived from `sample()` readings | plausible-looking | Found the undocumented surface, spent units on noisy readings, and fitted to them. | `sample()` is noisy by construction (Step 4). Fitting an exact congruence to perturbed readings yields a modulus that divides nothing. It also burns budget that the real route needs. |

### 3b. The coefficients — subtler, and they pass their own sanity checks

| # | Submitted `a,b,c` | `m` | How a solver gets here | Precise reason it is wrong |
|---|---|---|---|---|
| NM-8 | `a=1654397203`, `b=402115669`, `c=-837205414070` | correct | Fitted the integer quadratic through a window that *had* wrapped — e.g. `x = 23..26` — and never reduced. Dangerously, that window's third difference is **`0`**, so the fit looks clean and self-consistent. | `c` is negative, so it is outside the declared `[1, m)` box. The fit is the true polynomial shifted by a multiple of the modulus. Reducing each coefficient mod `m` recovers the truth exactly — the solver stopped one step early. |
| NM-9 | `a=1654397203`, `b=-3348783650343`, `c=1694688088629505` | correct | Same error, larger window (`x = 1000..1003`). Third difference is again `0`, so again it looks clean. | `b` negative and `c` far above `m`: both outside the box. Measured: a random 4-wide consecutive window looks clean (`D3 = 0`) in **1259/4000** trials, and in **1259/1259** of those the unreduced coefficients are wrong. "The fit was clean" is not evidence of correctness. |
| NM-10 | `a=1654397203`, `b=3710910075`, `c=2147540305` | correct | Probed `x = 1,2,3,4` but indexed the finite differences as if the window began at `x = 0`. | Reports `P(x+1)`, not `P(x)`: `b' = 2a+b`, `c' = a+b+c`. **Both values sit inside `[1, m)`, so the range sanity check does not catch this one.** The most dangerous coefficient near-miss in the set. |
| NM-10' | `a=1654397203`, `b=7019704481`, `c=7512847583` | correct | Same off-by-two, window `x = 2..5`. | Reports `P(x+2)`: `b' = 4a+b`, `c' = 4a+2b+c`. Also inside the box, also uncaught by range checks. |
| NM-11 | `a=3308794406`, `b`/`c` correct | correct | Read the second finite difference as `a` instead of `2a`. | `a` is doubled. Classic bookkeeping slip; no partial credit applies. |
| NM-12 | `a` correct, `b=2056512872`, `c` correct | correct | Read the first finite difference at the window start as `b`, forgetting it equals `a+b`. | `b` is inflated by `a`. |
| NM-13 | `a=838950838706`, rest correct | correct | Recovered `a` correctly but reported it unreduced (`a + m`). | Outside the declared `[1, m)` box. The representative matters: the answer is the canonical residue. |

### 3c. Format-level failures

| # | Submission | Reason |
|---|---|---|
| NM-14 | all four correct, but as `{"a": ..., "b": ..., "c": ..., "modulus": ...}` | Required key `m` absent. Recoverable by the normaliser only if the intent is unambiguous; if the grader has to guess, it is a FAIL. |
| NM-15 | `"m is either 837296441503 or 1674592883006"` | Hedged. FAIL — see section 2. |
| NM-16 | all four correct but `m` given as `8.372964415e11` | Lossy float; does not convert to the exact integer. FAIL. |
| NM-17 | values correct but positionally reversed, e.g. `[c, b, a, m]` against an expected `[m, a, b, c]` | Field identity is part of the answer. FAIL. |

## 4. What a PASS looks like

```json
{"m": 837296441503, "a": 1654397203, "b": 402115669, "c": 91027433}
```

Accepted regardless of route, key order, integer-as-string, or surrounding prose, provided the
four values are exactly these and the submission commits to them.

## 5. Grader implementation note

```
load golden/expected.json
parse submission -> {m, a, b, c} as exact ints (reject lossy conversions, reject hedges)
PASS  iff  all four fields equal the locked values
FAIL  otherwise, with the matching NM-row cited when one applies
```

The NM citation is for calibration reporting only. It never changes the score.

## 6. Coverage check against the locked design

The table is built to catch the failures the design actually produces, not a generic list:

- **The headline trap** (modulus invisible in the low window) -> NM-1, NM-2.
- **Incomplete disambiguation of the gcd** -> NM-3, NM-3'.
- **False-clean windows** — the measured 31% of 4-wide windows with `D3 = 0` that still give
  wrong coefficients -> NM-8, NM-9.
- **Indexing slips that survive a range check** -> NM-10, NM-10'.
- **Finite-difference bookkeeping** -> NM-11, NM-12.
- **The undocumented surface as a false lead** -> NM-7.
- **Canonical-representative discipline** -> NM-13.

### Resolved at the Section 6b red-team

- **NM-2 was nearly self-refuting, and the design was changed to save it.** The prompt originally
  declared `1e11 < m < 1e13`. Every output of a low sweep is below `4.35e10`, i.e. below that
  lower bound — so a careful solver could deduce *from the prompt alone* that no reduction had
  fired in their sample, and could reject NM-2 without spending a probe. That handed over the
  insight the task is built on. The declared range is now `1e10 < m < 1e13`, which is below the
  largest low-sweep output, so NM-2 is a fully admissible answer that only the box can refute.
  Graders should expect NM-2 to stay the most common failure.
- **Headline ordering kept as is.** NM-1/NM-2 remain first: they are what a solver who never
  leaves the low region produces, and that is the majority failure. NM-10 stays where it is but
  is the most *dangerous* row for a solver who clears the gate, because it is the only family
  that is wrong while sitting entirely inside the declared box.
- **No fifth family of wrong moduli was found.** Every wrong modulus observed in testing is a
  member of one of these: below-the-truth minimal guesses (NM-2), small multiples of the truth
  (NM-3), near-neighbours of the truth (NM-4, NM-6), round guesses (NM-5), and noise-derived
  values (NM-7).
