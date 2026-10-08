import math
import random
import pytest

from app.core.probability.engine import ProbabilityEngine
from app.core.rng.engine import PythonRNG


# ==============================================================================
# EDGE CASES (A through N)
# ==============================================================================


def test_edge_case_a_empty_outcomes():
    """A. Verify empty outcomes collection raises explicit ValueError."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Outcomes cannot be empty"):
        pe.weighted_choice([], [])


def test_edge_case_b_empty_weights():
    """B. Verify empty weights collection with non-empty outcomes raises explicit ValueError."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Weights cannot be empty"):
        pe.weighted_choice(["A"], [])


def test_edge_case_c_mismatched_lengths():
    """C. Verify mismatched lengths between outcomes and weights raises ValueError."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Length mismatch"):
        pe.weighted_choice(["A", "B", "C"], [10, 20])


def test_edge_case_d_negative_weight():
    """D. Verify negative weights are rejected."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Weights must be non-negative"):
        pe.weighted_choice(["A", "B"], [-1, 10])


def test_edge_case_e_nan_weight():
    """E. Verify NaN weights are rejected as non-finite numbers."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Invalid weight"):
        pe.weighted_choice(["A", "B"], [math.nan, 10])


def test_edge_case_f_infinite_weight():
    """F. Verify infinite weights (+inf, -inf) are rejected as non-finite numbers."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Invalid weight"):
        pe.weighted_choice(["A", "B"], [math.inf, 10])

    with pytest.raises(ValueError, match="Invalid weight"):
        pe.weighted_choice(["A", "B"], [-math.inf, 10])


def test_edge_case_g_all_zero_weights():
    """G. Verify that all-zero weights raise ValueError because total weight <= 0."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Total weight must be strictly greater than 0"):
        pe.weighted_choice(["A", "B", "C"], [0, 0, 0])


def test_edge_case_h_single_outcome():
    """H. Verify single outcome with positive weight deterministically returns that outcome."""
    pe = ProbabilityEngine(PythonRNG(seed=1))
    result = pe.weighted_choice(["SOLO"], [42])
    assert result == "SOLO"


def test_edge_case_i_multiple_outcomes():
    """I. Verify selection across multiple outcomes operates within valid set."""
    pe = ProbabilityEngine(PythonRNG(seed=100))
    outcomes = ["COMMON", "RARE", "EPIC", "LEGENDARY"]
    weights = [60, 25, 10, 5]

    results = [pe.weighted_choice(outcomes, weights) for _ in range(50)]
    assert all(r in outcomes for r in results)
    assert len(set(results)) > 1


def test_edge_case_j_zero_weight_outcome_never_selected():
    """J. Verify outcomes with zero weight are never selected across many draws."""
    pe = ProbabilityEngine(PythonRNG(seed=777))
    outcomes = ["NEVER_1", "POSSIBLE_A", "NEVER_2", "POSSIBLE_B"]
    weights = [0, 50, 0, 50]

    results = [pe.weighted_choice(outcomes, weights) for _ in range(100)]
    assert "NEVER_1" not in results
    assert "NEVER_2" not in results
    assert all(r in ("POSSIBLE_A", "POSSIBLE_B") for r in results)


def test_edge_case_k_very_different_weight_magnitudes():
    """K. Verify selection handles vastly different orders of magnitude without numerical failure."""
    pe = ProbabilityEngine(PythonRNG(seed=555))
    outcomes = ["MICRO", "MACRO"]
    weights = [1e-9, 1e9]

    # Over 50 draws, MACRO should dominate completely
    results = [pe.weighted_choice(outcomes, weights) for _ in range(50)]
    assert results.count("MACRO") == 50


def test_edge_case_l_deterministic_seed():
    """L. Verify identical seeds produce strictly identical sequence of selections."""
    pe1 = ProbabilityEngine(PythonRNG(seed=99999))
    pe2 = ProbabilityEngine(PythonRNG(seed=99999))

    outcomes = ["A", "B", "C", "D"]
    weights = [10, 20, 30, 40]

    seq1 = [pe1.weighted_choice(outcomes, weights) for _ in range(50)]
    seq2 = [pe2.weighted_choice(outcomes, weights) for _ in range(50)]

    assert seq1 == seq2


def test_edge_case_m_save_and_restore_rng_state():
    """M. Verify saving RNG state, executing probability calls, and restoring produces identical output."""
    pe = ProbabilityEngine(PythonRNG(seed=12345))
    outcomes = ["X", "Y", "Z"]
    weights = [15, 35, 50]

    # Advance state slightly
    _ = [pe.weighted_choice(outcomes, weights) for _ in range(5)]

    # Snapshot state
    state = pe.rng.get_state()
    val_a = pe.weighted_choice(outcomes, weights)
    subsequent_a = [pe.weighted_choice(outcomes, weights) for _ in range(10)]

    # Restore state
    pe.rng.set_state(state)
    val_b = pe.weighted_choice(outcomes, weights)
    subsequent_b = [pe.weighted_choice(outcomes, weights) for _ in range(10)]

    assert val_a == val_b
    assert subsequent_a == subsequent_b


def test_edge_case_n_global_random_state_isolation():
    """N. Verify ProbabilityEngine calls do not alter or depend on Python's global random state."""
    random.seed(31415)
    global_before = [random.random() for _ in range(5)]

    # Reset global seed
    random.seed(31415)

    # Use ProbabilityEngine with isolated RNG
    pe = ProbabilityEngine(PythonRNG(seed=27182))
    _ = [pe.weighted_choice(["A", "B", "C"], [10, 20, 30]) for _ in range(50)]

    global_after = [random.random() for _ in range(5)]
    assert global_before == global_after


# ==============================================================================
# DETERMINISM & INDEPENDENT STREAMS
# ==============================================================================


def test_different_seeds_produce_independent_streams():
    """Verify different seeds produce independently seeded streams."""
    pe1 = ProbabilityEngine(PythonRNG(seed=101))
    pe2 = ProbabilityEngine(PythonRNG(seed=202))

    outcomes = ["A", "B", "C"]
    weights = [1, 1, 1]

    seq1 = [pe1.weighted_choice(outcomes, weights) for _ in range(30)]
    seq2 = [pe2.weighted_choice(outcomes, weights) for _ in range(30)]

    assert seq1 != seq2


def test_dependency_injection_of_rng():
    """Verify explicit RNG injection and default initialization."""
    custom_rng = PythonRNG(seed=42)
    pe_injected = ProbabilityEngine(rng=custom_rng)
    assert pe_injected.rng is custom_rng

    pe_default = ProbabilityEngine()
    assert pe_default.rng is not None


def test_weighted_choice_from_dict():
    """Verify convenience method weighted_choice_from_dict selects outcomes correctly."""
    pe = ProbabilityEngine(PythonRNG(seed=789))
    dist = {"FIRE": 50, "WATER": 30, "GRASS": 20}

    results = [pe.weighted_choice_from_dict(dist) for _ in range(30)]
    assert all(r in dist for r in results)

    with pytest.raises(ValueError, match="Distribution mapping cannot be empty"):
        pe.weighted_choice_from_dict({})


# ==============================================================================
# STATISTICAL SANITY TEST (Lightweight, Non-flaky)
# ==============================================================================


def test_lightweight_statistical_sanity():
    """Verify empirical distribution aligns with expected weights under deterministic sample.

    Weights: [1, 3] -> Expected: A = 25%, B = 75%.
    Sample size: 1000 draws under fixed seed 42.
    Tolerance: +/- 5% (asserts 20% <= ratio_A <= 30% and 70% <= ratio_B <= 80%).
    """
    pe = ProbabilityEngine(PythonRNG(seed=42))
    outcomes = ["A", "B"]
    weights = [1, 3]
    total_samples = 1000

    results = [pe.weighted_choice(outcomes, weights) for _ in range(total_samples)]

    count_a = results.count("A")
    count_b = results.count("B")

    ratio_a = count_a / total_samples
    ratio_b = count_b / total_samples

    # Deterministic counts under seed 42: count_a == 238 (23.8%), count_b == 762 (76.2%)
    assert 0.20 <= ratio_a <= 0.30, f"Observed ratio A: {ratio_a}"
    assert 0.70 <= ratio_b <= 0.80, f"Observed ratio B: {ratio_b}"
