# BRIEF.md — Top-down summary of task-01

> **Leak discipline:** this file is author- and reviewer-facing, but it is written to the same
> standard as the solver-facing prompt: it names **no** parameter value, **no** boundary
> location, and **no** oracle output. It describes the *shape* of the task, not its content.
> The answer lives in `STATE.md` and `golden/expected.json` only.

## 1. What the hidden system is

A deterministic black box holding a **quadratic congruence over the integers**:

```
f(x) = (a*x^2 + b*x + c) mod m
```

- `m` is prime, with `1e10 < m < 1e13`.
- `a`, `b`, `c` are integers in `[1, m)`.
- The input domain is `x` in `[0, 1000000]`, integer.
- The box is exact and noiseless on its advertised surface. Nothing is randomised there, and
  the same input always returns the same output.

All four values are fixed and were committed before any solver-facing text existed.

## 2. What the solver must recover

The **complete rule**: all four of `m`, `a`, `b`, `c`.

Grading is **exact match on all four fields. There is no partial credit.** A submission with
three fields perfect and one wrong scores exactly the same as a blank one. This is deliberate
and is the load-bearing decision of the whole design — see section 5.

## 3. The surfaces and the budget

The solver is given a black box with a **6-unit budget**, spent as follows:

| Surface | Cost | Advertised to the solver? |
|---|---|---|
| `evaluate(x)` | 1 unit | yes |
| `help()` | free | yes |
| `sample()` | 1 unit | **no** |

`evaluate(x)` is the only surface the prompt describes for gathering evidence. `help()` returns
a fixed, free hint that is written to survive repeated calls without narrowing the answer space.

`sample()` exists on the object but is **deliberately absent from `problem.md`**. It is
reachable by a solver who introspects the box rather than reading the brief. It is seeded, so
it is reproducible run to run, and it **charges the budget like any probe**. It is not a
shortcut and not a gift: it is a cost for solvers who spend their allowance on discovery
instead of on reasoning.

Budget exhaustion is hard. Once 6 units are spent, no further evidence is available, and the
solver must answer from what they already hold.

## 4. Where the difficulty actually lives

Not in the algebra. Recovering polynomial coefficients from finite differences is standard, and
any competent solver will do it quickly.

The difficulty is that the four unknowns are **not equally observable**. The domain is not
uniform: what a probe tells you depends on *where you spend it*, and the cheapest, most natural
probes do not inform all four fields equally. With only 6 units and no refunds, the solver's
real task is **allocating a budget across a domain whose informativeness they must first reason
about** — before spending it. A solver who probes first and thinks afterwards will have bought
a confident, self-consistent, incomplete picture, and will have nothing left to fix it with.

The search space rules out brute force by construction: `m` alone ranges over roughly 3e11
primes, and `(a, b, c)` over `m^3`. There is no sweeping the answer out. The investigation has
to be real.

## 5. Difficulty target

**A strong model at 8 attempts should land at most 2/8.**

The target is reached by the interaction of three things, not by any one of them:

1. **The natural approach terminates early and feels finished.** The evidence it produces is
   internally consistent and passes its own sanity checks, so there is no felt prompt to keep
   investigating. This is the reasoning trap, documented in `reasoning_trap.md` (Step 5).
2. **Exact match on all four fields, no partial credit.** This converts "mostly solved" into a
   failure. Without it, the trap would still fire but would cost almost nothing, and the task
   would grade as easy.
3. **A 6-unit budget that the natural route spends in the wrong place.** The reference route
   uses all six (four to characterise, two to pin the remaining unknown). The *cheapest*
   correct route needs only four, so there are two units of genuine slack — the allowance is
   not what makes this hard, and claiming otherwise would be a lie the harness can catch.
   What the budget does is punish sequencing: a solver who spends all six before asking which
   unknowns they have actually informed has nothing left to fix it with, whether the true
   minimum was four or six.

Fairness is preserved because the recovery path is **exact and deterministic** — no estimation,
no statistics, no luck, no seed sensitivity. A solver who reasons correctly about where to
spend probes recovers all four values with certainty, every run. The task is hard because the
right allocation is non-obvious, not because the answer is hidden behind noise.

## 6. Artifact status

| Step | Artifact | State |
|---|---|---|
| 1 | `STATE.md`, `golden/expected.json` | done — answer locked |
| 2 | `BRIEF.md` | this file |
| 3 | `grader/grading_guide.md` | done — 21 machine-verified near-misses |
| 4 | `oracle/oracle.py` | done — three surfaces, budget anchored per interpreter |
| 5 | `solution/main.py`, `solution/shortcut.py`, `reasoning_trap.md` | done — passes / fails as required |
| 6 | `problem.md` | done — written last, leak-scanned |
| 6 | `scripts/checks.py` | done — four signals, negative-tested |
| 6b | adversarial self-critique | done — `.scratch/critique.md`, defects fixed |
