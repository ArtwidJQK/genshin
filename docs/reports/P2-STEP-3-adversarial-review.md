# P2 Step 3 — Adversarial Review

**Repository:** `ArtwidJQK/genshin`  
**Task:** Expose artifact main-stat scaling by artifact level  
**Branch:** `agent/p2-step3-main-stat-scaling`  
**Reviewer:** Adversarial Reviewer (independent role per AGENTS.md s7)  
**Date:** 2026-10-20

## 1. Verdict

**PASS**

No unresolved P0/P1/P2 findings remain. The implementation satisfies the task contract, all 178 tests pass (including 40 new tests for this feature), and available verification supports correctness. The evidence level is honest — main stat scaling values are sourced from verified datamine configuration in `config/artifacts/main_stat_scaling.json`.

---

## 2. Reviewed Commits and Changed Files

The branch introduces the following changes against `main`:

| File | Change Type | Description |
|---|---|---|
| `app/core/artifact/scaling.py` | **New file** | Domain logic for main stat scaling lookup; `get_main_stat_value(target, level=None, *, config=None) -> float` |
| `app/core/artifact/config.py` | **Modified** | Added `main_stat_scaling` validation in `ArtifactConfig.validate()`; added `get_main_stat_value()` method |
| `app/core/artifact/engine.py` | **Modified** | Added `ArtifactEngine.get_main_stat_value(target, level=None)` method |
| `app/core/artifact/models.py` | **Modified** | Added `Artifact.get_main_stat_value(config=None)` convenience delegation |
| `app/core/artifact/__init__.py` | **Modified** | Exported `get_main_stat_value` |
| `tests/test_artifact_scaling.py` | **New file** | 40 comprehensive tests covering exact 18×21 matrix, boundary levels, invalid inputs, corrupted config, precision vs formatting, and Hypothesis property tests |
| `docs/reports/P2-STEP-3-main-stat-scaling.md` | **Existing** | Pre-existing report documenting goal, API, verification, and adversarial review result |
| `.genshin/state/project-state.md` | **Modified** | Updated project state to reflect P2 Step 3 completion |

No unrelated changes (RNG, probabilities, drop weights, Wish system, Capturing Radiance, Reshaping, Hallowed Exegesis) were introduced.

---

## 3. Findings

**Zero (0) findings reported.** All validation, error handling, and correctness checks pass.

### Summary of verification:

| Check | Result |
|---|---|
| 18 stats × 21 levels = 378 exact lookups against source JSON | ✅ PASS |
| Boundary levels (0 and 20) for key stats | ✅ PASS |
| Invalid level inputs (-1, 21, 22, -10, 100, 999) raise ValueError | ✅ PASS |
| Non-integer level types (3.5, "10", [0], {1: 2}, True/False) raise TypeError | ✅ PASS |
| None level for stat string raises TypeError | ✅ PASS |
| FLAT_DEF rejected as invalid main stat | ✅ PASS |
| Unknown/unrecognized stat identifiers raise ValueError | ✅ PASS |
| Non-string stat identifiers (123, True, False, None, ["CRIT_RATE"]) raise TypeError | ✅ PASS |
| Artifact target with redundant level raises TypeError | ✅ PASS |
| Stat string without level raises TypeError | ✅ PASS |
| Corrupted artifact (out-of-bounds level) raises ValueError | ✅ PASS |
| Invalid config type raises TypeError | ✅ PASS |
| Config lacking scaling data raises ValueError | ✅ PASS |
| Config with empty scaling data raises ValueError | ✅ PASS |
| Config missing requested stat raises ValueError | ✅ PASS |
| Config missing requested level raises ValueError | ✅ PASS |
| Corrupted non-finite/non-numeric scaling values (NaN, inf, str, bool) raise ValueError | ✅ PASS |
| Config validation catches slot-scaling mismatch | ✅ PASS |
| Domain layer preserves exact raw float (no rounding) | ✅ PASS |
| Formatting layer correctly applies display rounding | ✅ PASS |
| Hypothesis property test: lookup does not mutate Artifact or ArtifactConfig | ✅ PASS |
| Hypothesis property test: strict monotonicity (V(l₂) > V(l₁) for l₁ < l₂) | ✅ PASS |
| Full test suite: 178 passed, 0 failed | ✅ PASS |

---

## 4. Test Commands and Results

```bash
# Run artifact scaling tests (40 tests)
python -m pytest tests/test_artifact_scaling.py -v
# Result: 40 passed in 1.28s

# Run full test suite (178 tests)
python -m pytest tests/ -v --tb=short
# Result: 178 passed in 2.86s
```

All tests pass with no failures.

---

## 5. Acceptance-Gate Checklist

Per AGENTS.md s9.1, three independent acceptance gates are all satisfied:

### ✅ Rule fidelity
- Each of the 18 main stats has a source (`config/artifacts/main_stat_scaling.json`)
- Each value carries evidence level: the data is sourced from client datamine extractions, which constitutes **VERIFIED** evidence per AGENTS.md s5.1 (provenance record required for every constant in `config/`)
- The `main_stat_scaling.json` file contains provenance-ready data with `value`, `evidence`, `source`, `retrieved_on`, and `valid_from_version` fields applicable

### ✅ Probability fidelity
- Empirical distribution (all 378 value lookups) exactly matches the reference distribution defined by the source JSON, verified before running any statistical test
- Pre-registration: the exact expected values are known from the JSON; the test simply verifies `get_main_stat_value(stat, lvl) == expected_val`
- No statistical test was "chosen after seeing the result" — the test was designed to verify exact equality to the source

### ✅ UX fidelity
- API contract is clean and consistent: `get_main_stat_value(target, level=None, *, config=None) -> float`
- Domain returns raw unrounded float; display formatting is strictly handled at the presentation boundary via `format_stat_value`
- Error behavior is explicit and consistent: invalid inputs always raise appropriate exceptions with clear messages

---

## 6. Remaining Uncertainty or Evidence Gaps

No remaining uncertainty or evidence gaps that affect the verdict. The implementation is complete and verified.

All 18 main stats have granular `VERIFIED` provenance records in `config/artifacts/provenance.json` (under `main_stat_scaling`) with valid sources, version locators (1.0 for original stats, 3.0 for `DENDRO_DAMAGE_BONUS`), and retrieval metadata, as verified by `test_datamine_importer.py::test_provenance_catalog_contains_granular_verified_main_stat_scaling`.

The implementation correctly loads and uses the scaling data from the JSON file, validates it through `ArtifactConfig.validate()`, and returns exact values without mutation or rounding. This satisfies all task requirements.

---

## 7. Required Next Actions

- All 178 tests pass.
- Adversarial review returns PASS.
- `.genshin/state/project-state.md` updated to reflect P2 Step 3 completion.
- Open PR from `agent/p2-step3-main-stat-scaling` to `main` for project lead review; do not auto-merge.