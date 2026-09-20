# CHEMCLAUDE.md — Project Chem Inverse-Task Authoring Guide

> Drop this file in your working folder and point Claude Code at it. It is self-contained:
> a fresh agent with no prior knowledge of Project Chem can execute it cold. No network,
> no API keys, no external reference files.

---

## 0. What this is

You (the human) are running Claude Code in a clean PowerShell on Windows to author **one
inverse task** for your own practice. This file tells Claude Code everything it needs. Work
happens entirely inside one folder and cleans up after itself.

---

## 1. The mental model (read this first, Claude)

An **inverse task** is a small investigation, not a normal task with the answer hidden. The
solver sees the *evidence* produced by a hidden system and must recover the hidden *rule*.

**Canonical example:** a black box computes `(a*x + b) mod 97`; the solver must recover the
pair `(a, b)` by probing it. Design your own hidden rule in the same spirit — a small
integer/modular system with a clean, unique answer.

A task is **well-built** only when all four of these hold:

1. The **intended solver passes** (recovers the answer within budget).
2. A **naive shortcut fails** (falls into a real reasoning trap).
3. **Nothing leaks** — the solver-facing prompt never names the answer.
4. The task is **hard but fair** — a strong model at 8 attempts lands **≤ 2/8**.

---

## 2. Human setup (run once in PowerShell)

```powershell
$root = "$HOME\project-chem\task-01"
New-Item -ItemType Directory -Force -Path `
  "$root\oracle","$root\solution","$root\grader","$root\golden","$root\scripts","$root\.scratch" | Out-Null
Copy-Item .\CHEMCLAUDE.md $root -ErrorAction SilentlyContinue
Set-Location $root
claude
```

Then paste into Claude Code:

> Read CHEMCLAUDE.md in this folder and execute it. Work only inside this directory.
> Start at Section 4, Step 1, and show me STATE.md before moving on.

---

## 3. Hard rules for Claude Code

- **Work only inside this directory.** Use `.scratch/` for throwaway work and delete it when done.
- **Lock the answer before writing anything the solver will read.** This is the single most
  important rule. Grading, the oracle, the leak-free prompt, and the failing shortcut all
  depend on it.
- **Do not write `problem.md` until the final authoring step.** Writing it early is how
  answers leak.
- **Stdlib only. No network, no API keys, no config.** Every check must run offline.
- **One step at a time.** Finish and show each artifact before moving to the next.
- **Red-team your own work before declaring it done.** See Section 6b. Be ruthless with
  yourself — a task that hasn't survived a hostile review of its own weak points is not finished.
- **Leave the folder clean.** Only the real artifacts remain at the end — no scratch files,
  no `__pycache__`.

---

## 4. Authoring sequence (follow the order exactly)

### Step 1 — Lock the answer
Write **`STATE.md`** containing:
- the committed answer (the hidden rule and its parameters),
- the order of design decisions,
- a **"why this is the only answer"** section proving uniqueness.

Write **`golden/expected.json`** with the locked answer in machine-readable form.
Nothing solver-facing exists yet. **Show STATE.md to the human before continuing.**

### Step 2 — Top-down brief
Write **`BRIEF.md`** — a top-down summary of the task: what the hidden system is, what the
solver must recover, the query budget, and the difficulty target.

### Step 3 — Grading first
Write **`grader/grading_guide.md`** with a **near-miss table**: candidate answers that are
close to correct and the precise reason each one is wrong. Grading is defined *against the
locked answer*, never reverse-engineered from a prompt.

### Step 4 — The hidden system
Write **`oracle/oracle.py`** exposing **exactly three surfaces**:

| Surface | Behavior | Budget |
|---|---|---|
| `evaluate(x)` | returns an output for input `x` | spends 1 unit of a fixed budget (use **6**) |
| `help()` | a free hint that **never names or reveals** the answer | free |
| `sample()` | an internal **seeded** noisy reading | spends budget |

The `sample()` surface is **deliberately NOT advertised** to the solver. Seed it so runs are
reproducible.

### Step 5 — The two solvers
- **`solution/main.py`** — the intended solver. Must recover the answer **within budget** and PASS.
- **`solution/shortcut.py`** — a plausible naive approach that must **FAIL**.
- **`reasoning_trap.md`** — explain the trap the shortcut falls into (e.g. a line-fit that
  ignores the modulus, so it fits the visible points but predicts wrong once the modulus wraps).

### Step 6 — The seen surface (last)
**Only now** write **`problem.md`** — the solver-facing prompt. It:
- exposes the evidence and how to probe the system,
- states the query budget,
- **never names the answer**,
- **deliberately omits** the `sample()` surface.

---

## 5. Requirements checklist (Claude self-verifies before declaring done)

- [ ] Answer locked (`STATE.md` + `expected.json`) **before** `problem.md` exists.
- [ ] `problem.md` and `help()` never name the answer.
- [ ] `shortcut.py` fails on a **real** reasoning trap; `main.py` passes within budget.
- [ ] `evaluate()` and `sample()` spend budget; `help()` is free; `sample()` is seeded.
- [ ] Intended solver passes; strong model × 8 should land **≤ 2/8**.
- [ ] Folder contains only real artifacts (no scratch, no `__pycache__`).

---

## 6. Build the calibration harness

Write **`scripts/checks.py`** (stdlib only) with these subcommands, each printing a clear
**PASS/FAIL** line:

| Subcommand | What it does | Expected |
|---|---|---|
| `verify` | runs `main.py` against the oracle, asserts it recovers `expected.json` | **PASS** |
| `shortcut` | runs `shortcut.py`, asserts it does **not** recover the answer | **FAIL (as intended)** |
| `lint` | scans `problem.md` for any leak of the answer | **CLEAN** |
| `preview` | reports the intended difficulty target | **≤ 2/8** |
| `selftest` | runs all four and asserts the expected outcomes | all green |

---

## 6b. Adversarial self-critique (Claude does this before the human runs anything)

Before you declare the task done, stop and **red-team your own work without mercy.** Assume a
skeptical reviewer is trying to prove your task is broken, and beat them to every finding.
Praise is worthless here; only defects are useful. Do not be kind to yourself — be *correct*.

Go artifact by artifact and attack it:

- **The answer.** Is it *actually* unique? Try to construct a second `(a, b)`-style pair that
  produces identical evidence within the budget. If one exists, your task is broken — fix the
  design, not the wording.
- **The leak.** Re-read `problem.md`, `help()`, and `BRIEF.md` as an adversary hunting for the
  answer. Does any example, hint, edge case, or offhand phrase narrow the answer space? A
  partial leak is still a leak.
- **The shortcut.** Is the trap *real*, or did you make the shortcut fail on purpose by
  crippling it? A fair naive solver — the one a competent person would actually try first —
  must fail for a *principled* reason (e.g. it ignores the modulus), not because you sabotaged
  it. If a slightly smarter shortcut would pass, your difficulty target is a lie.
- **The intended solver.** Does `main.py` win *within budget*, or is it quietly over-spending?
  Would it still pass if the seed changed? If it only works on one lucky seed, it's fragile.
- **The budget.** Can the whole system be brute-forced inside the 6-query budget? If the answer
  space is small enough to sweep, the investigation is fake. Widen it.
- **The oracle.** Does `sample()` stay hidden from the solver-facing prompt? Does `help()`
  leak under repeated calls? Is anything reproducible-by-accident that shouldn't be?
- **The grading.** Does the near-miss table actually catch the *most tempting* wrong answers,
  or only obvious ones? Add the near-misses a real solver would land on.

Write your findings to **`.scratch/critique.md`** as a blunt defect list — no hedging, no
"this is mostly fine." For every defect, either **fix it** or record why it's acceptable.
Then run Section 6's checklist again from scratch. **Only after this pass survives its own
cruelty do you tell the human it's ready.** Iterate — a first draft that passes its own
red-team on the first try almost certainly wasn't attacked hard enough.

---

## 7. The calibration gate (human runs this)

```powershell
python scripts\checks.py verify     # intended solver PASSES
python scripts\checks.py shortcut   # naive solver FAILS
python scripts\checks.py lint       # CLEAN — prompt names no answer
python scripts\checks.py preview    # difficulty <= 2/8
python scripts\checks.py selftest   # all four asserted at once
```

Use `python`, not `python3` — PowerShell resolves `python` on Windows. If any signal lands
wrong, paste the output back to Claude Code and have it fix the **specific** artifact, not
rewrite everything.

---

## 8. Cleanup (human runs this at the end)

```powershell
Remove-Item -Recurse -Force "$root\.scratch" -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include __pycache__ -Directory | Remove-Item -Recurse -Force
```

The finished folder now holds only the real task artifacts.

---

## 9. Final artifact layout

```
task-01/
├─ CHEMCLAUDE.md            (this file)
├─ STATE.md                 (locked answer + uniqueness proof)
├─ BRIEF.md                 (top-down summary)
├─ problem.md              (solver-facing prompt — written LAST)
├─ reasoning_trap.md        (the trap the shortcut falls into)
├─ oracle/
│  └─ oracle.py             (evaluate / help / hidden seeded sample)
├─ solution/
│  ├─ main.py               (intended solver — PASSES)
│  └─ shortcut.py           (naive solver — FAILS)
├─ grader/
│  └─ grading_guide.md      (near-miss table)
├─ golden/
│  └─ expected.json         (locked answer, machine-readable)
└─ scripts/
   └─ checks.py             (verify / shortcut / lint / preview / selftest)
```

**The one instruction that matters most:** lock the answer before writing anything the solver
reads. Everything downstream depends on that ordering.
