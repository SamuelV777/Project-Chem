# reasoning_trap.md — what `shortcut.py` falls into

## 1. The shortcut, stated fairly

`solution/shortcut.py` does what a competent person does first, and does it correctly:

1. Sweeps the cheapest contiguous inputs, `x = 0..5` — six probes, the entire allowance.
2. Takes finite differences. Every third difference is `0`.
3. Reads off the coefficients: `a = 1654397203`, `b = 402115669`, `c = 91027433`. **All three
   are exactly right.**
4. **Validates.** The fit is built from four points; the other two are spare. It predicts both
   and both land exactly. The model is not merely fitted, it is cross-checked.
5. Infers a modulus. No third difference anywhere in the sample is non-zero, so no reduction was
   ever observed to fire, so the modulus must exceed every output seen. It reports the least
   prime that satisfies that: `43461535867`.

Output: `{"m": 43461535867, "a": 1654397203, "b": 402115669, "c": 91027433}` — three of four
fields perfect, and a **FAIL** (grading guide, NM-2).

Note what is *not* wrong with it. It is not crippled, it does not run out of budget by accident,
it does not skip validation, and its final inference is **true**: the modulus really does exceed
every value it saw. Nothing in its own evidence contradicts a single thing it concluded.

## 2. The trap

**The shortcut mistakes the smallest modulus consistent with its evidence for the modulus its
evidence determines.** Those are different things, and here the gap is infinite.

Its six observations are consistent with the recovered coefficients under **every prime greater
than `43461535853`**. Not a handful of candidates — an unbounded family, of which the truth,
`837296441503`, is one perfectly ordinary member roughly nineteen times further out. The
shortcut did not choose badly among candidates. It never had grounds to choose at all.

The structural cause: `a*x^2 + b*x + c < m` holds **exactly for `x = 0..22`**. Inside that
window the reduction never fires and the box is indistinguishable from a plain integer
polynomial. The modulus is not merely hard to see there — it is *absent from the data*. No
amount of care, precision, or extra probing inside `x <= 22` can recover it, because nothing
inside that window depends on it.

## 3. Why the trap catches good solvers rather than careless ones

The cruelty is in step 2's third differences being zero. A zero third difference reads as
**confirmation** — the data is exactly quadratic, the model fits, the spare points validate, the
investigation feels finished. It is actually the opposite: it is the signature of a region that
carries **no information about the quantity still unknown**. The evidence that feels most
conclusive is the evidence that is most silent.

So the shortcut stops, and it stops *confident*, having passed every check it knew to run. There
is no ragged edge to prompt another look — and by then the allowance is gone anyway. That
combination, a self-validating fit plus a spent budget, is the trap.

This is also why grading is exact-match with no partial credit. Under partial credit the
shortcut would score 3/4 for work that never located the hidden quantity at all, and the task
would be measuring arithmetic instead of investigation.

## 4. How the intended solver escapes

`solution/main.py` spends its allowance in two regimes instead of one: four low probes for the
coefficients, two far probes for the modulus. The far probes work because of an identity the low
window cannot supply — for any `x`,

```
fitted(x) - box(x) = (an exact multiple of the modulus)
```

Two such differences, and `gcd` returns the modulus times a small cofactor; the cofactor strips
off because the modulus is prime and everything else in the gcd is small. Recovery is exact and
deterministic: no estimation, no statistics, no luck. Verified over 60 random far-probe pairs,
0 failures.

The decisive move is not algebraic skill. It is asking, **before** spending anything: *which of
my four unknowns does this probe actually inform?* The shortcut never asks, and spends six
probes answering a question it had already answered after four.

## 5. Is the trap real, or is the shortcut sabotaged?

Held to the standard that a slightly smarter naive solver must not walk through it:

- **Would probing more points help?** No. Any number of probes with `x <= 22` leaves the modulus
  exactly as undetermined as one probe does. The failure is not a sample-size problem.
- **Would probing farther out be enough by itself?** Partly, and this claim has been measured
  rather than asserted. Far outputs do not interpret themselves: a solver holding `f(999983)`
  and nothing else has gained nothing, and still needs a way to turn outputs into a multiple of
  the modulus. But the residue identity above is **not the only such way** — differencing four
  or more *consecutive* far probes also produces one, without ever fitting the low window. So
  the second layer is real but thinner than "you must find this one identity": of five
  approaches in the harness panel that clear the first layer, **three succeed and two still
  fail** (an off-by-one low window, and a brute-force search that never terminates in budget).
  Clearing the first layer is therefore necessary and *usually* sufficient. The honest summary
  is that this task has one hard gate and one modest one, not two hard ones.
- **Would a smarter modulus guess help?** No. `43461535867` is already the best-justified guess
  available from that evidence. Every alternative is worse-motivated, and all of them are wrong.
- **Is the shortcut's reasoning sound?** Yes, every step, including the last. It fails on a true
  premise, correctly applied. That is what makes it a trap rather than a mistake.

**The honest residual risk**, recorded rather than hidden: a solver who habitually spreads probes
across a domain — not from insight, just from habit — lands in the right regime by accident and
then needs only the gcd step. The design does not prevent that, and should not pretend to. It is
the main reason the difficulty target is *at most* 2 in 8 rather than 0 in 8. Carried to §6b for
adversarial review.

## 6. The second trap, for solvers who clear the first

A solver who reaches the far region can still lose on the coefficients. A 4-wide consecutive
window looks perfectly clean — third difference exactly `0` — in **1259 of 4000** random
trials, and in **1259 of 1259** of those the unreduced integer fit is wrong, because the window
wrapped uniformly rather than not at all. It yields values like `c = -837205414070`, which is
correct modulo the modulus and outside the declared `[1, m)` box (grading guide, NM-8/NM-9).

Same lesson, one level up: *a clean fit is not a validated one.* The remedy is the same discipline
the oracle's free hint points at — ask what else could have produced exactly this evidence.
