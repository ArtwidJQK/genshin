# Adversarial Review Report: Phase P3.2 Artifact Loot Sources Implementation

- **Review Date:** 2026-10-20
- **Auditor:** Adversarial Reviewer (Independent Verification Pass)
- **Target Deliverables:**
  - `config/artifacts/loot_sources.json` (D1)
  - `config/artifacts/provenance.json` (D2)
  - `app/core/artifact/schema.py` (D3)
  - `app/core/artifact/config.py` (D4)
  - `app/core/artifact/loot.py` (D5)
  - `app/core/artifact/__init__.py` (D6)
  - `tests/unit/test_loot_determinism.py` (D7)
  - `tests/unit/test_loot_invariants.py` (D8)
  - `tests/statistical/test_loot_statistical.py` (D9)
- **Governing Specifications:**
  - `docs/specs/p3_loot_sources_spec.md` v1.3.0
  - `docs/adr/ADR-002-loot-sources-and-4star-abstraction.md`
  - `AGENTS.md` Section 5, 7, 8, 9, 10, 11

---

## 1. Executive Summary

| Gate | Requirement | Result | Evidence |
| :--- | :--- | :---: | :--- |
| **Rule & Architectural Fidelity** | Refusal on unverified rules; strict isolation; zero silent fallback | **PASS** | `test_strict_fidelity_mode_refusal_invariant` (14/14 tests passing) |
| **Probability Fidelity** | Preregistered Dual Gates (Bonferroni $\chi^2$ & $4\sigma$ margins) | **PASS** | Fast Suite ($N = 100,000$) & Heavy Suite ($N = 1,000,000$) both pass Gate 1 & Gate 2 |
| **Determinism & PRNG Purity** | Injected RNGInterface; bit-for-bit replay; global state isolation | **PASS** | `test_loot_determinism.py` (6/6 tests passing) |
| **Catalog & Provenance** | 14 loot source records with locators and honest evidence levels | **PASS** | `test_config_schema.py` (10/10 tests passing) |
| **Regression Safety** | Full baseline test suite preservation (178 existing tests) | **PASS** | Full suite: 200 tests passing (199 fast + 1 heavy slow) |

**OVERALL VERDICT:** **PASS** (Zero CRITICAL, zero HIGH findings).

---

## 2. Adversarial Stress & Invariant Audit

### 2.1 Fidelity Mode Enforcement & Zero Silent Fallback (F1)
- **Test Objective:** Prove that `STRICT` mode cannot be tricked into executing empirical community rates or silently substituting default drop odds.
- **Verification:**
  - Invoking `run_domain_of_blessing(fidelity_mode="STRICT")`, `"strict"`, or `LootFidelityMode.STRICT` immediately raises `FidelityViolationError` without calling RNG or generating entities.
  - Invoking `craft_strongbox(..., fidelity_mode="STRICT")` immediately raises `FidelityViolationError`.
  - Calling `load_and_validate_artifact_config(fidelity_mode="strict")` detects the unverified constants in `loot_sources.json` and raises `ValueError`.
  - `weakest_evidence_level` is explicitly `"INFERRED"` in `BEST_EFFORT` and `"EXPERIMENTAL"` in `EXPERIMENTAL`.
- **Finding:** No bypass exists. Behavior is completely conformant with `AGENTS.md Section 5.2`.

### 2.2 Condensed Resin Single-PRNG Stream Policy (F6)
- **Test Objective:** Prove that Condensed Resin does not clone, re-seed, or leak RNG state between Cycle 0 and Cycle 1.
- **Verification:**
  - Tested in `test_condensed_resin_matches_two_sequential_normal_runs`: running 1 Condensed Resin run yields exactly the concatenated artifacts, sum of fodder, and identical audit stream as running 2 consecutive normal runs on the same engine without re-seeding.
  - Tested in `test_prng_stream_isolation_from_global_random`: mutating Python's global `random` seed and drawing random numbers does not perturb the output of seeded loot executions.

### 2.3 Strongbox Input Validation & Immutability (F4, Decision 3A)
- **Test Objective:** Attempt to corrupt state or pass invalid items into `craft_strongbox`.
- **Verification:**
  - Non-list input (`tuple`, `str`, `None`) raises `TypeError`.
  - Empty list or counts $< 3$ raise `ValueError`.
  - Non-multiple of 3 ($N = 4, 5, 7$) raises `ValueError`.
  - List containing any non-5★ artifact raises `ValueError` specifying the offending artifact ID and rarity.
  - Empty or whitespace `target_set` raises `ValueError`.
  - Passed sacrifice list is not mutated or cleared in-place.
  - Exact $3:1$ ratio preserved ($N = 12 \to 4$ outputs).

### 2.4 4★ Fodder Representation & Evidence Audit (F3)
- **Test Objective:** Verify that 4★ fodder is strictly abstracted as an integer and classified as `INFERRED`.
- **Verification:**
  - `count_4star_fodder` is typed as `int` on `DomainDropResult`.
  - Normal runs yield integers in $[2, 3]$; condensed runs yield integers in $[4, 6]$.
  - Provenance catalog classifies `domain.fodder_4star_baseline` and `domain.fodder_4star_secondary_probability` as `INFERRED` (Level C), documenting that HoYoverse text only guarantees 4★ presence in the pool without publishing drop quantities.

---

## 3. Preregistered Statistical Verification Results (F5)

### 3.1 Gate 1: Chi-Square Goodness-of-Fit Gate (Omnicategorical)
- **Hypothesis Family ($M = 3$):** 5 Slots ($df=4$), Set Split ($df=1$), Domain Initial Lines ($df=1$).
- **Significance Level:** Family $\alpha = 0.001$, adjusted $\alpha_{\text{adj}} = \frac{0.001}{3} \approx 0.000333$ (Bonferroni union bound).
- **Critical Thresholds (strictest of Spec v1.3.0 and exact machine precision):**
  - $df = 4$: $\chi^2_{\text{crit}} = 20.888$ (exact machine quantile for $\alpha = 0.001/3$ is $20.8876...$; strictly tighter than Spec $21.110$)
  - $df = 1$: $\chi^2_{\text{crit}} = 12.870$ (Spec v1.3.0 value; strictly tighter than machine precision $12.8731...$)

| Suite | Dataset Evaluated | Degrees of Freedom | $\chi^2_{\text{crit}}$ | $\chi^2_{\text{calc}}$ | Result |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Fast ($N=100k$)** | 5 Artifact Slots | $df = 4$ | $20.888$ | **$6.7713$** | **PASS** ($p > 0.14$) |
| **Fast ($N=100k$)** | Set Split (50/50) | $df = 1$ | $12.870$ | **$5.8279$** | **PASS** ($p > 0.01$) |
| **Fast ($N=100k$)** | Initial Lines (80/20) | $df = 1$ | $12.870$ | **$0.5960$** | **PASS** ($p > 0.44$) |
| **Heavy ($N=1M$)** | 5 Artifact Slots | $df = 4$ | $20.888$ | **$3.1942$** | **PASS** ($p > 0.52$) |
| **Heavy ($N=1M$)** | Set Split (50/50) | $df = 1$ | $12.870$ | **$0.0211$** | **PASS** ($p > 0.88$) |
| **Heavy ($N=1M$)** | Initial Lines (80/20) | $df = 1$ | $12.870$ | **$0.0435$** | **PASS** ($p > 0.83$) |

### 3.2 Gate 2: $4\sigma$ Local Binomial Boundary Gate
- **Formulas Evaluated:**
  - Artifact-level trials ($N_{\text{art}}$): $|\hat{p} - p| \le 4 \times \sqrt{\frac{p(1-p)}{N_{\text{art}}}}$ (empirical Bernoulli sample size)
  - Run-count nominal bound ($N_{\text{runs}}$): $|\hat{p} - p| \le 4 \times \sqrt{\frac{p(1-p)}{N_{\text{runs}}}}$ (Spec Table 8.4 nominal bound)
  - Craft/run-level trials: Denominator matches observation unit ($N_{\text{crafts}}$ for Strongbox, $N_{\text{runs}}$ for Secondary 5★)

| Suite | Metric Evaluated | Observation Unit ($n$) | Expected $p$ | Observed $\hat{p}$ | Deviation $\|\hat{p} - p\|$ | $4\sigma$ Bound ($N_{\text{art}}$) | $4\sigma$ Bound ($N_{\text{runs}}$ / Spec) | Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fast ($100k$)** | Domain Set 50/50 | Artifact ($106,546$) | $0.500000$ | $0.496302$ | $0.003698$ | $\pm 0.006127$ | $\pm 0.006325$ | **PASS (both)** |
| **Fast ($100k$)** | Domain 4-Line (20%) | Artifact ($106,546$) | $0.200000$ | $0.200946$ | $0.000946$ | $\pm 0.004902$ | $\pm 0.005060$ | **PASS (both)** |
| **Fast ($100k$)** | Strongbox 4-Line (34%) | Craft ($100,000$) | $0.340000$ | $0.339180$ | $0.000820$ | N/A | $\pm 0.005992$ | **PASS** |
| **Fast ($100k$)** | Secondary 5★ (6.54%) | Domain Run ($100,000$) | $0.065400$ | $0.065460$ | $0.000060$ | N/A | $\pm 0.003127$ | **PASS** |
| **Heavy ($1M$)** | Domain Set 50/50 | Artifact ($1,065,288$) | $0.500000$ | $0.499929$ | $0.000071$ | $\pm 0.001938$ | $\pm 0.002000$ | **PASS (both)** |
| **Heavy ($1M$)** | Domain 4-Line (20%) | Artifact ($1,065,288$) | $0.200000$ | $0.199921$ | $0.000079$ | $\pm 0.001550$ | $\pm 0.001600$ | **PASS (both)** |
| **Heavy ($1M$)** | Strongbox 4-Line (34%) | Craft ($1,000,000$) | $0.340000$ | $0.339682$ | $0.000318$ | N/A | $\pm 0.001895$ | **PASS** |
| **Heavy ($1M$)** | Secondary 5★ (6.54%) | Domain Run ($1,000,000$) | $0.065400$ | $0.065288$ | $0.000112$ | N/A | $\pm 0.000989$ | **PASS** |

---

## 4. Standing Blockers & Scope Boundary Audit
- **Capturing Radiance (`OQ-01`):** Verified strictly UNTOUCHED and BLOCKED.
- **Reshaping & Hallowed Exegesis (`OQ-03`):** Verified strictly UNTOUCHED and BLOCKED.
- **Phase P4 (Transmuter, Sanctifying Elixir):** Verified zero out-of-scope implementation.
- **Git Hygiene:** No commits, pushes, or branch switches performed.

---

## 5. Adversarial Review Conclusion

```
RESULT: PASS
CRITICAL FINDINGS: 0
HIGH FINDINGS:     0
MEDIUM FINDINGS:   0
LOW FINDINGS:      0
```

All 9 deliverables (D1–D9) satisfy specification v1.3.0, ADR-002, and `AGENTS.md`. The implementation is mathematically rigorous, epistemologically sound, and ready for Project Lead review.
