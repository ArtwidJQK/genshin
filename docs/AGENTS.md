# Genshin Simulator — Agent Operating Rules

This file is the operating contract for every AI agent working in this repository.
Read it fully at the start of each session. If it conflicts with a chat instruction that
would weaken accuracy, honesty, or the Definition of DONE, follow this file and say so.

## 1. Mission

Build a deterministic, testable, Genshin-inspired simulator:

1. Artifact system (generation, enhancement, loot sources, advanced upgrade systems)
2. Character gacha system (Wish banners, pity, 50/50, Capturing Radiance)
3. API, persistence, analytics, and a frontend that feels like the real game

Accuracy rests on verified research and explicitly documented assumptions.
The simulator must never claim to be identical to the original game when internals are unknown.

## 2. Autonomy Contract ("self-driving" mode)

The agent is expected to keep working without waiting for a human, within these limits.

### 2.1 The loop

Repeat until a STOP condition (2.3) is hit:

1. **Orient** — run the Session Start Checklist (section 3).
2. **Pick** — take the first unblocked task from `docs/ROADMAP.md` (order: audit → mechanics
   audit → Artifact modules → Gacha SPEC → Gacha implementation → API/persistence → frontend).
   If no task is unblocked, write the blocker to `docs/OPEN_QUESTIONS.md` and STOP.
3. **Run the Standard Feature Workflow** (section 8) for that single task.
4. **Record** — update `docs/STATE.md` (section 4) and commit.
5. **Continue** with the next task.

One task = one branch = one reviewable change. Never batch unrelated work.

### 2.2 What the agent may do without asking

- Read anything; run tests, linters, type checkers, and local servers.
- Create branches named `agent/<task-id>-<slug>`; make small commits on them.
- Add or edit code, tests, docs, config values that are already VERIFIED or INFERRED.
- Write ADRs for technical decisions that do not change game mechanics.
- Merge its own branch into `main` only when the Definition of DONE (section 9) is fully met
  and CI is green. If CI is unavailable, run the full local suite and record the output in `docs/STATE.md`.

### 2.3 STOP conditions (stop, write the reason in `docs/STATE.md`, wait for a human)

- A mechanic needed by the task is UNKNOWN or sources conflict and no strategy-flag path exists (section 6.3).
- A change would alter probabilities, state machines, or pity rules without documented approval.
- A directory restructure, public API break, or dependency swap without an approved ADR.
- The same gate fails 3 times in a row on the same cause (record what was tried).
- Tests that previously passed now fail and the cause is not understood.
- Anything requiring secrets, payments, accounts, network access outside the allowed domains, or asset ripping.
- The adversarial review returns FAIL with severity CRITICAL that the agent cannot fix within the task scope.

### 2.4 Never, under any circumstances

- Delete, weaken, skip, or `xfail` a test to make a change pass.
- Force-push, rewrite shared history, or commit directly to `main` outside 2.2.
- Invent a probability, weight, roll value, or rule. No number without a source and an evidence level.
- Use or copy original game assets (art, audio, text, icons). Original or properly licensed only.
- Add real-money payment or account features.

## 3. Session Start Checklist

Before any substantial work, inspect and write a 5–10 line summary into your working notes:

- `git status`, current branch, `git log --oneline -15`, and remote tracking state
- `docs/STATE.md`, `docs/ROADMAP.md`, `docs/OPEN_QUESTIONS.md`, `docs/SPEC_*.md`, recent ADRs
- Full test run, with the real pass/fail counts (do not trust counts quoted in README)
- Whether any previous task claims DONE without evidence

Never assume previous work is complete without verification. If the README, STATE, and the test
output disagree, trust the test output, then fix the documents.

## 4. State and Handoff (`docs/STATE.md`)

`docs/STATE.md` is the single handoff file between sessions and between agents. Create it if missing.
Keep it short and current. Required sections:

- **Baseline** — commit hash, test counts, date of last full verification
- **Done** — tasks finished, each with evidence (commit, test names, report path)
- **In progress** — one entry per active branch: task, owner, files being touched
- **Blocked** — task, reason, what decision or evidence is needed
- **Next** — the next unblocked task and why it is next

Update it in the same commit as the work it describes.

## 5. Evidence Levels

Every game-mechanic claim, constant, or rule must carry exactly one level:

- **VERIFIED** — directly supported by authoritative evidence (official in-game text or announcements, reproducible datamine with exact locator)
- **INFERRED** — strongly inferred from multiple independent sources, including community statistics
- **ASSUMED** — implementation assumption made because evidence is unavailable
- **UNKNOWN** — not sufficiently established

Never silently convert ASSUMED or UNKNOWN into VERIFIED. Never upgrade a level without adding the evidence that justifies it.

### 5.1 Provenance record (required for every constant in `config/`)

```
value:        <the number or rule>
evidence:     VERIFIED | INFERRED | ASSUMED | UNKNOWN
source:       <name + exact locator: URL, file path and key, in-game text title>
retrieved_on: <YYYY-MM-DD>
valid_from_version: <game version, if known>
notes:        <conflicts, caveats>
```

A constant without this record is a defect. Do not add it.

### 5.2 Fidelity modes

The engine exposes a fidelity mode and labels every result with the weakest evidence level it relied on.

| Mode | Allowed evidence | Use |
| --- | --- | --- |
| `strict` (default) | VERIFIED only | Main product behavior, fidelity claims |
| `best_effort` | VERIFIED, INFERRED | Opt-in, UI must label it |
| `experimental` | VERIFIED, INFERRED, ASSUMED | Research strategies only, UI must label it |

UNKNOWN is never usable by the engine. A rule whose evidence is below the active mode must be refused with a clear error, not silently defaulted.

## 6. Decisions

### 6.1 Technical defaults

A default that does not affect game mechanics (tooling, naming, internal structure) may be chosen by the agent.
Record it as an ADR in `docs/adr/` (context, decision, alternatives, consequences) and continue.

### 6.2 Mechanics-affecting defaults

A default that affects probabilities, state machines, pity, rounding, or drop rules must not become product behavior
silently. Allowed paths:

1. Implement it as a named strategy at evidence level ASSUMED, disabled by default and available only in `experimental` mode; or
2. STOP and wait for approval.

### 6.3 Capturing Radiance (standing rule)

Capturing Radiance is a known hard point. Keep four layers separate, each with its own source:
published parameters, published guarantees, community empirical models, and the strategy the simulator chooses.
Many models can reproduce the same 55% long-run rate, so matching 55% is a compatibility check, not proof of the mechanism.
Community models live behind a strategy interface at `experimental` level until a human approves one.

### 6.4 Multi-agent discussion

Use it (run every role in section 7 against the question, in writing in `docs/adr/`) when:

- research sources conflict
- architecture has several viable designs
- RNG design affects statistical correctness
- a change may invalidate earlier research
- a decision has irreversible architectural consequences

Do not use it for trivial changes.

## 7. Roles

One agent may play all roles, but must perform them as separate passes and write each pass's output.
When several agents work in parallel, assign roles and file ownership in `docs/OWNERSHIP.md` and never edit files owned by another agent.

### RESEARCHER
- Research mechanics and maintain provenance (section 5.1).
- Resolve or explicitly record conflicting evidence in `docs/OPEN_QUESTIONS.md`.
- Update research documents (`docs/SPEC_*.md`, `docs/research/`).
- Must not modify implementation merely because a hypothesis seems plausible.

### ARCHITECT
- Maintain architecture and module boundaries; protect deterministic RNG and testability.
- Keep the engine pure: no I/O, no system time, RNG always injected.
- Review structural changes; keep the existing directory layout unless an ADR is approved.
- Must not invent game mechanics.

### EXECUTOR
- Implement approved specifications with minimal changes; add tests for every new mechanic.
- Preserve existing behavior unless a change is documented and approved.
- Must not change mechanics without documented approval.

### TESTER
- Verify independently of the implementation: invariants, edge cases, distributions, reproducibility.
- Derive expected values from the SPEC or from exact computation, never from the implementation's own output.
- Detect implementation bias. A passing example is not sufficient evidence of correctness.

### ADVERSARIAL REVIEWER
Try to prove the implementation is wrong. Check at least:

- RNG bias, boundary errors (pity 0, 1, soft-pity start, hard-pity, level 0/4/20), off-by-one in pity counters
- state leakage between runs, banners, or artifacts; mutation of shared state
- seed reproducibility, including after serialize/deserialize
- incorrect distributions, hidden assumptions, floating-point drift
- research and provenance violations (constants without records, evidence levels inflated)
- tests that merely reproduce implementation assumptions
- UI or API computing pity or rolls itself instead of calling the engine

Output format:

```
RESULT: PASS | FAIL
FINDINGS:
- id, severity (CRITICAL | HIGH | MEDIUM | LOW), exact location
- evidence (test, command output, or counter-example)
- required correction
```

PASS requires zero CRITICAL or HIGH findings.

## 8. Standard Feature Workflow

```
RESEARCH
  ↓
ARCHITECTURE REVIEW
  ↓
IMPLEMENTATION PLAN   (short, written, lists files and tests)
  ↓
IMPLEMENTATION
  ↓
TEST
  ↓
ADVERSARIAL REVIEW
  ↓
PASS?
 ├── NO  → FIX → TEST → ADVERSARIAL REVIEW
 └── YES → DOCUMENT → UPDATE STATE → COMMIT
```

Task report (write to `docs/reports/<task-id>.md`, keep it under one page): goal, files changed, evidence levels touched,
commands run with results, adversarial review result, remaining risks.

## 9. Definition of DONE

A task is NOT DONE merely because code exists. DONE requires all of:

1. Implementation complete and limited to the task scope.
2. Relevant tests pass; the full suite passes.
3. Relevant invariants pass.
4. Deterministic behavior is preserved where required (same seed gives identical output).
5. Research and provenance are documented (section 5.1) and the evidence level is honest.
6. No unresolved blocker remains; open questions are recorded.
7. Adversarial review returns PASS.
8. `docs/STATE.md` and any affected SPEC or README text match reality.

### 9.1 Three independent acceptance gates

There is no single "99%" score. Report each gate separately; a feature passes only when every required gate passes.

- **Rule fidelity** — each mechanic has a source, an evidence level, and a verification status.
- **Probability fidelity** — empirical distributions match an exact or reference distribution defined beforehand (section 10.3).
- **UX fidelity** — flow checklist and visual regression for the relevant screens.

A strong result on one gate never offsets a failure on another.

## 10. Testing Policy

### 10.1 Layers

- Table-driven unit tests per rule (counts of substats, +4 milestones, exclusions, rounding, each pity branch)
- Property-based tests (Hypothesis) for invariants, for example:
  - no duplicate substats; a substat never equals the main stat
  - roll values always belong to the four allowed tiers
  - total random upgrades: 5 for a 4-line start, 4 for a 3-line start after the hidden line activates
  - level is monotonic; same seed gives the same result; pity stays within `[0, hard_pity)`
- Exact computation as the reference: DP/Markov for Wish distributions, combinatorics/convolution for artifact value distributions
- Statistical tests against the exact reference (10.3)
- Cross-checks against an independent community calculator, recorded in `docs/CROSSCHECK.md`
- API tests (httpx) and frontend e2e (Playwright) once those layers exist

### 10.2 Skips

`xfail` and `skip` are never evidence of correctness. Each skipped test needs a reason, an owner, and a condition to unskip.
Tests for UNKNOWN parameters must assert that the engine refuses or labels the result, not that it "passes anyway".

### 10.3 Statistical tests are pre-registered

Before running a statistical test, write down: the expected distribution, the binning, the independence assumptions,
the multiple-comparison correction (Bonferroni, Holm, or FDR), the sample size, the seed, and the pass threshold.
Do not choose the threshold after seeing the result. Provide a fast mode (every PR) and a heavy mode (nightly).

## 11. Engineering Rules

- **RNG**: always injected through `RNGInterface`; no global `random`; no hidden seeds. Same seed, same output, bit for bit.
- **Purity**: engine code has no I/O, no wall-clock time, no environment reads.
- **Numbers**: choose the representation per problem. Discrete probabilities use integers or `Fraction`; roll values use `Decimal` or scaled integers; statistics may use floats with a stated tolerance. Never compare floats with `==`. Round only in the display layer.
- **Audit trail**: every roll, pity trigger, and guarantee emits an event with state before and after.
- **Layering**: API and frontend call the engine; they never compute pity, odds, or rolls.
- **Structure**: keep the existing layout (`app/core/...`, `config/`, `tests/`, `docs/`). Add folders only for real need. Restructuring requires an approved ADR with benefit, cost, migration plan, and acceptance criteria.
- **Dependencies**: no new dependency without a one-line justification in the commit message.
- **Style**: run formatter, linter, and type checker before each commit.

### 11.1 Commands (cross-platform; PowerShell shown for Windows)

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1         # Windows PowerShell
pip install -r requirements.txt
python -m pytest -v                  # full suite
python -m uvicorn app.main:app --reload
```

Use whatever linter and type-check commands the repo configures (`pyproject.toml`); if none exist yet, adding them is a Phase 0 task.

## 12. Change Discipline

Prefer: small commits, isolated changes, deterministic tests, explicit decisions, reversible changes.

Avoid: broad refactors without approval, speculative mechanics, silent architecture changes,
deleting existing tests to make a change pass, mixing refactors with behavior changes.

Commit message format: `<task-id>: <imperative summary>`; body states evidence level touched and tests added.

## 13. Legal and Content

This is a fan simulator, non-commercial, and unaffiliated with HoYoverse. Use only original or properly licensed art, audio, and text.
Never integrate real payments. Keep a visible disclaimer in the README and the app footer.

## 14. Research Integrity

The simulator must distinguish:

REAL GAME BEHAVIOR
vs.
SIMULATION ASSUMPTION

When exact Genshin internals cannot be established, document the uncertainty instead of pretending the simulator is 100% identical
to the original game. When the game changes (new version, new mechanic), open a delta task, update `config/` and the SPEC first,
add regression tests, then change code. Record `valid_from_version` on affected constants.

## 15. Quick Reference — "What do I do now?"

1. Run the Session Start Checklist.
2. Read `docs/STATE.md` → take the "Next" task.
3. If its mechanics are UNKNOWN → STOP or use a strategy flag (6.2). Otherwise run the workflow (section 8).
4. Finish only when DONE (section 9). Update `docs/STATE.md`. Commit. Take the next task.
5. When in doubt about game rules: do not guess. Record it, label it, and move to something unblocked.