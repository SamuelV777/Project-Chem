# task-01 — Recover the hidden rule

## The system

A black box holds one fixed arithmetic rule of the form

```
f(x) = (a*x^2 + b*x + c) mod m
```

The four values `m`, `a`, `b`, `c` were chosen once, before this prompt was written, and do not
change. They are what you are here to find.

What you are told about them:

- `m` is **prime**, and `10000000000 < m < 10000000000000`.
- `a`, `b`, `c` are integers with `1 <= a, b, c < m`.
- The input domain is the integers `x` with `0 <= x <= 1000000`.

Exactly one `(m, a, b, c)` satisfying those constraints produces the box's behaviour. There is
no ambiguity in the answer and no second valid solution.

## What you must recover

All four values: `m`, `a`, `b`, `c`.

## How to probe the box

```python
import importlib.util
spec = importlib.util.spec_from_file_location("oracle", "oracle/oracle.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)

box = oracle.Oracle()

y = box.evaluate(x)     # the integer output for input x -- costs 1 unit
hint = box.help()       # a fixed hint -- costs nothing
```

**`evaluate(x)`** returns the box's output for the integer input `x`. It is deterministic and
exact: the same input always returns the same output, and the output is never approximate or
rounded. **Each call costs 1 unit.**

A call with a non-integer input, or an input outside the domain, is rejected with an error and
costs you nothing — a rejected query buys no information, so it buys no cost.

**`help()`** returns a fixed hint. It is free, and it returns the same text every time, so there
is nothing to gain by calling it repeatedly. There is also no reason not to call it.

## The budget

**You have 6 units in total.**

The allowance is spent, never refunded, and there is no reserve. Once 6 units are gone,
`evaluate` refuses and you must answer from the evidence you already hold. The allowance is
shared: constructing another `Oracle()` does not buy you a fresh one.

Six units is not a lot. It is enough.

## Rules

- Treat the box as a black box. Probe it through the interface described above. Reading its
  internals, or reaching around the interface, is not a solution to this task — it also will not
  teach you anything you were asked to find out.
- Standard library only. No network access.
- Commit to one answer. See below.

## What to submit

A single JSON object with exactly these four integer fields:

```json
{"m": ..., "a": ..., "b": ..., "c": ...}
```

Report each value as an exact integer in its canonical range, `1 <= a, b, c < m`.

## How you are graded

**Exact match on all four fields. No partial credit, no tolerance.**

- All four correct — pass.
- Anything else — fail. Three fields right and one wrong scores exactly what an empty
  submission scores.
- **Do not hedge.** A submission offering two candidates, or qualifying an answer with "either
  this or that", is a failed submission. The grader will not choose on your behalf. Recovering
  the rule means committing to it.

One thing worth weighing before you spend your first unit: a rule that reproduces everything you
have observed is not the same as a rule your observations *force*. Only one of those is a
recovered answer.
