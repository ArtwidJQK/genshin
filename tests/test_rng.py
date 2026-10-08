import math
import random
import pytest

from app.core.rng.engine import PythonRNG


# 1. same seed -> same sequence
def test_same_seed_produces_identical_sequence():
    """Verify that identical seeds produce strictly identical sequences."""
    rng1 = PythonRNG(seed=12345)
    rng2 = PythonRNG(seed=12345)

    seq1 = [rng1.random() for _ in range(25)]
    seq2 = [rng2.random() for _ in range(25)]

    assert seq1 == seq2


# 2. different seed -> different sequence
def test_different_seeds_produce_different_sequences():
    """Verify that distinct seeds produce different sequences."""
    rng1 = PythonRNG(seed=12345)
    rng2 = PythonRNG(seed=54321)

    seq1 = [rng1.random() for _ in range(25)]
    seq2 = [rng2.random() for _ in range(25)]

    assert seq1 != seq2


# 3. save/restore RNG state
def test_rng_state_save_and_restore():
    """Verify state snapshot and restoration reproduces identical subsequent outputs."""
    rng = PythonRNG(seed=999)

    # Burn a few outputs
    _ = [rng.random() for _ in range(5)]

    # Capture state
    state = rng.get_state()
    val_a = rng.random()
    subsequent_a = [rng.random() for _ in range(5)]

    # Restore state
    rng.set_state(state)
    val_b = rng.random()
    subsequent_b = [rng.random() for _ in range(5)]

    assert val_a == val_b
    assert subsequent_a == subsequent_b


# 4. random() range
def test_random_produces_values_in_expected_range():
    """Verify random() outputs fall strictly within [0.0, 1.0)."""
    rng = PythonRNG(seed=42)
    for _ in range(100):
        val = rng.random()
        assert 0.0 <= val < 1.0


# 5. random_int() bounds
def test_random_int_respects_bounds():
    """Verify random_int respects inclusive [a, b] bounds and raises when a > b."""
    rng = PythonRNG(seed=42)

    for _ in range(100):
        val = rng.random_int(1, 6)
        assert 1 <= val <= 6
        assert isinstance(val, int)

    # Single value bound
    assert rng.random_int(7, 7) == 7

    # Inverted bounds error
    with pytest.raises(ValueError, match="cannot exceed upper bound"):
        rng.random_int(10, 5)


def test_random_float_respects_bounds():
    """Verify random_float respects [a, b] bounds and raises when a > b."""
    rng = PythonRNG(seed=42)

    for _ in range(100):
        val = rng.random_float(2.5, 8.5)
        assert 2.5 <= val <= 8.5
        assert isinstance(val, float)

    with pytest.raises(ValueError, match="cannot exceed upper bound"):
        rng.random_float(10.0, 5.0)


# 6. choice()
def test_choice_works_and_rejects_empty():
    """Verify choice selects from sequence and rejects empty sequences."""
    rng = PythonRNG(seed=42)
    items = ["pyro", "hydro", "anemo", "electro", "dendro", "cryo", "geo"]

    for _ in range(20):
        choice = rng.choice(items)
        assert choice in items

    with pytest.raises(ValueError, match="Cannot choose from an empty sequence"):
        rng.choice([])


# 7. shuffle() deterministic with same seed
def test_shuffle_is_deterministic_under_same_seed():
    """Verify shuffle mutates in-place deterministically with matching seeds."""
    rng1 = PythonRNG(seed=101)
    rng2 = PythonRNG(seed=101)

    list1 = list(range(20))
    list2 = list(range(20))

    rng1.shuffle(list1)
    rng2.shuffle(list2)

    assert list1 == list2
    # Ensure it actually shuffled
    assert list1 != list(range(20))


# 8. valid weighted_choice()
def test_weighted_choice_accepts_valid_weights():
    """Verify weighted_choice functions with valid integer and float weights."""
    rng = PythonRNG(seed=777)
    outcomes = ["A", "B", "C"]
    weights = [1, 2, 7]

    results = [rng.weighted_choice(outcomes, weights) for _ in range(50)]
    assert all(r in outcomes for r in results)

    # Edge case: zero weight on an item means it is never chosen
    strict_rng = PythonRNG(seed=123)
    zero_weight_results = [
        strict_rng.weighted_choice(["never", "always"], [0, 10]) for _ in range(20)
    ]
    assert all(r == "always" for r in zero_weight_results)


# 9. invalid weighted_choice() input
def test_weighted_choice_rejects_invalid_inputs():
    """Verify weighted_choice enforces strict validation on empty, mismatched, and negative inputs."""
    rng = PythonRNG(seed=42)

    # Empty outcomes
    with pytest.raises(ValueError, match="Outcomes cannot be empty"):
        rng.weighted_choice([], [])

    # Mismatched lengths
    with pytest.raises(ValueError, match="Length mismatch"):
        rng.weighted_choice(["A", "B"], [1])

    # Negative weight
    with pytest.raises(ValueError, match="Weights must be non-negative"):
        rng.weighted_choice(["A", "B"], [-1, 5])

    # Non-numeric or NaN / Inf weights
    with pytest.raises(ValueError, match="Invalid weight"):
        rng.weighted_choice(["A", "B"], [math.nan, 5])

    with pytest.raises(ValueError, match="Invalid weight"):
        rng.weighted_choice(["A", "B"], ["high", 5])  # type: ignore

    # Boolean weight
    with pytest.raises(ValueError, match="Invalid weight"):
        rng.weighted_choice(["A", "B"], [True, 5])


def test_weighted_choice_deterministic_under_same_seed():
    """Verify identical seeds produce identical sequence of weighted choices."""
    rng1 = PythonRNG(seed=8888)
    rng2 = PythonRNG(seed=8888)

    outcomes = ["R", "SR", "SSR", "UR"]
    weights = [80, 15, 4, 1]

    seq1 = [rng1.weighted_choice(outcomes, weights) for _ in range(50)]
    seq2 = [rng2.weighted_choice(outcomes, weights) for _ in range(50)]

    assert seq1 == seq2


def test_weighted_choice_state_save_and_restore():
    """Verify capturing and restoring RNG state reproduces identical weighted choice results."""
    rng = PythonRNG(seed=4321)
    outcomes = ["common", "uncommon", "rare", "legendary"]
    weights = [70.0, 20.0, 8.5, 1.5]

    # Advance state slightly
    _ = [rng.random() for _ in range(5)]

    state = rng.get_state()
    val_a = rng.weighted_choice(outcomes, weights)
    subsequent_a = [rng.weighted_choice(outcomes, weights) for _ in range(10)]

    rng.set_state(state)
    val_b = rng.weighted_choice(outcomes, weights)
    subsequent_b = [rng.weighted_choice(outcomes, weights) for _ in range(10)]

    assert val_a == val_b
    assert subsequent_a == subsequent_b


# 10. zero/negative total weight handling
def test_weighted_choice_zero_or_negative_total_weight_handling():
    """Verify weighted_choice explicitly rejects zero or negative cumulative weights."""
    rng = PythonRNG(seed=42)

    # All weights zero
    with pytest.raises(ValueError, match="Total weight must be strictly greater than 0"):
        rng.weighted_choice(["A", "B", "C"], [0, 0, 0])

    # Negative weight causing failure before or during sum
    with pytest.raises(ValueError, match="Weights must be non-negative"):
        rng.weighted_choice(["A", "B"], [-5, 2])


def test_isolated_from_global_random():
    """Verify that PythonRNG does not mutate or depend on global random state."""
    random.seed(111)
    global_seq1 = [random.random() for _ in range(5)]

    # Reset global seed
    random.seed(111)

    # Create and advance isolated PythonRNG
    isolated_rng = PythonRNG(seed=999)
    _ = [isolated_rng.random() for _ in range(20)]

    # Global sequence must remain unchanged by isolated_rng actions
    global_seq2 = [random.random() for _ in range(5)]
    assert global_seq1 == global_seq2
