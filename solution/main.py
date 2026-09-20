"""Intended solver for task-01.

Recovers all four hidden values inside the 6-unit allowance, exactly and
deterministically -- no estimation, no search, no seed sensitivity.

The plan, decided before any unit is spent:

  Phase A (4 units)  Probe four consecutive low inputs. Their finite differences
                     give the three coefficients. The third difference also tells
                     us whether the window is trustworthy as an *integer* fit.

  Phase B (2 units)  Probe two far inputs. Here is the whole idea: for any x,
                     the fitted polynomial and the box's output differ by an
                     exact multiple of the hidden modulus. Two such differences,
                     and their gcd is the modulus times a small cofactor.

  Phase C (0 units)  Strip the cofactor, reduce the coefficients into canonical
                     range, and verify the recovered rule against every probe.

Why Phase B is not optional: Phase A alone cannot see the modulus at all. Its
four outputs are consistent with the recovered coefficients under *every*
modulus larger than the largest value observed -- an infinite family. A fit that
reproduces the evidence is not the same as a fit the evidence forces.

Stdlib only.
"""

import importlib.util
import json
import os
import sys
from math import gcd

LOW_WINDOW = (0, 1, 2, 3)
FAR_PROBES = (999983, 524287)

# The cofactor on the Phase B gcd is small but not tiny: sampling the pair space
# puts the worst case in the low ten-thousands, so strip well past that.
COFACTOR_BOUND = 1_000_000


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


def fit_integer_quadratic(window, values):
    """Return (a, b, c) in the x-variable from four consecutive observations.

    Also returns the third finite difference: zero means the window never
    wrapped, so the fit is exact over the integers. Non-zero means it did wrap,
    and the fit is only correct modulo the hidden modulus -- still usable,
    because Phase B needs nothing more than that.
    """
    d1 = [values[i + 1] - values[i] for i in range(3)]
    d2 = [d1[i + 1] - d1[i] for i in range(2)]
    d3 = d2[1] - d2[0]
    lead = d2[0] // 2
    linear = d1[0] - lead
    const = values[0]
    s = window[0]
    # re-express P(t), t = x - s, in terms of x
    return (lead, linear - 2 * lead * s, lead * s * s - linear * s + const), d3


def strip_cofactor(g):
    """Split g = modulus * cofactor, with the cofactor small.

    The modulus is prime and large; every other factor of g is small. So divide
    out small factors until what is left is prime.
    """
    remaining = g
    d = 2
    while d <= COFACTOR_BOUND and remaining > 1:
        if is_prime(remaining):
            return remaining
        if remaining % d == 0:
            remaining //= d
            continue
        d += 1 if d == 2 else 2
    return remaining


def solve(oracle_module=None, verbose=False):
    oracle_module = oracle_module or load_oracle()
    box = oracle_module.Oracle()

    hint = box.help()  # free; costs nothing, so there is no reason not to read it
    if verbose:
        print("hint:", hint[:60], "...")

    # ---- Phase A: four low probes -> the coefficients -------------------
    low_values = [box.evaluate(x) for x in LOW_WINDOW]
    (a, b, c), d3 = fit_integer_quadratic(LOW_WINDOW, low_values)
    if d3 != 0:
        # The window wrapped unevenly, so the second difference is not 2*lead and
        # the integer fit is meaningless. Refuse rather than proceed on a fit that
        # cannot be trusted -- the low window the plan uses never does this.
        raise RuntimeError(
            f"low window {LOW_WINDOW} has third difference {d3}; "
            "it does not admit an integer fit, probe lower"
        )
    if verbose:
        print(f"phase A: third difference = {d3} (window never wrapped)")
        print(f"phase A: coefficients (pre-reduction) a={a} b={b} c={c}")

    # ---- Phase B: two far probes -> the modulus -------------------------
    def fitted(x):
        return a * x * x + b * x + c

    far_values = []
    residues = []
    for x in FAR_PROBES:
        observed = box.evaluate(x)
        far_values.append(observed)
        residues.append(fitted(x) - observed)
    if verbose:
        print(f"phase B: residues are multiples of the modulus: {residues}")

    g = 0
    for r in residues:
        g = gcd(g, r)
    if g == 0:
        raise RuntimeError("far probes did not wrap; choose probes further out")
    modulus = strip_cofactor(abs(g))
    if verbose:
        print(f"phase B: gcd = {g}, cofactor = {abs(g) // modulus}, modulus = {modulus}")

    # ---- Phase C: canonicalise and verify -------------------------------
    a, b, c = a % modulus, b % modulus, c % modulus

    if not is_prime(modulus):
        raise RuntimeError(f"recovered modulus {modulus} is not prime")

    # Verify against what the box actually returned. Reconstructing the far
    # observations from the fit would be circular -- and the fit has since been
    # reduced, so it would not even reconstruct them correctly.
    probes = list(zip(LOW_WINDOW, low_values)) + list(zip(FAR_PROBES, far_values))
    for x, observed in probes:
        if (a * x * x + b * x + c) % modulus != observed:
            raise RuntimeError(f"recovered rule disagrees with the box at x={x}")

    spent = oracle_module._harness_spent()
    if verbose:
        print(f"phase C: verified against all {len(probes)} probes; "
              f"{spent}/{oracle_module.BUDGET} units spent")

    return {"m": modulus, "a": a, "b": b, "c": c}, spent


def main():
    answer, spent = solve(verbose="-v" in sys.argv)
    print(json.dumps(answer))
    print(f"# units spent: {spent}", file=sys.stderr)


if __name__ == "__main__":
    main()
