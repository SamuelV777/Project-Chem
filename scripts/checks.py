"""Calibration harness for task-01.

    python scripts/checks.py verify     intended solver recovers the answer   -> PASS
    python scripts/checks.py shortcut   naive solver does not                 -> FAIL (as intended)
    python scripts/checks.py lint       prompt leaks nothing                  -> CLEAN
    python scripts/checks.py preview    difficulty target                     -> <= 2/8
    python scripts/checks.py selftest   all four, asserted                    -> all green

Stdlib only. Offline. No configuration.

Every check loads a *fresh* oracle module object, so each one starts with a full
allowance and none can be contaminated by another. Budget figures are read from
the oracle itself, never from a solver's self-report.

This file contains no literal of the answer: it reads golden/expected.json.
"""

import importlib.util
import json
import os
import re
import sys
from math import gcd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GREEN = "PASS"
RED = "FAIL"


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------

def _load(name, relpath):
    path = os.path.join(ROOT, relpath)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fresh_oracle():
    """An oracle with a full allowance and a clean noise stream.

    The allowance lives per interpreter, not per module object -- deliberately,
    so that re-importing the oracle cannot buy extra probes. That means a fresh
    module object is NOT a fresh budget, and the harness has to ask for one.
    """
    module = _load("task01_oracle_%d" % fresh_oracle.counter, "oracle/oracle.py")
    module._harness_reset()
    return module


fresh_oracle.counter = 0


def _next_oracle():
    fresh_oracle.counter += 1
    return fresh_oracle()


def expected():
    with open(os.path.join(ROOT, "golden", "expected.json")) as fh:
        return json.load(fh)


def read(relpath):
    with open(os.path.join(ROOT, relpath), encoding="utf-8") as fh:
        return fh.read()


def line(ok, label, detail=""):
    tag = GREEN if ok else RED
    print(f"[{tag}] {label}" + (f" -- {detail}" if detail else ""))
    return ok


def is_prime(n):
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for p in small:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for base in small:
        x = pow(base, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------

def cmd_verify():
    print("== verify: does the intended solver recover the locked answer? ==")
    gold = expected()
    answer = gold["answer"]
    budget = gold["constraints"]["budget_units"]

    orc = _next_oracle()
    main = _load("task01_main", "solution/main.py")
    try:
        got, _ = main.solve(orc)
    except Exception as exc:
        return line(False, "intended solver raised", f"{type(exc).__name__}: {exc}")

    spent = orc._harness_spent()
    correct = got == answer
    in_budget = spent <= budget

    for field in ("m", "a", "b", "c"):
        ok = got.get(field) == answer[field]
        print(f"     {field}: {got.get(field)} {'==' if ok else '!='} locked value")
    line(in_budget, "within allowance", f"{spent}/{budget} units spent")
    return line(correct and in_budget, "intended solver recovers the answer")


# --------------------------------------------------------------------------
# shortcut
# --------------------------------------------------------------------------

def cmd_shortcut():
    print("== shortcut: does the naive solver fail, as it must? ==")
    gold = expected()
    answer = gold["answer"]

    orc = _next_oracle()
    short = _load("task01_shortcut", "solution/shortcut.py")
    try:
        got, _ = short.solve(orc)
    except Exception as exc:
        return line(False, "naive solver raised instead of answering wrongly",
                    f"{type(exc).__name__}: {exc} "
                    "(a trap must produce a confident wrong answer, not a crash)")

    spent = orc._harness_spent()
    recovered = got == answer
    fields_right = [f for f in ("m", "a", "b", "c") if got.get(f) == answer[f]]

    print(f"     submitted: {json.dumps(got)}")
    print(f"     fields correct: {len(fields_right)}/4 {fields_right}")
    print(f"     units spent: {spent}")

    # The trap is only interesting if the naive solver gets *most* of it right
    # and still fails. A naive solver that gets nothing right proves nothing.
    tempting = len(fields_right) == 3
    line(tempting, "near-miss is genuinely tempting", f"{len(fields_right)}/4 fields correct")
    return line(not recovered, "naive solver does NOT recover the answer",
                "FAIL (as intended)")


# --------------------------------------------------------------------------
# lint
# --------------------------------------------------------------------------

def cmd_lint():
    print("== lint: does anything the solver reads leak the answer? ==")
    gold = expected()
    ans = gold["answer"]
    m, a, b, c = ans["m"], ans["a"], ans["b"], ans["c"]

    prompt = read("problem.md")
    orc = _next_oracle()
    hint = orc.Oracle().help()          # free, so linting it costs no allowance
    brief = read("BRIEF.md")

    def rule(x):
        return (a * x * x + b * x + c) % m

    # 1. the four values themselves
    literals = {"m": m, "a": a, "b": b, "c": c}

    # 2. quantities that would narrow the answer without naming it
    derived = {
        "2a": 2 * a,
        "a+b": a + b,
        "2a+b": 2 * a + b,
        "4a+b": 4 * a + b,
        "a+b+c": a + b + c,
        "4a+2b+c": 4 * a + 2 * b + c,
        "a+m": a + m,
        "m-1": m - 1,
        "m+1": m + 1,
        "2m": 2 * m,
        "m//a": m // a,
        "wrap boundary": gold["structure"]["wrap_free_window"][1],
        "first wrapping input": gold["structure"]["first_wrapping_input"],
    }

    # 3. any actual output of the box, anywhere in the low region a solver
    #    would naturally probe, plus a spread of far ones
    outputs = {rule(x) for x in range(0, 200)}
    outputs |= {rule(x) for x in range(0, 1000001, 9973)}

    # 4. words that would hand over the technique
    method_words = [
        "gcd", "greatest common", "finite difference", "third difference",
        "second difference", "wrap", "overflow", "residue", "divisor",
        "multiple of the", "interpolat", "factorise", "factorize",
    ]

    # 5. the undocumented surface
    undocumented = ["sample", "calibrat", "noisy", "noise", "uncalibrated"]

    failures = []

    for label, text in (("problem.md", prompt), ("help()", hint)):
        low = text.lower()
        hits = [k for k, v in literals.items() if str(v) in text]
        if hits:
            failures.append(f"{label} names the answer: {hits}")
        hits = [k for k, v in derived.items() if str(v) in text]
        if hits:
            failures.append(f"{label} leaks derived quantities: {hits}")
        nums = {int(n) for n in re.findall(r"\b\d{5,}\b", text)}
        hits = sorted(nums & outputs)
        if hits:
            failures.append(f"{label} quotes real box outputs: {hits}")
        hits = [w for w in method_words if w in low]
        if hits:
            failures.append(f"{label} gives away the method: {hits}")
        hits = [w for w in undocumented if w in low]
        if hits:
            failures.append(f"{label} advertises the undocumented surface: {hits}")

    # BRIEF.md is author-facing, but a partial leak there is still a leak.
    blow = brief.lower()
    hits = [k for k, v in literals.items() if str(v) in brief]
    hits += [k for k, v in derived.items() if str(v) in brief]
    if hits:
        failures.append(f"BRIEF.md leaks: {hits}")

    # the prompt must still be usable: it has to state the real constraints
    K = gold["constraints"]
    required = {
        "modulus lower bound": str(K["m_range_exclusive"][0]),
        "modulus upper bound": str(K["m_range_exclusive"][1]),
        "domain maximum": str(K["domain"][1]),
        "budget": str(K["budget_units"]),
    }
    missing = [k for k, v in required.items() if v not in prompt]
    if missing:
        failures.append(f"problem.md omits stated constraints: {missing}")

    # and the locked answer must actually satisfy what the prompt claims
    lo, hi = K["m_range_exclusive"]
    if not (lo < m < hi and all(1 <= v < m for v in (a, b, c)) and is_prime(m)):
        failures.append("the locked answer violates the constraints the prompt states")

    for f in failures:
        print(f"     {f}")
    print(f"     scanned: problem.md, help(), BRIEF.md "
          f"({len(literals)} literals, {len(derived)} derived, {len(outputs)} outputs, "
          f"{len(method_words)} method words)")
    return line(not failures, "solver-facing text leaks nothing", "CLEAN" if not failures else "")


# --------------------------------------------------------------------------
# preview -- the strategy panel
# --------------------------------------------------------------------------

def _fit4(values, start):
    """Integer quadratic through four consecutive observations, re-expressed in x."""
    d1 = [values[i + 1] - values[i] for i in range(3)]
    d2 = [d1[i + 1] - d1[i] for i in range(2)]
    d3 = d2[1] - d2[0]
    lead = d2[0] // 2
    lin = d1[0] - lead
    const = values[0]
    return (lead, lin - 2 * lead * start, lead * start * start - lin * start + const), d3


def _strip(g, bound=1_000_000):
    remaining, d = g, 2
    while d <= bound and remaining > 1:
        if is_prime(remaining):
            return remaining
        if remaining % d == 0:
            remaining //= d
            continue
        d += 1 if d == 2 else 2
    return remaining


def _s_low_sweep_minimal_prime(orc):
    """Sweep the cheap end; report the least prime above everything seen."""
    box = orc.Oracle()
    vals = [box.evaluate(x) for x in range(6)]
    (a, b, c), _ = _fit4(vals[:4], 0)
    cand = max(vals) + 1
    if cand % 2 == 0:
        cand += 1
    while not is_prime(cand):
        cand += 2
    return {"m": cand, "a": a, "b": b, "c": c}


def _s_low_sweep_no_modulus(orc):
    """Sweep the cheap end; conclude the reduction never fires and omit it."""
    box = orc.Oracle()
    vals = [box.evaluate(x) for x in range(6)]
    (a, b, c), _ = _fit4(vals[:4], 0)
    return {"m": None, "a": a, "b": b, "c": c}


def _s_two_regime_raw_gcd(orc):
    """Right idea, one step short: report the gcd without stripping its cofactor."""
    box = orc.Oracle()
    vals = [box.evaluate(x) for x in range(4)]
    (a, b, c), _ = _fit4(vals, 0)
    g = 0
    for x in (1000000, 999999):
        g = gcd(g, a * x * x + b * x + c - box.evaluate(x))
    return {"m": abs(g), "a": a, "b": b, "c": c}


def _s_intended(orc):
    """The intended route, via solution/main.py itself."""
    main = _load("task01_main_panel", "solution/main.py")
    got, _ = main.solve(orc)
    return got


def _s_offbyone_window(orc):
    """Two-regime, but the low window is read as if it began at zero."""
    box = orc.Oracle()
    vals = [box.evaluate(x) for x in (1, 2, 3, 4)]
    (a, b, c), _ = _fit4(vals, 0)          # the slip: start is really 1
    g = 0
    for x in (999983, 524287):
        g = gcd(g, a * x * x + b * x + c - box.evaluate(x))
    m = _strip(abs(g)) if g else 0
    return {"m": m, "a": a % m if m else a, "b": b % m if m else b, "c": c % m if m else c}


def _s_far_consecutive_window(orc):
    """Six consecutive probes far out; modulus from the third differences."""
    box = orc.Oracle()
    start = 500000
    vals = [box.evaluate(start + i) for i in range(6)]
    d3 = [vals[i + 3] - 3 * vals[i + 2] + 3 * vals[i + 1] - vals[i] for i in range(3)]
    g = 0
    for v in d3:
        g = gcd(g, v)
    if g == 0:
        return {"m": None, "a": None, "b": None, "c": None}
    m = _strip(abs(g))
    # coefficients mod m from three of the observations, by elimination over GF(m)
    xs = [start, start + 1, start + 2]
    ys = [vals[0], vals[1], vals[2]]
    A = [[xs[i] ** 2 % m, xs[i] % m, 1, ys[i] % m] for i in range(3)]
    for col in range(3):
        piv = next((r for r in range(col, 3) if A[r][col] % m), None)
        if piv is None:
            return {"m": m, "a": None, "b": None, "c": None}
        A[col], A[piv] = A[piv], A[col]
        ipiv = pow(A[col][col], -1, m)
        A[col] = [(v * ipiv) % m for v in A[col]]
        for r in range(3):
            if r != col and A[r][col]:
                f = A[r][col]
                A[r] = [(A[r][k] - f * A[col][k]) % m for k in range(4)]
    a, b, c = A[0][3], A[1][3], A[2][3]
    return {"m": m, "a": a, "b": b, "c": c}


def _s_sample_led(orc):
    """Find the undocumented surface, spend on it, fit to what it returns."""
    box = orc.Oracle()
    reads = [box.sample() for _ in range(2)]
    vals = [box.evaluate(x) for x in range(4)]
    (a, b, c), _ = _fit4(vals, 0)
    g = 0
    for r in reads:
        g = gcd(g, a * r["input"] ** 2 + b * r["input"] + c - r["reading"])
    m = _strip(abs(g)) if g else 0
    return {"m": m, "a": a, "b": b, "c": c}


def _s_bounded_prime_search(orc):
    """Probe both regimes, then search primes upward for a consistent modulus."""
    box = orc.Oracle()
    vals = [box.evaluate(x) for x in range(4)]
    (a, b, c), _ = _fit4(vals, 0)
    far = [(x, box.evaluate(x)) for x in (999983, 524287)]
    cand = max(vals) + 1
    checked = 0
    LIMIT = 200_000            # a patient solver's search budget, not an infinite one
    while checked < LIMIT:
        if is_prime(cand):
            if all((a * x * x + b * x + c) % cand == y for x, y in far):
                return {"m": cand, "a": a % cand, "b": b % cand, "c": c % cand}
        cand += 1
        checked += 1
    return {"m": None, "a": a, "b": b, "c": c, "_note": f"gave up after {LIMIT} candidates"}


# Each strategy is tagged by whether it embodies the key insight: spending probes
# where the reduction actually fires. That tag is what makes the panel readable --
# see cmd_preview for why the raw count is not the difficulty.
INSIGHT_FREE = "no"
INSIGHT_BEARING = "yes"

PANEL = [
    (INSIGHT_FREE,    "low sweep, least consistent prime", _s_low_sweep_minimal_prime),
    (INSIGHT_FREE,    "low sweep, modulus omitted", _s_low_sweep_no_modulus),
    (INSIGHT_FREE,    "led by the undocumented surface", _s_sample_led),
    (INSIGHT_BEARING, "two regimes, cofactor stripped (intended)", _s_intended),
    (INSIGHT_BEARING, "two regimes, gcd reported raw", _s_two_regime_raw_gcd),
    (INSIGHT_BEARING, "six consecutive probes far out", _s_far_consecutive_window),
    (INSIGHT_BEARING, "two regimes, low window off by one", _s_offbyone_window),
    (INSIGHT_BEARING, "two regimes, then brute-force search", _s_bounded_prime_search),
]


def _run_panel(answer, budget):
    results = []
    for tag, name, fn in PANEL:
        orc = _next_oracle()
        try:
            got = fn(orc)
            spent = orc._harness_spent()
            ok = {k: got.get(k) for k in ("m", "a", "b", "c")} == answer
            note = got.get("_note", "")
        except Exception as exc:
            ok, spent, note = False, orc._harness_spent(), type(exc).__name__
        results.append((tag, name, ok, spent, note))
    return results


def cmd_preview():
    print("== preview: intended difficulty ==")
    gold = expected()
    answer = gold["answer"]
    budget = gold["constraints"]["budget_units"]

    print("     target: a strong model at 8 attempts lands <= 2/8")
    print(f"     allowance: {budget} units; grading: exact match on 4 fields, no partial credit")
    print()
    print("     What this panel is, and is not:")
    print("       It runs 8 plausible approaches. It does NOT simulate 8 model attempts --")
    print("       nothing offline can, because the difficulty here is how often a solver")
    print("       has the key insight, and that needs a model to measure. So the raw count")
    print("       is not the pass rate. What the panel CAN falsify is two design claims:")
    print("         (1) no approach lacking the insight may succeed   -- else there is a bypass")
    print("         (2) some approach having it must succeed          -- else the task is unfair")
    print()

    results = _run_panel(answer, budget)

    for want, heading in (
        (INSIGHT_FREE, "     approaches WITHOUT the insight (every one must fail):"),
        (INSIGHT_BEARING, "     approaches WITH the insight (at least one must pass):"),
    ):
        print(heading)
        for tag, name, ok, spent, note in results:
            if tag != want:
                continue
            mark = "PASS" if ok else "fail"
            print(f"       [{mark}] {name:<42} {spent}/{budget} units"
                  + (f"  ({note})" if note else ""))
        print()

    free = [r for r in results if r[0] == INSIGHT_FREE]
    bearing = [r for r in results if r[0] == INSIGHT_BEARING]
    bypasses = [r for r in free if r[2]]
    cleared = [r for r in bearing if r[2]]

    print(f"     bypasses: {len(bypasses)}/{len(free)} (required: 0)")
    print(f"     past the gate: {len(cleared)}/{len(bearing)} succeed (required: at least 1)")
    print()

    if bypasses:
        print("     A bypass exists: the insight is not load-bearing. The task is broken.")
    else:
        print("     Difficulty rests entirely on the insight gate: every approach that")
        print("     skips it fails, without exception. The <= 2/8 target therefore holds")
        print("     exactly when a strong model finds the insight in at most 2 tries of 8 --")
        print("     which is a claim about the model, and is settled by running it, not here.")
    if len(cleared) == len(bearing):
        print("     NOTE: everything past the gate succeeds, so there is no second filter.")
    elif cleared:
        print(f"     {len(bearing) - len(cleared)} of {len(bearing)} approaches clear the gate and still fail,")
        print("     so execution past it is a real second filter, not a formality.")

    ok = not bypasses and bool(cleared)
    return line(ok, "difficulty target", "<= 2/8, gated on the insight")


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def cmd_selftest():
    print("== selftest: all four signals, asserted ==\n")
    results = {}
    for name, fn in (("verify", cmd_verify), ("shortcut", cmd_shortcut),
                     ("lint", cmd_lint), ("preview", cmd_preview)):
        results[name] = fn()
        print()

    print("== summary ==")
    for name, ok in results.items():
        expect = {
            "verify": "intended solver PASSES",
            "shortcut": "naive solver FAILS (as intended)",
            "lint": "prompt CLEAN",
            "preview": "difficulty <= 2/8",
        }[name]
        line(ok, f"{name:<9}", expect)

    every = all(results.values())
    print()
    return line(every, "all four signals land where they should",
                "task is calibrated" if every else "fix the specific artifact that failed")


COMMANDS = {
    "verify": cmd_verify,
    "shortcut": cmd_shortcut,
    "lint": cmd_lint,
    "preview": cmd_preview,
    "selftest": cmd_selftest,
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    return 0 if COMMANDS[sys.argv[1]]() else 1


if __name__ == "__main__":
    sys.exit(main())
