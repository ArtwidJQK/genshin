"""Layer 3: Statistical distribution tests for Artifact Loot Sources.

Satisfies:
- P3 Spec Section 8 (Dual-Gate Pre-Registered Statistical Acceptance Criteria)
- Gate 1: Chi-Square Goodness-of-Fit Gate (Omnicategorical with Bonferroni correction M=3, alpha_adj = 0.000333)
- Gate 2: 4-sigma Local Binomial Boundary Gate (|p_hat - p| <= 4 * SE) across 4 scalar targets
- Fast Suite (N = 100,000, seed = 20261020)
- Heavy Suite (N = 1,000,000, seed = 20261021)
"""

import math
from typing import Dict, List, Sequence, Tuple

import pytest

from app.core.artifact.engine import ArtifactEngine
from app.core.artifact.loot import (
    craft_strongbox,
    run_domain_of_blessing,
)
from app.core.artifact.models import Artifact, ArtifactSlot, SubstatState
from app.core.rng.engine import PythonRNG

# Pre-registered Bonferroni critical values (Spec Section 8.2 & Table 8.4)
# M = 3 hypothesis tests on Domain dataset, alpha_family = 0.001, alpha_adj = 0.000333
# df = 4 (5 slots): chi2_crit = 20.888 (exact machine precision for alpha=0.001/3; strictly tighter than Spec 21.110)
# df = 1 (2 bins):  chi2_crit = 12.870 (Spec v1.3.0 value; strictly tighter than machine precision 12.873)
CHI2_CRIT_DF4 = 20.888
CHI2_CRIT_DF1 = 12.870


def test_gate_1_critical_values_reconciliation():
    """Verify Gate 1 critical values are selected to satisfy the strictest criteria between Spec v1.3.0 and machine precision.

    - df = 4: CHI2_CRIT_DF4 = 20.888 (exact machine quantile for alpha = 0.001/3 is 20.8876..., strictly more conservative than Spec v1.3.0's 21.110).
    - df = 1: CHI2_CRIT_DF1 = 12.870 (Spec v1.3.0 value 12.870 is strictly more conservative than exact machine quantile 12.8731...).
    """
    assert CHI2_CRIT_DF4 == 20.888
    assert CHI2_CRIT_DF4 < 21.110  # Stricter than Spec 21.110
    assert CHI2_CRIT_DF1 == 12.870
    assert CHI2_CRIT_DF1 < 12.873132  # Stricter than machine precision 12.873


def compute_chi_square(observed: Sequence[int], expected_probs: Sequence[float]) -> float:
    """Compute Pearson's chi-square goodness-of-fit statistic."""
    total = sum(observed)
    if total == 0:
        raise ValueError("Cannot compute chi-square with zero total observations.")
    chi2_val = 0.0
    for obs, prob in zip(observed, expected_probs):
        expected = total * prob
        chi2_val += ((obs - expected) ** 2) / expected
    return chi2_val


def run_domain_simulation(n_runs: int, seed: int) -> Tuple[int, List[int], List[int], List[int], int]:
    """Execute n_runs of Domain of Blessing collecting statistical metrics.

    Returns:
        total_artifacts: Total count of 5★ artifacts generated across all runs.
        slot_counts: Counts across [FLOWER, PLUME, SANDS, GOBLET, CIRCLET].
        set_counts: Counts across [set_a, set_b].
        line_counts: Counts across [3-line, 4-line].
        runs_with_secondary_5star: Number of runs that dropped 2 5★ artifacts.
    """
    engine = ArtifactEngine(rng=PythonRNG(seed=seed))
    slot_index_map = {
        ArtifactSlot.FLOWER: 0,
        ArtifactSlot.PLUME: 1,
        ArtifactSlot.SANDS: 2,
        ArtifactSlot.GOBLET: 3,
        ArtifactSlot.CIRCLET: 4,
    }

    slot_counts = [0] * 5
    set_counts = [0, 0]  # [set_a, set_b]
    line_counts = [0, 0]  # [3-line, 4-line]
    runs_with_secondary_5star = 0
    total_artifacts = 0

    for _ in range(n_runs):
        res = run_domain_of_blessing(
            domain_id="domain_stat_sim",
            sets=("set_a", "set_b"),
            use_condensed=False,
            engine=engine,
        )
        if len(res.artifacts) == 2:
            runs_with_secondary_5star += 1
        total_artifacts += len(res.artifacts)

        for art in res.artifacts:
            slot_counts[slot_index_map[art.slot]] += 1
            if art.set_id == "set_a":
                set_counts[0] += 1
            else:
                set_counts[1] += 1

            active_count = sum(1 for s in art.substats if s.state == SubstatState.ACTIVE)
            if active_count == 3:
                line_counts[0] += 1
            else:
                line_counts[1] += 1

    return total_artifacts, slot_counts, set_counts, line_counts, runs_with_secondary_5star


def run_strongbox_simulation(n_crafts: int, seed: int) -> List[int]:
    """Execute n_crafts of Artifact Strongbox collecting line count statistics.

    Returns:
        line_counts: Counts across [3-line, 4-line].
    """
    engine = ArtifactEngine(rng=PythonRNG(seed=seed))
    dummy_sacrifices = [engine.generate_artifact() for _ in range(3)]
    sb_line_counts = [0, 0]  # [3-line, 4-line]

    for _ in range(n_crafts):
        res = craft_strongbox(
            target_set="noblesse_oblige",
            sacrifice_artifacts=dummy_sacrifices,
            engine=engine,
        )
        art = res.artifacts[0]
        active_count = sum(1 for s in art.substats if s.state == SubstatState.ACTIVE)
        if active_count == 3:
            sb_line_counts[0] += 1
        else:
            sb_line_counts[1] += 1

    return sb_line_counts


def evaluate_gate_1(
    slot_counts: List[int],
    set_counts: List[int],
    line_counts: List[int],
) -> Dict[str, Tuple[float, float, bool]]:
    """Evaluate Gate 1 (Chi-square with Bonferroni correction across M=3 tests)."""
    chi2_slots = compute_chi_square(slot_counts, [0.20] * 5)
    chi2_set = compute_chi_square(set_counts, [0.50, 0.50])
    chi2_lines = compute_chi_square(line_counts, [0.80, 0.20])

    results = {
        "slots_5": (chi2_slots, CHI2_CRIT_DF4, chi2_slots < CHI2_CRIT_DF4),
        "set_split": (chi2_set, CHI2_CRIT_DF1, chi2_set < CHI2_CRIT_DF1),
        "initial_lines": (chi2_lines, CHI2_CRIT_DF1, chi2_lines < CHI2_CRIT_DF1),
    }
    return results


def evaluate_gate_2(
    set_a_count: int,
    total_domain_artifacts: int,
    domain_4line_count: int,
    sb_4line_count: int,
    n_sb_crafts: int,
    runs_secondary_5star: int,
    n_domain_runs: int,
) -> Dict[str, Tuple[float, float, float, float, float, bool]]:
    """Evaluate Gate 2 (4-sigma local binomial bounds across 4 scalar targets).

    For artifact-level metrics (domain_set_50_50, domain_4_line), evaluates BOTH:
      1. four_se_art: 4 * sqrt(p*(1-p)/N_art) using actual observation count
      2. four_se_runs: 4 * sqrt(p*(1-p)/N_runs) using nominal run count per Spec Table 8.4

    For craft/run-level metrics (strongbox_4_line, secondary_5star), uses the exact
    observation denominator matching the trial unit (n_sb_crafts and n_domain_runs).

    Returns:
        Dict mapping metric_name -> (p_hat, p_expected, diff, four_se_art, four_se_runs, passes)
    """
    results: Dict[str, Tuple[float, float, float, float, float, bool]] = {}

    # 1. Artifact-level metric: Domain Set 50/50
    p_set = 0.500
    p_hat_set = set_a_count / total_domain_artifacts
    diff_set = abs(p_hat_set - p_set)
    four_se_set_art = 4.0 * math.sqrt(p_set * (1.0 - p_set) / total_domain_artifacts)
    four_se_set_runs = 4.0 * math.sqrt(p_set * (1.0 - p_set) / n_domain_runs)
    passes_set = (diff_set <= four_se_set_art) and (diff_set <= four_se_set_runs)
    results["domain_set_50_50"] = (
        p_hat_set,
        p_set,
        diff_set,
        four_se_set_art,
        four_se_set_runs,
        passes_set,
    )

    # 2. Artifact-level metric: Domain 4-Line Count
    p_line = 0.200
    p_hat_line = domain_4line_count / total_domain_artifacts
    diff_line = abs(p_hat_line - p_line)
    four_se_line_art = 4.0 * math.sqrt(p_line * (1.0 - p_line) / total_domain_artifacts)
    four_se_line_runs = 4.0 * math.sqrt(p_line * (1.0 - p_line) / n_domain_runs)
    passes_line = (diff_line <= four_se_line_art) and (diff_line <= four_se_line_runs)
    results["domain_4_line"] = (
        p_hat_line,
        p_line,
        diff_line,
        four_se_line_art,
        four_se_line_runs,
        passes_line,
    )

    # 3. Craft-level metric: Strongbox 4-Line Count (trial unit is 1 craft)
    p_sb = 0.340
    p_hat_sb = sb_4line_count / n_sb_crafts
    diff_sb = abs(p_hat_sb - p_sb)
    four_se_sb = 4.0 * math.sqrt(p_sb * (1.0 - p_sb) / n_sb_crafts)
    passes_sb = diff_sb <= four_se_sb
    results["strongbox_4_line"] = (p_hat_sb, p_sb, diff_sb, four_se_sb, four_se_sb, passes_sb)

    # 4. Run-level metric: Secondary 5★ (trial unit is 1 domain run)
    p_sec = 0.0654
    p_hat_sec = runs_secondary_5star / n_domain_runs
    diff_sec = abs(p_hat_sec - p_sec)
    four_se_sec = 4.0 * math.sqrt(p_sec * (1.0 - p_sec) / n_domain_runs)
    passes_sec = diff_sec <= four_se_sec
    results["secondary_5star"] = (p_hat_sec, p_sec, diff_sec, four_se_sec, four_se_sec, passes_sec)

    return results


def test_fast_loot_statistical_dual_gates():
    """Fast Suite (N = 100,000, seed = 20261020): strictly passes both Gate 1 and Gate 2."""
    n_samples = 100_000
    seed = 20261020

    # 1. Run Domain simulation
    (
        total_artifacts,
        slot_counts,
        set_counts,
        line_counts,
        runs_secondary_5star,
    ) = run_domain_simulation(n_samples, seed=seed)

    # 2. Run Strongbox simulation
    sb_line_counts = run_strongbox_simulation(n_samples, seed=seed)

    # 3. Evaluate Gate 1 (Chi-Square Bonferroni)
    gate_1 = evaluate_gate_1(slot_counts, set_counts, line_counts)
    for test_name, (chi2_calc, chi2_crit, passes) in gate_1.items():
        assert passes, f"Fast Gate 1 FAIL on '{test_name}': chi2_calc={chi2_calc:.4f} >= chi2_crit={chi2_crit:.4f}"

    # 4. Evaluate Gate 2 (4-sigma Binomial Bounds)
    gate_2 = evaluate_gate_2(
        set_a_count=set_counts[0],
        total_domain_artifacts=total_artifacts,
        domain_4line_count=line_counts[1],
        sb_4line_count=sb_line_counts[1],
        n_sb_crafts=n_samples,
        runs_secondary_5star=runs_secondary_5star,
        n_domain_runs=n_samples,
    )
    for metric_name, (p_hat, p, diff, four_se_art, four_se_runs, passes) in gate_2.items():
        assert passes, (
            f"Fast Gate 2 FAIL on '{metric_name}': p_hat={p_hat:.6f}, p={p:.6f}, "
            f"diff={diff:.6f} exceeds four_se_art={four_se_art:.6f} or four_se_runs={four_se_runs:.6f}"
        )


@pytest.mark.slow
def test_heavy_loot_statistical_dual_gates():
    """Heavy Suite (N = 1,000,000, seed = 20261021): strictly passes both Gate 1 and Gate 2."""
    n_samples = 1_000_000
    seed = 20261021

    # 1. Run Domain simulation
    (
        total_artifacts,
        slot_counts,
        set_counts,
        line_counts,
        runs_secondary_5star,
    ) = run_domain_simulation(n_samples, seed=seed)

    # 2. Run Strongbox simulation
    sb_line_counts = run_strongbox_simulation(n_samples, seed=seed)

    # 3. Evaluate Gate 1 (Chi-Square Bonferroni)
    gate_1 = evaluate_gate_1(slot_counts, set_counts, line_counts)
    for test_name, (chi2_calc, chi2_crit, passes) in gate_1.items():
        assert passes, f"Heavy Gate 1 FAIL on '{test_name}': chi2_calc={chi2_calc:.4f} >= chi2_crit={chi2_crit:.4f}"

    # 4. Evaluate Gate 2 (4-sigma Binomial Bounds)
    gate_2 = evaluate_gate_2(
        set_a_count=set_counts[0],
        total_domain_artifacts=total_artifacts,
        domain_4line_count=line_counts[1],
        sb_4line_count=sb_line_counts[1],
        n_sb_crafts=n_samples,
        runs_secondary_5star=runs_secondary_5star,
        n_domain_runs=n_samples,
    )
    for metric_name, (p_hat, p, diff, four_se_art, four_se_runs, passes) in gate_2.items():
        assert passes, (
            f"Heavy Gate 2 FAIL on '{metric_name}': p_hat={p_hat:.6f}, p={p:.6f}, "
            f"diff={diff:.6f} exceeds four_se_art={four_se_art:.6f} or four_se_runs={four_se_runs:.6f}"
        )
