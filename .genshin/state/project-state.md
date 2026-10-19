# Genshin Project State

**Audit Timestamp:** 2026-10-20
**Target Game Version:** Genshin Impact 7.1 ("A Rekviem for the Underworld", Released 2026-09-23)
**Local Repository:** `D:\side_project\genshin`
**Current Phase:** P2 Artifact Core (Step 2 — formatter/property tests; CI PASS, merge pending)
**Canonical Roadmap:** `docs/PROJECT_PLAN.md` (Kế hoạch A–Z: Genshin Artifact & Wish Simulator)

---

## 1. Git & Repository Status

### Audited Repository State
- **GitHub main baseline:** da26d5e3acceb54454a74515ad251d122cd3fcd3 (docs(state): reconcile project state after P2 Step 1 commit).
- **Task branch:** agent/p2-step2-artifact-formatting (Step 2 changes isolated here).
- **Local Windows working tree:** Not observable through the GitHub connector; verify local status before syncing the branch.
- **Remote main:** Not modified by this task while implementation and CI review are pending.
- **Git policy:** Project Lead has authorized project continuation and Git commits/pushes; do not bypass review or merge while CI is failing.

---

## 2. Milestone & System Status

| Milestone | Scope | Technical Components | Automated Tests | Epistemological Status | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0: Foundation & Audit** | RNG & Probability primitives; Repo consolidation | `app/core/rng/`, `app/core/probability/`, `pyproject.toml`, `LICENSE`, CI | 33 passed (`test_rng.py`: 14, `test_probability.py`: 19) | Level A/Self | **VERIFIED & CONSOLIDATED** |
| **P1: Sổ đặc tả và dữ liệu** | Data schemas, provenance catalog, fidelity modes, specs, open questions & datamine importer | `app/core/artifact/schema.py`, `config/artifacts/provenance.json`, `docs/SPEC_ARTIFACT.md`, `docs/SPEC_WISH.md`, `docs/OPEN_QUESTIONS.md`, `tools/import_artifact_datamine.py`, `tests/fixtures/datamine/` | 20 passed (`test_config_schema.py`: 10, `test_datamine_importer.py`: 10) | Level A / B / C Provenance Classified | **VERIFIED & GATE APPROVED FOR CLOSURE BY PO** |
| **Artifact Foundation v1** | 5★ Artifact Domain Model, Generation & Enhancement Engine | `app/core/artifact/`, `config/artifacts/` | 69 passed (`test_artifact.py`: 69, `test_api.py`: 1) | Level A / Level B / Level C (Empirical) | **VERIFIED & SIGNED OFF** |
| **P1.5: Artifact Research Validation** | Provenance Catalog & Claim Matrix for Artifact Mechanics | `docs/research/artifact_validation.md` | N/A (Documentation & Claim Audit) | Level A–D Classified | **VERIFIED & SIGNED OFF** |
| **Mechanics Delta Audit (v7.1)** | Delta matrix for v7.1 "A Rekviem for the Underworld" | `docs/research/version_7_1_mechanics_delta.md` | N/A (Official HoYoverse Notices Audit) | Level A–C Classified | **VERIFIED & COMPLETE** (No mechanics change found) |
| **P2 Step 1: Datamine Importer** | 5★ Main-stat scaling & Substat roll tiers extraction | `tools/import_artifact_datamine.py`, `config/artifacts/main_stat_scaling.json`, `tests/fixtures/datamine/` | 10 passed (`test_datamine_importer.py`: 10) | Level B (Datamine Verified) | **VERIFIED & COMPLETED** |
| **P2: Character Gacha SPEC** | Pluggable Probability & State Machine Architecture | `docs/specs/p2_gacha_engine_spec.md`, `docs/SPEC_WISH.md` | Deterministic & Monte Carlo specs defined | Level A Facts vs Level C Empirical vs Simulator Choices | **AUDITED & CORRECTED** (Commit `5891919`) |
| **P2: Character Gacha Implementation** | Engine implementation (`app/core/gacha/`) | None (Directory not created) | 0 tests | N/A | **BLOCKED ON CAPTURING RADIANCE MODEL** |
| **Agent Infrastructure** | Operating rules, workflow roles, and tool skills | `AGENTS.md`, `.genshin/`, `.agents/skills/` | Verified static assets | Repo-local operating rules | **STATICALLY VERIFIED** |

**P2 Step 2 CI:** 138 passed, 1 Starlette deprecation warning on Python 3.11 (1.96s) and 138 passed, 1 Starlette deprecation warning on Python 3.12 (2.28s). GitHub Actions run 39294411756 succeeded for both matrix jobs.

---

## 3. Verified Artifacts & Evidence

1. **RNG Isolation & Determinism (P0):**
   - All stochastic calls route strictly through `RNGInterface` (`PythonRNG`). Python's global `random` state is completely isolated.
   - Seeded replay produces identical generation sequences and enhancement histories.

2. **Artifact Domain Mechanics (P1):**
   - 4 conceptual substat slots invariant enforced on `Artifact` dataclass.
   - 3-line base artifacts initialize slot 4 as `INACTIVE`; milestone +4 activates it without rolls or stat replacement.
   - 4-line base artifacts initialize all 4 slots as `ACTIVE`; milestone +4 performs 1 upgrade roll.
   - Milestones +8, +12, +16, +20 perform exactly 1 upgrade roll each.
   - Non-milestone intermediate levels (e.g. 0 → 6 → 10 → 15 → 20) only trigger crossed milestones.

3. **Version 7.1 Mechanics Delta Audit:**
   - Completed source-backed delta report: `docs/research/version_7_1_mechanics_delta.md`.
   - Verified that Version 7.1 introduced new artifact sets and UI "Set Lock Plans", but made zero changes to 5★ artifact RNG, enhancement milestones, or Character Event Wish rates/pity/guarantees.
   - Reconfirmed that `docs/specs/p2_gacha_engine_spec.md` requires zero changes.

4. **P0 Repository Consolidation (Master Execution Directive):**
   - Normalized canonical roadmap: `docs/PROJECT_PLAN.md`.
   - Reconciled `README.md` test counts from 67/87 to the true verified count of 93.
   - Added project metadata, tool configuration, and warning filters: `pyproject.toml`.
   - Added `LICENSE` (MIT License with fan-made non-commercial disclaimer).
   - Added GitHub Actions CI workflow: `.github/workflows/ci.yml`.

5. **Datamine Importer & Main Stat Scaling (P2 Step 1 / P1 Requirement):**
   - Offline importer `tools/import_artifact_datamine.py` supporting `--check` dry-run mode and `--input-dir`.
   - Complete 21-level curves (0–20) for all 18 valid main stats extracted into `config/artifacts/main_stat_scaling.json`.
   - Strict monotonicity ($V(l+1) > V(l)$) and boundary anchors verified for all 18 stats.
   - `FLAT_DEF` confirmed strictly excluded from main stats and preserved in substats.
   - 5★ substat roll tiers in depot 501 verified against ratio bounds $0.70/0.80/0.90/1.00$ within $\pm 0.005$ tolerance.
   - Granular `VERIFIED` provenance records added non-destructively to `config/artifacts/provenance.json`.

---

## 4. Gaps & Unresolved Questions

1. **Capturing Radiance Mathematical Implementation:**
   - **STATUS: BLOCKED FROM DEFAULT ENGINE** (Strategy Isolation Required).
   - HoYoverse disclosed only external parameters ($0.018\%$ base, $55\%$ consolidated, 3-loss guarantee).
   - A naive static Bernoulli model produces $\approx 51.7\%$, not $55\%$.
   - The concrete model remains an empirical hypothesis. Production core engine remains isolated behind `CapturingRadianceModel` abstract interface.
2. **Hallowed Exegesis Threshold Milestones (Reshaping):**
   - **STATUS: BLOCKED** (Do not implement Reshaping while community sources conflict: 6/12/18 vs 12/16).
3. **Multi-Source Artifact Line Count:**
   - **STATUS: ISOLATED TO DOMAIN DROPS** ($80/20$). Strongbox/Bosses ($66/34$) to be addressed in P3.

---

## 5. Gate Status

- **P0 Gate (Kiểm toán và củng cố repo):** **PASS**
  - Test suite passes 100% (123/123 passed, 2 warnings, 0 failures, 0 skips).
  - README reconciled with verified reality.
  - Table 6.0 mapping confirmed with evidence.
  - Directory structure preserved.
  - Canonical roadmap `docs/PROJECT_PLAN.md` explicitly approved by PO (Art) and merged into `main`.
- **P1 Gate (Sổ đặc tả và dữ liệu):** **APPROVED FOR CLOSURE BY PROJECT LEAD (PASS)**
  - Zero constants without provenance records (`config/artifacts/provenance.json`).
  - All UNKNOWN parameters cataloged in `docs/OPEN_QUESTIONS.md`.
  - Tests verify that engine refuses unverified rules in `strict` fidelity mode, and UNKNOWN in all modes (`tests/test_config_schema.py`).
  - Core specification books established: `docs/SPEC_ARTIFACT.md` and `docs/SPEC_WISH.md`.
  - Datamine importer requirement (`docs/PROJECT_PLAN.md:166`) fully satisfied by `tools/import_artifact_datamine.py` and verified by automated tests (`tests/test_datamine_importer.py`).
  - 18 main stat scaling curves and 40 substat roll values verified against client datamine sources.
- **Rule Fidelity Gate (v7.1 Delta):** **PASS**
  - Full source inventory and delta matrix documented.
  - Tier A official rules separated from Tier C empirical models.
- **Probability Fidelity Gate:** **PASS (Artifact Foundation uniform upgrade target & roll tier chi-square pre-registered tests verified); PENDING PHASE 5 for Gacha.**

---

## 6. Current Task and Next Step

- **In progress:** P2 Step 2 — separate display formatting from internal value accumulation and add property-based tests for artifact slot, generation, enhancement, and determinism invariants.
- **Review gates:** CI passed on Python 3.11 and 3.12; adversarial review PASS recorded in docs/reports/P2-STEP-2-artifact-formatter.md. Merge the task branch after this report/state commit also passes CI.
- **Next after this gate:** Finish remaining P2 core work by exposing and testing the imported main-stat value curve for the artifact's current level; then continue to P3 source-specific loot rules (Domain first) and Strongbox as a separate researched module. Do not implement Reshaping while OQ-03 remains blocked.
- **Gacha implementation:** remains blocked on an approved Capturing Radiance model; do not invent a default.
