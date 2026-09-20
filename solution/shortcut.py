"""Naive solver for task-01 -- the first thing a competent person tries.

This is not a straw man. The approach below is the standard, sensible one, it is
executed correctly, and it checks its own work before answering:

  1. Sweep the cheapest inputs: x = 0, 1, 2, 3, 4, 5. Six probes, six units,
     the whole allowance spent on a clean contiguous sample.
  2. Take finite differences. The third difference is zero, so the data is an
     exact quadratic over the integers. Read off the three coefficients.
  3. Do not stop there -- validate. Use the two probes not consumed by the fit
     to predict and compare. Both predictions land exactly.
  4. Every third difference across the sample is zero, so no reduction was ever
     observed to fire. Report the smallest modulus consistent with that: the
     least prime exceeding the largest output seen. Any smaller modulus would
     have visibly wrapped one of these outputs, and it did not.

Each step is defensible. The conclusion is wrong, and the reason is in
reasoning_trap.md.

Stdlib only.
"""

import importlib.util
import json
import os
import sys

SWEEP = (0, 1, 2, 3, 4, 5)


def load_oracle():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, os.pardir, "oracle", "oracle.py")
    spec = importlib.util.spec_from_file_location("task01_oracle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def next_prime_above(n):
    candidate = n + 1
    if candidate % 2 == 0:
        candidate += 1
    while not is_prime(candidate):
        candidate += 2
    return candidate


def solve(oracle_module=None, verbose=False):
    oracle_module = oracle_module or load_oracle()
    box = oracle_module.Oracle()

    # 1. Sweep the cheap end of the domain.
    values = [box.evaluate(x) for x in SWEEP]
    if verbose:
        print("sweep:", values)

    # 2. Finite differences.
    d1 = [values[i + 1] - values[i] for i in range(5)]
    d2 = [d1[i + 1] - d1[i] for i in range(4)]
    d3 = [d2[i + 1] - d2[i] for i in range(3)]
    if verbose:
        print("first differences: ", d1)
        print("second differences:", d2)
        print("third differences: ", d3)

    a = d2[0] // 2
    b = d1[0] - a
    c = values[0]

    # 3. Validate on the part of the sample the fit did not consume.
    ok = all(a * x * x + b * x + c == values[x] for x in (4, 5))
    if verbose:
        print(f"fit a={a} b={b} c={c}; predictions for x=4,5 exact: {ok}")

    # 4. All third differences vanish, so nothing ever wrapped in this sample.
    #    The modulus therefore exceeds every value seen; take the least such prime.
    assert all(v == 0 for v in d3), "sample is not a clean quadratic"
    modulus = next_prime_above(max(values))
    if verbose:
        print(f"no wrapping observed anywhere in the sample; "
              f"largest output {max(values)} -> least consistent prime modulus {modulus}")

    spent = oracle_module._harness_spent()
    return {"m": modulus, "a": a, "b": b, "c": c}, spent


def main():
    answer, spent = solve(verbose="-v" in sys.argv)
    print(json.dumps(answer))
    print(f"# units spent: {spent}", file=sys.stderr)


if __name__ == "__main__":
    main()
