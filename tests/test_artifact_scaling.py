"""Tests for Artifact main stat scaling domain API and invariants.

Verifies:
- Exact lookup for all 18 valid 5★ main stats across all 21 levels (0-20) compared to source JSON.
- Rejection of invalid levels, types, and stats (including FLAT_DEF).
- Rejection of missing or corrupted scaling configurations.
- Immutability of Artifact and ArtifactConfig during lookup.
- Boundary levels (0 and 20) and strict monotonicity.
- Clean separation between internal floating-point values and display formatting.
- Property-based tests via Hypothesis.
"""
import copy
import json
import math
from pathlib import Path
from typing import List

import pytest
from hypothesis import given, settings, strategies as st

from app.core.artifact import (
    Artifact,
    ArtifactConfig,
    ArtifactEngine,
    ArtifactSlot,
    Substat,
    SubstatState,
    VALID_MAIN_STATS,
    format_stat_value,
    get_main_stat_value,
    load_artifact_config,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "artifacts"
SCALING_JSON_PATH = CONFIG_DIR / "main_stat_scaling.json"


def _make_dummy_artifact(main_stat: str, level: int = 0, slot: ArtifactSlot = ArtifactSlot.SANDS) -> Artifact:
    """Helper to construct a valid 5★ Artifact for scaling tests."""
    # Pick 4 distinct substats that do not collide with main_stat
    candidates = [s for s in ("CRIT_RATE", "CRIT_DMG", "ENERGY_RECHARGE", "ELEMENTAL_MASTERY", "FLAT_ATK") if s != main_stat]
    substats = [
        Substat(
            slot_index=i,
            stat_type=candidates[i],
            state=SubstatState.ACTIVE,
            initial_value=10.0,
            initial_tier="100%",
            rolls=[],
        )
        for i in range(4)
    ]
    return Artifact(
        id="test-scaling-artifact",
        rarity=5,
        set_id="gladiators_finale",
        slot=slot,
        level=level,
        main_stat=main_stat,
        substats=substats,
        history=[],
    )


# ---------------------------------------------------------------------------
# 1. Complete 18 x 21 matrix verification against source JSON
# ---------------------------------------------------------------------------

def test_all_18_stats_all_21_levels_exact_lookup_against_source_json():
    """Verify that every single one of the 18 x 21 values exactly matches source JSON."""
    with open(SCALING_JSON_PATH, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    stats_data = raw_json["stats"]
    assert set(stats_data.keys()) == VALID_MAIN_STATS
    assert len(stats_data) == 18

    config = load_artifact_config()
    engine = ArtifactEngine(config=config)

    for stat_name, levels in stats_data.items():
        assert len(levels) == 21
        for lvl_str, expected_raw in levels.items():
            lvl = int(lvl_str)
            expected_val = float(expected_raw)

            # 1. Standalone function with (stat, level)
            val1 = get_main_stat_value(stat_name, lvl, config=config)
            assert val1 == expected_val, f"Mismatch for {stat_name} at lvl {lvl}: {val1} != {expected_val}"
            assert isinstance(val1, float)

            # 2. Config method
            val2 = config.get_main_stat_value(stat_name, lvl)
            assert val2 == expected_val

            # 3. Engine method
            val3 = engine.get_main_stat_value(stat_name, lvl)
            assert val3 == expected_val

            # 4. Standalone function with default config
            val4 = get_main_stat_value(stat_name, lvl)
            assert val4 == expected_val

            # 5. Standalone function with Artifact target
            art = _make_dummy_artifact(main_stat=stat_name, level=lvl)
            val5 = get_main_stat_value(art, config=config)
            assert val5 == expected_val

            # 6. Artifact method
            val6 = art.get_main_stat_value(config=config)
            assert val6 == expected_val

            # 7. Engine with Artifact target
            val7 = engine.get_main_stat_value(art)
            assert val7 == expected_val


# ---------------------------------------------------------------------------
# 2. Boundary Levels (0 and 20)
# ---------------------------------------------------------------------------

def test_boundary_levels_min_max():
    """Explicitly verify level 0 (min) and level 20 (max) anchors for key stats."""
    config = load_artifact_config()

    # HP base: 717.0 -> 4780.0
    assert get_main_stat_value("FLAT_HP", 0, config=config) == 717.0
    assert get_main_stat_value("FLAT_HP", 20, config=config) == 4780.0

    # ATK base: 47.0 -> 311.0
    assert get_main_stat_value("FLAT_ATK", 0, config=config) == 47.0
    assert get_main_stat_value("FLAT_ATK", 20, config=config) == 311.0

    # CRIT Rate: 4.7 -> 31.1
    assert get_main_stat_value("CRIT_RATE", 0, config=config) == 4.7
    assert get_main_stat_value("CRIT_RATE", 20, config=config) == 31.1

    # CRIT DMG: 9.3 -> 62.2
    assert get_main_stat_value("CRIT_DMG", 0, config=config) == 9.3
    assert get_main_stat_value("CRIT_DMG", 20, config=config) == 62.2

    # Percentage stats: 7.0 -> 46.6
    assert get_main_stat_value("ATK_PERCENT", 0, config=config) == 7.0
    assert get_main_stat_value("ATK_PERCENT", 20, config=config) == 46.6


# ---------------------------------------------------------------------------
# 3. Invalid Level Inputs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("invalid_level", [-1, 21, 22, -10, 100, 999])
def test_reject_level_out_of_bounds(invalid_level):
    """Artifact level outside [0, 20] must raise ValueError."""
    with pytest.raises(ValueError, match="Artifact level must be between 0 and 20 inclusive"):
        get_main_stat_value("CRIT_RATE", invalid_level)


@pytest.mark.parametrize("invalid_level_type", [3.5, "10", [0], {1: 2}])
def test_reject_non_integer_level_type(invalid_level_type):
    """Non-integer level types must raise TypeError."""
    with pytest.raises(TypeError, match="Artifact level must be an integer"):
        get_main_stat_value("CRIT_RATE", invalid_level_type)


def test_reject_none_level():
    """None level for stat string must raise TypeError."""
    with pytest.raises(TypeError, match="Argument 'level' is required when target is a stat_type string"):
        get_main_stat_value("CRIT_RATE", None)


@pytest.mark.parametrize("bool_level", [True, False])
def test_reject_boolean_level(bool_level):
    """Booleans (True/False) must be explicitly rejected as level."""
    with pytest.raises(TypeError, match="Artifact level must be an integer"):
        get_main_stat_value("CRIT_RATE", bool_level)


# ---------------------------------------------------------------------------
# 4. Invalid Stat Inputs
# ---------------------------------------------------------------------------

def test_reject_flat_def_as_main_stat():
    """FLAT_DEF is never a valid 5★ main stat in Genshin Impact."""
    with pytest.raises(ValueError, match="Stat 'FLAT_DEF' is not a valid 5★ main stat"):
        get_main_stat_value("FLAT_DEF", 0)


@pytest.mark.parametrize("invalid_stat", ["NOT_A_STAT", "CRIT", "", "HP", "DEF", "BASE_ATK"])
def test_reject_unknown_main_stat(invalid_stat):
    """Unknown or unsupported stat identifiers must raise ValueError."""
    with pytest.raises(ValueError, match="is not a valid 5★ main stat"):
        get_main_stat_value(invalid_stat, 0)


@pytest.mark.parametrize("non_string_stat", [123, True, False, None, ["CRIT_RATE"]])
def test_reject_non_string_stat(non_string_stat):
    """Non-string stat identifiers must raise TypeError."""
    with pytest.raises(TypeError, match="Target (cannot be a boolean|must be an Artifact)"):
        get_main_stat_value(non_string_stat, 0)


# ---------------------------------------------------------------------------
# 5. Artifact Target Usages & Edge Cases
# ---------------------------------------------------------------------------

def test_artifact_target_with_redundant_level_raises_type_error():
    """Providing 'level' when target is an Artifact must raise TypeError."""
    art = _make_dummy_artifact("CRIT_RATE", level=5)
    with pytest.raises(TypeError, match="Argument 'level' must not be provided when target is an Artifact"):
        get_main_stat_value(art, level=5)


def test_stat_string_without_level_raises_type_error():
    """Providing a stat string without level must raise TypeError."""
    with pytest.raises(TypeError, match="Argument 'level' is required when target is a stat_type string"):
        get_main_stat_value("CRIT_RATE")


def test_reject_corrupted_artifact():
    """An Artifact violating domain invariants must be rejected by get_main_stat_value."""
    art = _make_dummy_artifact("CRIT_RATE", level=0)
    # Mutate to out-of-bounds level
    art.level = 25
    with pytest.raises(ValueError, match="Artifact level must be between 0 and 20 inclusive"):
        get_main_stat_value(art)


# ---------------------------------------------------------------------------
# 6. Config Robustness & Validation
# ---------------------------------------------------------------------------

def test_reject_invalid_config_type():
    """Passing a non-ArtifactConfig instance for config must raise TypeError."""
    with pytest.raises(TypeError, match="config must be an instance of ArtifactConfig"):
        get_main_stat_value("CRIT_RATE", 0, config="not-a-config")


def test_reject_config_lacking_scaling_data():
    """ArtifactConfig without main_stat_scaling loaded must raise ValueError."""
    config = load_artifact_config()
    config.main_stat_scaling = None
    with pytest.raises(ValueError, match="ArtifactConfig does not have main_stat_scaling data loaded"):
        get_main_stat_value("CRIT_RATE", 0, config=config)


def test_reject_config_with_empty_scaling_data():
    """ArtifactConfig with empty main_stat_scaling dict must raise ValueError."""
    config = load_artifact_config()
    config.main_stat_scaling = {}
    with pytest.raises(ValueError, match="ArtifactConfig does not have main_stat_scaling data loaded"):
        get_main_stat_value("CRIT_RATE", 0, config=config)


def test_reject_config_missing_requested_stat():
    """If scaling data is missing the requested stat, raise ValueError."""
    config = load_artifact_config()
    del config.main_stat_scaling["CRIT_RATE"]
    with pytest.raises(ValueError, match="Main stat 'CRIT_RATE' is not present in scaling configuration"):
        get_main_stat_value("CRIT_RATE", 0, config=config)


def test_reject_config_missing_requested_level():
    """If scaling data is missing the requested level, raise ValueError."""
    config = load_artifact_config()
    del config.main_stat_scaling["CRIT_RATE"][10]
    with pytest.raises(ValueError, match="Level 10 is not present in scaling data for 'CRIT_RATE'"):
        get_main_stat_value("CRIT_RATE", 10, config=config)


def test_reject_corrupted_non_numeric_or_non_finite_scaling_value():
    """Corrupted scaling value in config (NaN, inf, str, bool) must raise ValueError."""
    config = load_artifact_config()
    config.main_stat_scaling["CRIT_RATE"][5] = float("nan")
    with pytest.raises(ValueError, match="Invalid non-finite or non-numeric scaling value"):
        get_main_stat_value("CRIT_RATE", 5, config=config)

    config.main_stat_scaling["CRIT_RATE"][5] = -1.0
    with pytest.raises(ValueError, match="must be strictly positive"):
        get_main_stat_value("CRIT_RATE", 5, config=config)


def test_config_validation_catches_slot_scaling_mismatch():
    """ArtifactConfig.validate() enforces consistency between slot pools and scaling curves."""
    config = load_artifact_config()
    # Add a phantom stat to main_stat_scaling
    config.main_stat_scaling["PHANTOM_STAT"] = {i: float(i + 1) for i in range(21)}
    with pytest.raises(ValueError, match="main_stat_scaling must contain exactly the 18 valid main stats"):
        config.validate()


# ---------------------------------------------------------------------------
# 7. No Rounding in Domain Layer vs Display Formatting
# ---------------------------------------------------------------------------

def test_unrounded_precision_preserved_and_separate_from_formatting():
    """Domain layer preserves exact raw float; formatting layer handles presentation."""
    config = load_artifact_config()

    # Level 20 CRIT Rate: raw float 31.1, displayed as "31.1%"
    raw_cr = get_main_stat_value("CRIT_RATE", 20, config=config)
    assert raw_cr == 31.1
    assert isinstance(raw_cr, float)
    formatted_cr = format_stat_value("CRIT_RATE", raw_cr)
    assert formatted_cr == "31.1%"

    # Level 0 FLAT_HP: raw float 717.0, displayed as "717"
    raw_hp = get_main_stat_value("FLAT_HP", 0, config=config)
    assert raw_hp == 717.0
    formatted_hp = format_stat_value("FLAT_HP", raw_hp)
    assert formatted_hp == "717"

    # Level 3 HP_PERCENT: raw float 12.9, displayed as "12.9%"
    raw_hp_pct = get_main_stat_value("HP_PERCENT", 3, config=config)
    assert raw_hp_pct == 12.9
    formatted_hp_pct = format_stat_value("HP_PERCENT", raw_hp_pct)
    assert formatted_hp_pct == "12.9%"


# ---------------------------------------------------------------------------
# 8. Property-Based Tests (Hypothesis)
# ---------------------------------------------------------------------------

@settings(max_examples=60, deadline=None)
@given(
    stat=st.sampled_from(sorted(VALID_MAIN_STATS)),
    level=st.integers(min_value=0, max_value=20),
)
def test_property_lookup_does_not_mutate_artifact_or_config(stat, level):
    """Lookup operations must be pure queries that never mutate the Artifact or ArtifactConfig."""
    config = load_artifact_config()
    config_snapshot = copy.deepcopy(config.main_stat_scaling)

    art = _make_dummy_artifact(main_stat=stat, level=level)
    art_snapshot = {
        "id": art.id,
        "rarity": art.rarity,
        "set_id": art.set_id,
        "slot": art.slot,
        "level": art.level,
        "main_stat": art.main_stat,
        "substats": [(s.slot_index, s.stat_type, s.state, s.initial_value, len(s.rolls)) for s in art.substats],
        "history": list(art.history),
    }

    # Perform lookups
    val_stat = get_main_stat_value(stat, level, config=config)
    val_art = get_main_stat_value(art, config=config)
    val_method = art.get_main_stat_value(config=config)
    val_cfg = config.get_main_stat_value(art)

    # Invariant: identical result across all access methods
    assert val_stat == val_art == val_method == val_cfg
    assert isinstance(val_stat, float)
    assert math.isfinite(val_stat)
    assert val_stat > 0

    # Invariant: Artifact was NOT mutated
    assert art.id == art_snapshot["id"]
    assert art.level == art_snapshot["level"]
    assert art.main_stat == art_snapshot["main_stat"]
    assert len(art.history) == len(art_snapshot["history"])
    for i, s in enumerate(art.substats):
        snap = art_snapshot["substats"][i]
        assert (s.slot_index, s.stat_type, s.state, s.initial_value, len(s.rolls)) == snap

    # Invariant: ArtifactConfig was NOT mutated
    assert config.main_stat_scaling == config_snapshot


@settings(max_examples=40, deadline=None)
@given(
    stat=st.sampled_from(sorted(VALID_MAIN_STATS)),
    l1=st.integers(min_value=0, max_value=19),
    l2=st.integers(min_value=1, max_value=20),
)
def test_property_strict_monotonicity(stat, l1, l2):
    """For any valid main stat, higher level strictly yields higher value."""
    if l1 >= l2:
        return
    config = load_artifact_config()
    v1 = get_main_stat_value(stat, l1, config=config)
    v2 = get_main_stat_value(stat, l2, config=config)
    assert v2 > v1, f"Monotonicity violation for {stat}: lvl {l1} ({v1}) >= lvl {l2} ({v2})"
