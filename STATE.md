# STATE.md — Locked answer (NOT solver-facing)

> Written at Section 4, Step 1, before any solver-facing artifact exists.
> Nothing in `problem.md`, `help()`, or `BRIEF.md` may restate anything below.

## 1. The committed answer

The hidden system is a **quadratic congruence with a hidden prime modulus**, evaluated over
the input domain `x` in `[0, 1000000]`:

```
f(x) = (a*x^2 + b*x + c) mod m
```

**Locked parameters — this is the answer the solver must recover:**

| Symbol | Value | Notes |
|---|---:|---|
| `m` | `837296441503` | prime (Miller-Rabin, bases 2..37); approx 8.37e11 |
| `a` | `1654397203` | leading coefficient |
| `b` | `402115669` | linear coefficient |
| `c` | `91027433` | constant term, equals `f(0)` |

Declared constraint box (the family the answer is unique *within*, to be stated to the solver):

- `m` prime, `1e10 < m < 1e13`
- `1 <= a, b, c < m`, `a != 0`
- domain `x` in `[0, 1000000]`, integer
- budget: **6** units; `evaluate(x)` costs 1, `sample()` costs 1, `help()` is free

## 2. The structural fact the whole task is built on

`a*x^2 + b*x + c < m` **exactly for `x = 0 .. 22`**, and for no larger `x` in the domain.

So the system splits into two regimes:

- **Wrap-free window `x <= 22`** — `f(x) = a*x^2 + b*x + c` over the integers. The modulus is
  *completely invisible* here: every observation is consistent with every `m` greater than the
  largest value seen. Four consecutive probes recover `a, b, c` exactly, and the third finite
  difference is `0`, which *looks like* confirmation that the rule is fully understood.
- **Wrapping regime `x >= 23`** — `f(x) = P(x) - m*w(x)` with `w(x) >= 1`. Only here does `m`
  leave a trace.

Recovering `a, b, c` is easy and is *not* where the task lives. Recovering `m` is the task,
and it costs queries in a regime the solver has no reason to visit unless they realise the
first regime is silent about it.

Reference solve (spends the full 6-unit budget; the cheapest correct route is 4 — see 3.7):

1. `evaluate(0..3)` -> 4 units. `c = F0`, `a = D2/2`, `b = D1_0 - a`; `D3 = 0` proves wrap-free.
2. `evaluate(x1), evaluate(x2)` at large `x` -> 2 units. Each gives `P(xi) - f(xi) = m*wi`.
3. `g = gcd(m*w1, m*w2) = m*gcd(w1, w2)`. Measured over 400 random large pairs: `g = m` outright
   in 240/400 cases; otherwise `g = m*d` with `d` in `{2 .. 14}`, and since `m` is prime and
   `d` is tiny, stripping small factors (or taking the largest prime factor) recovers `m` in
   **160/160** of the remaining cases. So the protocol is robust, not seed-luck.

## 3. Order of design decisions (chronological)

1. **Chose the failure mode first, not the formula.** The trap had to be *"the evidence a
   competent person would collect is genuinely insufficient, and looks sufficient."* That
   demanded a hidden quantity that is invisible on an entire contiguous region of the domain.
2. **Picked "hidden modulus" as that quantity**, and a polynomial as the carrier, because a
   polynomial's finite differences annihilate to a clean multiple of the modulus — giving an
   exact, non-statistical recovery path so the task stays *fair*.
3. **Picked degree 2, not 1.** Degree 1 wraps at a constant rate and is the textbook example;
   degree 2 grows fast enough that the wrap-free window is short and sharply bounded, and the
   third-difference identity is less rehearsed than the first-difference one.
4. **Sized the window at 22.** Chose `m/a` approx `506` so the wrap-free region is
   `x <= floor(sqrt(m/a)) = 22`. Long enough that every natural probe set (`0..3`, `0..5`,
   `1..6`) lands entirely inside it; short enough that any deliberate reach outward escapes it
   immediately.
5. **Sized `m` at ~8.4e11 and made it prime.** Prime for two reasons: it makes `a, b, c`
   uniquely determined mod `m` (Vandermonde invertible), and it lets the solver disambiguate
   `m` from the multiple `m*d` that a gcd of two probes can return.
6. **Sized the domain at 1e6** so `w(x)` reaches ~2e9 — large, varied, and with the
   coprimality that makes two probes enough.
7. **Set budget 6** — the reference plan uses `4 + 2`. NOTE (revised at 6b): this is *not*
   tight. The cheapest correct route is 4 units (3 low probes force the coefficients, 1 far
   probe plus Pollard-rho factoring gives the modulus), so 2 units of slack exist. The budget
   is a sequencing constraint, not a scarcity one: a solver who spends all 6 in one regime has
   lost, regardless of what the true minimum was.
8. **Only then** locked these four integers and wrote this file.

## 4. Why this is the only answer

Let `(m', a', b', c')` be any member of the declared constraint box that reproduces the
oracle's output on every `x` in the domain. Then:

**Step 1 — `m'` divides every third difference.** For any quadratic `P'` with integer
coefficients, `P'(x+3) - 3P'(x+2) + 3P'(x+1) - P'(x) = 0` identically. Since each observed
`F(x)` is congruent to `P'(x)` mod `m'`, the same alternating sum of *observed* values is
congruent to `0` mod `m'`. So `m'` divides `D3(x)` for every `x`, hence `m'` divides `G`,
where `G = gcd over x of D3(x)`.

**Step 2 — that gcd is exactly `m`.** Computed over **all** `x` in `[0, 999997]` (not sampled):
`G = 837296441503 = m`. (Verification retained in section 5.)

**Step 3 — so `m' = m`.** `m'` divides `m`, `m` is prime, and `m' > 1e10 > 1`, so `m' = m`.

**Step 4 — the coefficients then follow uniquely.** With the modulus fixed at the prime `m`,
any three distinct inputs give a Vandermonde system that is invertible over `GF(m)`, so
`(a', b', c')` is determined mod `m`; the box constrains each to `[1, m)`, so
`(a', b', c') = (a, b, c) = (1654397203, 402115669, 91027433)`. QED

**Uniqueness from the *intended* evidence specifically.** The six intended observations already
pin the answer: any admissible `m'` must divide `g = m*d` with `d <= 14`, and the only prime in
`(1e10, 1e13)` dividing `m*d` is `m` itself; Step 4 then applies unchanged.

**And why the naive evidence set is *not* enough — stated here so grading can be honest.**
Six probes drawn from `x <= 22` are consistent with `(a, b, c, m')` for **every** prime
`m' > 43461535853`. That is not a near-miss; it is an infinite family. The naive solver is not
unlucky — its evidence genuinely does not contain the answer. This is the reasoning trap, and
it is the reason the answer had to be locked before `problem.md` exists.

## 5. Verification record (reproduce with stdlib only)

| Claim | Result |
|---|---|
| `m` is prime | Miller-Rabin bases 2..37 -> prime |
| wrap-free window | `a*x^2+b*x+c < m` iff `x <= 22` (exhaustive over domain) |
| `f(x) = P(x)` for `x <= 22` | true for all 23 inputs |
| gcd of all third differences over domain | `837296441503` = `m` (exact, all 999998 windows) |
| 4 probes at `x=0..3` recover `a,b,c` | exact; third difference `= 0` |
| 2 large probes -> `m` | `g = m` in 240/400 random pairs; the other 160/160 yield `m` after removing the small cofactor `d` in `{2..14}` |
| naive window `x=0..5` determines `m` | **no** — consistent with every prime `m' > f(5) = 43461535853` |

Reference outputs (for building the oracle and the checks; **never** to appear in `problem.md`):
`f(0..5) = 91027433, 2147540305, 7512847583, 16186949267, 28169845357, 43461535853`;
`f(500) = 176007509451`; `f(500001) = 156037680238`.

## 6. Status

- [x] Answer locked (this file + `golden/expected.json`)
- [x] Grading policy confirmed by the human: **exact match on all four fields, no partial
      credit** (`expected.json` -> `grading.partial_credit = false`). Step 3 must build its
      near-miss table against this, so every near-miss is a full failure, not a deduction.
- [x] `BRIEF.md` — Step 2 (leak-scanned: contains no parameter value, no boundary location,
      no oracle output)
- [x] `grader/grading_guide.md` — Step 3. 21 near-miss values, all machine-verified to differ
      from the locked answer and to match their claimed derivations. Two measured facts feed
      it: a 4-wide window looks clean (`D3 = 0`) in 1259/4000 random trials and is wrong in
      1259/1259 of those; the two-large-probe gcd returns `m*d`, `d > 1`, in 160/400 pairs.
      Note for the red-team: NM-10 (`b = 2a+b`, `c = a+b+c` from an off-by-one window) lands
      **inside** `[1, m)`, so no range check catches it.
- [x] `oracle/oracle.py` — Step 4. Exactly three public methods (`evaluate`, `help`, `sample`);
      12-point test passed. Parameters live in a sha256-XOR envelope, so no decimal literal of
      the answer appears in the source — stated in the file as obfuscation, not secrecy.
      Budget is **module-level**, so `Oracle()` cannot be re-instantiated for a fresh allowance.
      Rejected queries are not charged. `help()` is a fixed string, identical on every call,
      and is methodological only (uniqueness-vs-fit, budget discipline) — it names no value and
      no technique. Defect found and fixed during this step: `sample()`'s drift could be `0`
      (~1 in 8193), which would have handed out an exact large-`x` probe; drift is now forced
      nonzero. Verified `sample()` yields `gcd = 1` over 6 readings, so it is not a route to
      the modulus even for a solver who already holds `a, b, c`.
- [x] `solution/main.py`, `solution/shortcut.py`, `reasoning_trap.md` — Step 5.
      `main.py` PASSES at exactly 6/6 units; correct on 60/60 random far-probe pairs and on
      7/9 low windows, and the 2 it rejects it rejects **loudly** (third difference non-zero
      means no valid integer fit) rather than answering wrongly. No answer literal in its
      source. Bug found and fixed during this step: `fitted()` closed over `a, b, c`, which
      Phase C rebinds to reduced values before verification ran — verification reconstructed
      the far observations from the *reduced* fit and so was both circular and wrong. It now
      verifies against what the box actually returned.
      `shortcut.py` FAILS as intended, landing exactly on near-miss NM-2
      (`m = 43461535867`, coefficients all correct). It is not sabotaged: it validates its fit
      on held-out probes, spends its full allowance, and its final inference is *true*.
      Open item carried to 6b (recorded in `reasoning_trap.md` §5): a solver who spreads probes
      out of habit rather than insight lands in the informative regime by accident. The second
      layer (the residue-gcd identity) is what keeps that from being a free pass.
- [ ] `oracle/oracle.py` — Step 4
- [ ] `solution/main.py`, `solution/shortcut.py`, `reasoning_trap.md` — Step 5
- [x] `problem.md` — Step 6, written **last**, after the answer had been locked for five steps.
      Seven-part adversarial leak scan passed: no answer literal; no derived quantity
      (`2a`, `a+b`, `2a+b`, `a+b+c`, `f(0)`, `f(1)`, `f(5)`, `m±1`, `2m`, the wrap boundary,
      `m/a`); no method word (gcd, difference, wrap, region, far, residue, factor, ...); no
      mention of `sample`, noise or calibration; and no number in the prompt is an actual box
      output — the only large numbers are the declared domain and modulus range, both of which
      the locked answer satisfies. `help()` re-scanned under the same rules: clean.
      Fixed during this step: the usage snippet called `evaluate(17)` literally, which would
      have silently cost a copy-pasting solver 1 of their 6 units on a probe they did not
      choose. Now a placeholder.

- [x] `scripts/checks.py` — Section 6 harness. `verify` / `shortcut` / `lint` / `preview` /
      `selftest`, all green. Each check loads a **fresh oracle module object**, so every one
      starts on a full allowance, and budget figures are read from the oracle itself, never
      from a solver's self-report. No answer literal in the harness source — it reads
      `golden/expected.json`. Negative-tested (harness proven non-vacuous): an injected
      modulus in `problem.md` -> lint FAILs; an injected *derived* quantity (`2a`) plus the
      phrase "second difference" -> lint FAILs on both counts; a perturbed `expected.json`
      -> verify FAILs. All restored, green re-confirmed.

      **Finding from the first `preview` run, recorded because it changed the harness.**
      The panel initially reported 3/8 and failed the gate. Inspection: all 3 passes were
      approaches that had already made the key move (probing where the reduction fires), and
      all 5 that lacked it failed. So there was no bypass — the defect was in the
      *measurement*. "How many of 8 distinct approaches succeed" is not "how many of 8 model
      attempts succeed", and the first version conflated them. `preview` now states plainly
      that nothing offline can measure the pass rate (it depends on how often a model has the
      insight), and gates on the two things it *can* falsify: **no insight-free approach may
      pass** (a bypass would mean the insight is not load-bearing) and **at least one
      insight-bearing approach must pass** (else the task is unfair). Current: 0/3 bypasses,
      3/5 past the gate.

      **Substantive risk this surfaced, carried to 6b:** 3 of 5 insight-bearing approaches
      succeed, so past the gate the task is not very hard. Two genuinely distinct routes exist
      (residue-gcd, and third differences of a far consecutive window), and the second does not
      need the low-window fit at all. This weakens the "two layers" claim in
      `reasoning_trap.md` §5 — the second layer is real (2 of 5 clear the gate and still fail)
      but thinner than that section implies. Decide in 6b whether to tighten §5's wording or
      the design.

- [x] **Section 6b adversarial self-critique** — `.scratch/critique.md`. Attacks were run as
      code, not asserted. **Eight defects found; all eight fixed.** Two were structural and
      would each have broken the task on their own:

      **D1 (critical): the budget was not enforced.** Re-importing `oracle.py` through a second
      `importlib` spec produced a second counter — measured 12 probes on a 6-unit allowance,
      unbounded on repeat. Every scarcity claim in the task was false, and `sample()`-as-a-cost
      was void. This survived four steps and a 12-point oracle test that specifically checked
      "a fresh `Oracle()` does not refill the allowance" — the test covered re-instantiation
      and never considered re-import. Fixed: state anchored on `sys`, so it exists once per
      interpreter however often the file is loaded. Re-verified refused.

      **D2 (major): the declared modulus range refuted the trap.** The old lower bound `1e11`
      sits *above* every low-sweep output (max `4.35e10`), so a solver could deduce from the
      prompt alone that nothing had wrapped — the core insight, given away in a constraint
      line — and could reject near-miss NM-2 for free. Fixed: range widened to
      `1e10 < m < 1e13`, which is below the largest low-sweep output. Truth still in range,
      uniqueness proof unaffected (it needs only `m' > a`), brute force still hopeless.

      D3: "budget has no slack" was false — cheapest correct solve is **4 units** (3 low probes
      force the coefficients, 1 far probe plus Pollard-rho gives the modulus). Corrected in
      `BRIEF.md` and here; the budget is a sequencing constraint, not a scarcity one.
      D4: `reasoning_trap.md` §5 overstated the second layer — measured 3 of 5 insight-bearing
      approaches succeed, so there is one hard gate and one modest one. Wording corrected.
      D5: `preview` measured the wrong quantity (see above). D6: `main.py` verified against a
      value it had computed itself. D7: `sample()` was an exact free probe ~1 call in 8193.
      D8: the prompt's example probe silently cost a unit.

      Accepted after attack, not defects: uniqueness holds under the widened range (verified —
      the low window forces `a, b, c` for *any* admissible modulus, and the far-residue gcd
      admits exactly one prime in range); `help()` gives 1 distinct string over 50 calls at 0
      units; `sample()` reproducibility is intended; the answer space is unsweepable
      (~3e11 primes); the shortcut is not sabotaged; no fifth family of wrong moduli exists.

      Section 6 checklist re-run from scratch afterwards: all five subcommands green.

**Status: complete.** All six authoring steps, the harness, and the adversarial pass are done.
