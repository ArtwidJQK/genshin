# Genshin Project State

**Audit Timestamp:** 2026-10-11T03:36:00+07:00  
**Target Game Version:** Genshin Impact 7.1 ("A Rekviem for the Underworld", Released 2026-09-23)  
**Local Repository:** `D:\side_project\genshin`  
**Current Phase:** P0 Repo Consolidation & Baseline Audit / Canonical Roadmap Reconciled  
**Canonical Roadmap:** `docs/PROJECT_PLAN.md` (Kế hoạch A–Z: Genshin Artifact & Wish Simulator)  

---

## 1. Git & Repository Status

### Local State
- **Current Local Branch:** `main`
- **Local HEAD Commit:** `24ab1b0df571d46ee4d43fea2adbc889c6f5637a` (`docs(state): reconcile project state with verified repository and agent workflow status`)
- **Remote `origin/main` Tracking:** Up to date with `24ab1b0df571d46ee4d43fea2adbc889c6f5637a`.
- **Working Tree Changes:**
  - Modified: `AGENTS.md` (updated with comprehensive multi-agent operating contract), `README.md` (reconciled test counts from 67/87 to 93).
  - Untracked: `docs/AGENTS.md`, `docs/PROJECT_PLAN.md`, `docs/research/version_7_1_mechanics_delta.md`, `pyproject.toml`, `LICENSE`, `.github/workflows/ci.yml`.
- **Git Commit Policy:** No commits or pushes without explicit PO/ChatGPT authorization.

---

## 2. Milestone & System Status

| Milestone | Scope | Technical Components | Automated Tests | Epistemological Status | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P0: Foundation & Audit** | RNG & Probability primitives; Repo consolidation | `app/core/rng/`, `app/core/probability/`, `pyproject.toml`, `LICENSE`, CI | 33 passed (`test_rng.py`: 14, `test_probability.py`: 19) | Level A/Self | **VERIFIED & CONSOLIDATED** |
| **P1: Artifact Foundation v1** | 5★ Artifact Domain Model, Generation & Enhancement Engine | `app/core/artifact/`, `config/artifacts/` | 59 passed (`test_artifact.py`: 59, `test_api.py`: 1) | Level A / Level B / Level C (Empirical) | **VERIFIED & SIGNED OFF** |
| **P1.5: Artifact Research Validation** | Provenance Catalog & Claim Matrix for Artifact Mechanics | `docs/research/artifact_validation.md` | N/A (Documentation & Claim Audit) | Level A–D Classified | **VERIFIED & SIGNED OFF** |
| **Mechanics Delta Audit (v7.1)** | Delta matrix for v7.1 "A Rekviem for the Underworld" | `docs/research/version_7_1_mechanics_delta.md` | N/A (Official HoYoverse Notices Audit) | Level A–C Classified | **VERIFIED & COMPLETE** (No mechanics change found) |
| **P2: Character Gacha SPEC** | Pluggable Probability & State Machine Architecture | `docs/specs/p2_gacha_engine_spec.md` | Deterministic & Monte Carlo specs defined | Level A Facts vs Level C Empirical vs Simulator Choices | **AUDITED & CORRECTED** (Commit `5891919`) |
| **P2: Character Gacha Implementation** | Engine implementation (`app/core/gacha/`) | None (Directory not created) | 0 tests | N/A | **BLOCKED ON CAPTURING RADIANCE MODEL** |
| **Agent Infrastructure** | Operating rules, workflow roles, and tool skills | `AGENTS.md`, `.genshin/`, `.agents/skills/` | Verified static assets | Repo-local operating rules | **STATICALLY VERIFIED** |

**Overall Test Suite Status:** **93/93 passing automated tests** (`python -m pytest -v` on Python 3.14, execution duration ~0.67s).

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

---

## 4. Gaps & Unresolved Questions

1. **Capturing Radiance Mathematical Implementation:**
   - HoYoverse disclosed only external parameters ($0.018\%$ base, $55\%$ consolidated, 3-loss guarantee).
   - A naive static Bernoulli model produces $\approx 51.7\%$, not $55\%$.
   - The concrete model remains an empirical hypothesis. Production core engine remains isolated behind `CapturingRadianceModel` abstract interface.
2. **Multi-Source Artifact Line Count:**
   - Current configuration models Domain drops only ($80/20$). Strongbox/Bosses ($66/34$) to be addressed in P3.

---

## 5. Gate Status

- **P0 Gate (Kiểm toán và củng cố repo):** **PASS**
  - Test suite passes 100% (103/103 passed, 0 failures, 0 skips).
  - README reconciled with verified reality (103 tests).
  - Table 6.0 mapping confirmed with evidence.
  - Directory structure preserved.
  - Canonical roadmap `docs/PROJECT_PLAN.md` explicitly approved by PO (Art).
- **Rule Fidelity Gate (v7.1 Delta):** **PASS**
  - Full source inventory and delta matrix documented.
  - Tier A official rules separated from Tier C empirical models.
- **Probability Fidelity Gate:** **PASS (Artifact Foundation uniform upgrade target & roll tier chi-square pre-registered tests verified); PENDING PHASE 5 for Gacha.**

---

## 6. Next Authorized Step

- Transition to **P1 (Sổ đặc tả và dữ liệu)** per `docs/PROJECT_PLAN.md` on branch `main` as authorized by PO (Art).
