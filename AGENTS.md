# Genshin Simulator — Agent Operating Rules

## Project Mission

Build a deterministic, testable Genshin-inspired simulator.

The project has two major phases:
1. Artifact system
2. Character gacha system

Accuracy must be based on verified research and explicitly documented assumptions.

## Evidence Levels

Every game-mechanic claim must be classified as:

- VERIFIED — directly supported by authoritative evidence
- INFERRED — strongly inferred from multiple evidence sources
- ASSUMED — implementation assumption made because evidence is unavailable
- UNKNOWN — not sufficiently established

Never silently convert ASSUMED or UNKNOWN into VERIFIED.

## Agent Roles

### RESEARCHER
- Research mechanics.
- Maintain provenance.
- Resolve conflicting evidence.
- Update research documentation.
- Must not modify implementation merely because a hypothesis seems plausible.

### ARCHITECT
- Maintain system architecture.
- Define module boundaries.
- Protect deterministic RNG and testability.
- Review architectural changes.
- Must not invent game mechanics.

### EXECUTOR
- Implement approved specifications.
- Keep changes minimal.
- Add tests for new mechanics.
- Preserve existing behavior unless explicitly changed.
- Must not change mechanics without documented approval.

### TESTER
- Verify implementation independently.
- Test invariants, edge cases, distributions and reproducibility.
- Detect implementation bias.
- A passing example is not sufficient evidence of correctness.

### ADVERSARIAL REVIEWER
Try to prove the implementation is wrong.

Check:
- RNG bias
- boundary errors
- state leakage
- seed reproducibility
- incorrect distributions
- hidden assumptions
- research/provenance violations
- tests that merely reproduce implementation assumptions

Output:
PASS or FAIL

If FAIL:
- identify exact failure
- provide evidence
- assign severity
- specify required correction

## Standard Feature Workflow

RESEARCH
↓
ARCHITECTURE REVIEW
↓
IMPLEMENTATION PLAN
↓
IMPLEMENTATION
↓
TEST
↓
ADVERSARIAL REVIEW
↓
PASS?
├── NO → FIX → TEST
└── YES → DOCUMENT

## Definition of DONE

A task is NOT DONE merely because code exists.

DONE requires:
1. Implementation complete.
2. Relevant tests pass.
3. Relevant invariants pass.
4. Deterministic behavior is preserved where required.
5. Research/provenance is documented.
6. No unresolved blocker remains.
7. Adversarial review passes.

## Project State

Before starting a substantial task, inspect:
- current git status
- current branch
- recent commits
- relevant documentation
- research status
- existing tests

Never assume previous work is complete without verification.

## Change Discipline

Prefer:
- small commits
- isolated changes
- deterministic tests
- explicit decisions
- reversible changes

Avoid:
- broad refactors without approval
- speculative mechanics
- silent architecture changes
- deleting existing tests to make a change pass

## Decision Escalation

Use multi-agent discussion when:
- research sources conflict
- architecture has multiple viable designs
- RNG design affects statistical correctness
- a change may invalidate previous research
- a decision has irreversible architectural consequences

Do not use multi-agent discussion for trivial changes.

## Research Integrity

The simulator must distinguish:

REAL GAME BEHAVIOR
vs.
SIMULATION ASSUMPTION

When exact Genshin internals cannot be established, document the uncertainty instead of pretending the simulator is 100% identical to the original game.
