"""task-01 oracle.

A black box holding one fixed arithmetic rule. Three surfaces:

    evaluate(x)   deterministic, exact, costs 1 unit of a 6-unit allowance
    help()        a fixed free hint, costs nothing
    sample()      an uncalibrated internal reading, costs 1 unit

The allowance is shared per interpreter. Constructing another Oracle does not
refill it, and neither does importing this file a second time. Spend it
deliberately.

Stdlib only. No network, no files, no configuration.

---------------------------------------------------------------------------
A note to whoever is reading this file rather than probing the box:

The parameters below are wrapped in an envelope so that they are not sitting in
this source as decimal literals. That is *obfuscation, not secrecy* -- anyone who
runs the unwrapping code gets the values, and no claim to the contrary is made
here. The envelope exists to stop an accidental glance from spoiling the task,
not to defeat a determined reader.

If you are solving this task: reading the internals is not the task, and it
teaches you nothing you were asked to find out. The investigation is the point.
---------------------------------------------------------------------------
"""

import hashlib
import random
import sys

DOMAIN_MIN = 0
DOMAIN_MAX = 1_000_000
BUDGET = 6

_ENVELOPE = "56815be5ff237132800599db161e36d81d3fd02aa8c648a5adca4bd041bc5fc1"
_ENVELOPE_KEY = b"project-chem/task-01/parameter-envelope"
_NOISE_SEED = 20260920


class BudgetExhausted(RuntimeError):
    """Raised when a priced surface is called with no allowance left."""


class OutOfDomain(ValueError):
    """Raised when evaluate() is given an input outside the stated domain."""


def _unwrap():
    raw = bytes.fromhex(_ENVELOPE)
    stream = b""
    counter = 0
    while len(stream) < len(raw):
        stream += hashlib.sha256(_ENVELOPE_KEY + counter.to_bytes(4, "big")).digest()
        counter += 1
    clear = bytes(r ^ s for r, s in zip(raw, stream))
    return tuple(int.from_bytes(clear[i * 8:(i + 1) * 8], "big") for i in range(4))


_M, _A, _B, _C = _unwrap()

# Process-wide state, parked on `sys` rather than on this module.
#
# Module level is not enough: importing this file twice (a second
# importlib.util.spec_from_file_location, say) produces two module objects with
# two independent counters, and the allowance doubles. Anchoring the state to
# `sys` -- which exists once per interpreter however many times this file is
# loaded -- makes the budget survive re-import as well as re-instantiation.
_STATE_KEY = "_task01_oracle_state"


def _state():
    st = getattr(sys, _STATE_KEY, None)
    if st is None:
        st = {"spent": 0, "noise": random.Random(_NOISE_SEED)}
        setattr(sys, _STATE_KEY, st)
    return st


_HINT = (
    "evaluate(x) is deterministic and exact: the same input always returns the same "
    "output, and the output is never approximate. Two cautions, both free. "
    "First: fitting your observations is not the same as being forced by them. Before "
    "you commit to an answer, ask whether some other rule could have produced exactly "
    "the evidence you are holding -- if one could, you have not finished, however neat "
    "your fit looks. Second: the allowance is spent, never refunded, and there is no "
    "reserve. Decide what a probe is for before you spend it."
)


def _charge():
    st = _state()
    if st["spent"] >= BUDGET:
        raise BudgetExhausted(
            f"allowance exhausted: {BUDGET} of {BUDGET} units spent"
        )
    st["spent"] += 1


def _rule(x):
    return (_A * x * x + _B * x + _C) % _M


class Oracle:
    """The black box. Construct freely; the allowance is shared, not per-instance."""

    def evaluate(self, x):
        """Return the box's output for integer input x. Costs 1 unit.

        Raises OutOfDomain for a non-integer or out-of-range input, without
        charging -- a rejected query buys no information, so it buys no cost.
        """
        if isinstance(x, bool) or not isinstance(x, int):
            raise OutOfDomain("input must be an integer")
        if not (DOMAIN_MIN <= x <= DOMAIN_MAX):
            raise OutOfDomain(
                f"input must satisfy {DOMAIN_MIN} <= x <= {DOMAIN_MAX}"
            )
        _charge()
        return _rule(x)

    def help(self):
        """Return a fixed hint. Free, and identical on every call."""
        return _HINT

    def sample(self):
        """Return one uncalibrated internal reading. Costs 1 unit.

        Seeded, so a given run reproduces. The reading carries a perturbation
        and is flagged as uncalibrated; it is not a substitute for evaluate().
        """
        _charge()
        rng = _state()["noise"]
        x = rng.randrange(DOMAIN_MIN, DOMAIN_MAX + 1)
        # Magnitude is never zero: an accidentally exact reading would be a free
        # probe, and a surface that is a gift once every few thousand calls is a
        # surface that is a gift.
        drift = rng.choice((-1, 1)) * rng.randrange(1, 4097)
        return {"input": x, "reading": _rule(x) + drift, "calibrated": False}


def _harness_reset():
    """Reset the allowance and the noise stream. For scripts/checks.py only.

    Not part of the box's interface and not something a solve may call: using it
    to buy extra probes is not a solution, it is a refusal to do the task.
    """
    setattr(sys, _STATE_KEY, {"spent": 0, "noise": random.Random(_NOISE_SEED)})


def _harness_spent():
    """Units spent so far. For scripts/checks.py only; not part of the interface."""
    return _state()["spent"]
