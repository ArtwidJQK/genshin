# Genshin Project State

**Audit Timestamp:** 2026-10-20T05:43:00+07:00
**Target Game Version:** Genshin Impact 7.1 ("A Rekviem for the Underworld", Released 2026-09-23)
**Local Repository:** `D:\side_project\genshin`
**Current Phase:** P3 Artifact Loot Sources (Completed & Committed to main; 201 tests passed)
**Canonical Roadmap:** `docs/PROJECT_PLAN.md` (Kế hoạch A–Z: Genshin Artifact & Wish Simulator)

---

## 1. Git & Repository Status

### Audited Repository State
- **GitHub main baseline:** `827482bdfad230cb8329beabc0257cb2590db799` (`feat(artifact): implement artifact loot sources, config, and 3-layer test suite`).
- **Current Local Branch:** `main` (synchronized with `origin/main`).
- **Working tree:** Post-P3.2 state reconciliation.
- **Remote main:** Up to date with `827482bdfad230cb8329beabc0257cb2590db799`.
- **Git policy:** Commits and pushes authorized by Project Lead. No unauthorized commits to `main`.

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
| **P2 Step 2: Formatter & Property Tests** | Display formatting boundary & Hypothesis invariants | `app/core/artifact/formatting.py`, `tests/test_artifact_properties.py`, `docs/adr/ADR-001-display-rounding.md` | 15 passed (`test_artifact_properties.py`: 15) | Level A / B Presentation Boundary | **VERIFIED & COMPLETED** |
| **P2 Step 3: Main-Stat Scaling** | Domain API exposing exact 21-level main stat curves | `app/core/artifact/scaling.py`, `app/core/artifact/config.py`, `tests/test_artifact_scaling.py` | 40 passed (`test_artifact_scaling.py`: 40) | Level B (Datamine Verified) | **VERIFIED & MERGED (PR #3)** |
| **P3: Artifact Loot Sources** | Domain of Blessing & Mystic Offering Strongbox; strict fidelity refusal; 3-layer decoupled test suite | `app/core/artifact/loot.py`, `config/artifacts/loot_sources.json`, `tests/unit/`, `tests/statistical/` | 23 passed (`test_loot_determinism.py`: 6, `test_loot_invariants.py`: 14, `test_loot_statistical.py`: 3) | Level A (Rules) / Level C (Empirical models) | **VERIFIED & GATE APPROVED BY PROJECT LEAD** |
| **P2: Character Gacha SPEC** | Pluggable Probability & State Machine Architecture | `docs/specs/p2_gacha_engine_spec.md`, `docs/SPEC_WISH.md` | Deterministic & Monte Carlo specs defined | Level A Facts vs Level C Empirical vs Simulator Choices | **AUDITED & CORRECTED** (Commit `5891919`) |
| **P2: Character Gacha Implementation** | Engine implementation (`app/core/gacha/`) | None (Directory not created) | 0 tests | N/A | **BLOCKED ON CAPTURING RADIANCE MODEL** |
| **Agent Infrastructure** | Operating rules, workflow roles, and tool skills | `AGENTS.md`, `.genshin/`, `.agents/skills/` | Verified static assets | Repo-local operating rules | **STATICALLY VERIFIED** |

**CI Status for P3.2 (`827482b`):** Pushed to origin/main; remote CI run pending. Last completed green CI run: `39309289931` on `1228624`.
**Overall Test Suite Status:** **201/201 passing automated tests, 2 warnings** (Fast suite: 200 passed in 35.25s; Heavy statistical test: 1 passed in 294.87s).

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

6. **Artifact Loot Sources (P3 Milestone):**
   - Domain of Blessing (20 Original Resin or 1 Condensed Resin): Level 90 domains drop guaranteed 1 5★ artifact plus Bernoulli trial ($p = 0.0654$) for 2nd; 4★ fodder count (2 baseline + 48% chance of 3rd); initial line count (80% 3-line vs 20% 4-line).
   - Condensed Resin Equivalence: Advances one single continuous PRNG stream across 2 sequential cycles; bit-for-bit identical to 2 consecutive normal runs on an un-reset RNG stream.
   - Mystic Offering Strongbox: 3:1 conversion ratio; strict input validation (list type, multiple of 3, minimum 3, rarity 5★ only, non-empty target set); initial line count (66% 3-line vs 34% 4-line).
   - Strict Fidelity Refusal: Calling `run_domain_of_blessing` or `craft_strongbox` in `STRICT` mode raises `FidelityViolationError` without silent fallback; catalog validation in `strict` mode rejects `INFERRED` constants in `loot_sources.json`.
   - Statistical Dual-Gate Verification: Fast Suite ($N = 100,000$, seed `20261020`) and Heavy Suite ($N = 1,000,000$, seed `20261021`) both independently passed Gate 1 (Bonferroni Chi-Square $M=3$) and Gate 2 ($4\sigma$ boundaries on both $N_{\text{art}}$ and $N_{\text{runs}}$).
   - Adversarial Review: Recorded as `PASS` (0 Critical, 0 High) in `docs/reports/P3-STEP-2-adversarial-review.md`.

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
   - **STATUS: RESOLVED IN P3** (Domain 80/20 & Strongbox 66/34 implemented and statistically verified).

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
- **P2 Gate (Artifact Foundation Scaling & Formatting):** **PASS (MERGED PR #3)**
- **P3 Gate (Artifact Loot Sources):** **PASS**
  - Rule fidelity verified: zero silent fallback in STRICT mode (`FidelityViolationError`).
  - Probability fidelity verified: dual-gate pre-registered statistical suite passes on both Fast ($N=100k$) and Heavy ($N=1M$) datasets.
  - Determinism verified: bit-for-bit replay from seed; global PRNG isolation.
  - Adversarial review verified: `docs/reports/P3-STEP-2-adversarial-review.md` verdict PASS.
- **Rule Fidelity Gate (v7.1 Delta):** **PASS**
- **Probability Fidelity Gate:** **PASS (Artifact Foundation & Loot Sources verified; Gacha pending Phase 5).**

---

## 6. Current Task and Next Step

- **Completed:** P3 Artifact Loot Sources implemented, verified, and committed (`827482bdfad230cb8329beabc0257cb2590db799`). 201 automated tests passing locally.
- **Review gates:** Full test suite (201 passed, 2 warnings) and `git diff --check` green. Adversarial review recorded as PASS (`docs/reports/P3-STEP-2-adversarial-review.md`).
- **Next authorized step:** Awaiting Project Lead directive for Phase P4 (Artifact Transmuter & Sanctifying Elixir) or P2 Gacha specification refinement. Capturing Radiance (`OQ-01`) and Reshaping / Hallowed Exegesis (`OQ-03`) remain strictly blocked.
- **Gacha implementation:** remains blocked on an approved Capturing Radiance model; do not invent a default.
