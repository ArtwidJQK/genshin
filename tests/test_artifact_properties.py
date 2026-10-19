"""Property-based tests for Artifact SPEC invariants."""
import re
from decimal import Decimal

import pytest
from hypothesis import given, settings, strategies as st

from app.core.artifact import (
    ALL_ARTIFACT_PROPERTIES,
    ArtifactEngine,
    ArtifactSlot,
    Substat,
    SubstatRoll,
    SubstatState,
    format_stat_value,
)
from app.core.rng.engine import PythonRNG

INTEGER_DISPLAY_STATS = {"FLAT_HP", "FLAT_ATK", "FLAT_DEF", "ELEMENTAL_MASTERY"}


@settings(max_examples=75, deadline=None)
@given(
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    slot=st.sampled_from(tuple(ArtifactSlot)),
    initial_lines=st.sampled_from((3, 4)),
    target_level=st.integers(min_value=0, max_value=20),
)
def test_artifact_generation_and_enhancement_invariants(seed, slot, initial_lines, target_level):
    """Every generated state preserves slot, exclusion, and milestone invariants."""
    engine = ArtifactEngine(rng=PythonRNG(seed=seed))
    artifact = engine.generate_artifact(
        slot=slot,
        initial_lines=initial_lines,
        artifact_id="hypothesis-artifact",
    )

    assert artifact.rarity == 5
    assert artifact.slot == slot
    assert len(artifact.substats) == 4
    assert len({substat.stat_type for substat in artifact.substats}) == 4
    assert artifact.main_stat not in {substat.stat_type for substat in artifact.substats}
    assert all(substat.slot_index == index for index, substat in enumerate(artifact.substats))
    assert all(substat.stat_type in engine.config.substat_weights for substat in artifact.substats)
    assert all(substat.initial_tier in engine.config.tier_weights for substat in artifact.substats)
    assert all(
        substat.initial_value == engine.config.roll_values[substat.stat_type][substat.initial_tier]
        for substat in artifact.substats
    )

    if slot == ArtifactSlot.FLOWER:
        assert artifact.main_stat == "FLAT_HP"
    elif slot == ArtifactSlot.PLUME:
        assert artifact.main_stat == "FLAT_ATK"

    if initial_lines == 3:
        assert [sub.state for sub in artifact.substats] == [
            SubstatState.ACTIVE,
            SubstatState.ACTIVE,
            SubstatState.ACTIVE,
            SubstatState.INACTIVE,
        ]
    else:
        assert all(sub.state == SubstatState.ACTIVE for sub in artifact.substats)

    expected_milestones = [level for level in (4, 8, 12, 16, 20) if level <= target_level]
    events = []
    if target_level > 0:
        events = engine.enhance_artifact(artifact, target_level=target_level)

    assert artifact.level == target_level
    assert [event.level for event in events] == expected_milestones
    assert artifact.history == events
    assert len(artifact.history) == len(expected_milestones)

    expected_rolls = len(expected_milestones)
    if initial_lines == 3 and target_level >= 4:
        expected_rolls -= 1  # +4 activates the pre-generated hidden line without a roll
    assert sum(len(sub.rolls) for sub in artifact.substats) == expected_rolls

    active_count = 4 if initial_lines == 4 or target_level >= 4 else 3
    assert len(artifact.active_substats) == active_count
    assert len(artifact.inactive_substats) == 4 - active_count

    for event in events:
        if initial_lines == 3 and event.level == 4:
            assert event.event_type == "ACTIVATION"
            assert event.increment == 0.0
            assert event.tier is None
            assert event.target_substat_index == 3
        else:
            assert event.event_type == "UPGRADE"
            assert 0 <= event.target_substat_index < 4
            target = artifact.substats[event.target_substat_index]
            assert event.stat_type == target.stat_type
            assert event.tier in engine.config.tier_weights
            assert event.increment == engine.config.roll_values[event.stat_type][event.tier]

    for substat in artifact.substats:
        assert substat.value == substat.initial_value + sum(roll.increment for roll in substat.rolls)
        assert all(roll.tier in engine.config.tier_weights for roll in substat.rolls)
        assert all(
            roll.increment == engine.config.roll_values[substat.stat_type][roll.tier]
            for roll in substat.rolls
        )


@settings(max_examples=50, deadline=None)
@given(
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    initial_lines=st.sampled_from((3, 4)),
    target_level=st.integers(min_value=0, max_value=20),
)
def test_artifact_sequence_is_reproducible_for_same_seed(seed, initial_lines, target_level):
    """Identical seed and inputs produce exactly the same artifact state and event trace."""
    engine_a = ArtifactEngine(rng=PythonRNG(seed=seed))
    engine_b = ArtifactEngine(rng=PythonRNG(seed=seed))
    artifact_a = engine_a.generate_artifact(initial_lines=initial_lines, artifact_id="same-id")
    artifact_b = engine_b.generate_artifact(initial_lines=initial_lines, artifact_id="same-id")

    events_a = engine_a.enhance_artifact(artifact_a, target_level) if target_level > 0 else []
    events_b = engine_b.enhance_artifact(artifact_b, target_level) if target_level > 0 else []

    assert events_a == events_b
    assert artifact_a == artifact_b


@settings(max_examples=100, deadline=None)
@given(
    stat_type=st.sampled_from(tuple(sorted(ALL_ARTIFACT_PROPERTIES))),
    value=st.floats(min_value=-1_000_000, max_value=1_000_000, allow_nan=False, allow_infinity=False),
)
def test_formatter_output_shape_for_every_property(stat_type, value):
    """Every supported property formats to the display precision prescribed by SPEC."""
    formatted = format_stat_value(stat_type, value)
    assert formatted == format_stat_value(stat_type, value)
    if stat_type in INTEGER_DISPLAY_STATS:
        assert re.fullmatch(r"-?\d+", formatted)
    else:
        assert re.fullmatch(r"-?\d+\.\d+%", formatted)


def test_formatter_uses_display_rounding_without_mutating_input():
    original = Decimal("3.85")
    assert format_stat_value("CRIT_RATE", original) == "3.9%"
    assert original == Decimal("3.85")
    assert format_stat_value("FLAT_HP", Decimal("298.75")) == "299"
    assert format_stat_value("ELEMENTAL_MASTERY", Decimal("23.31")) == "23"
    assert format_stat_value("CRIT_DMG", 5.44) == "5.4%"


def test_substat_value_keeps_full_precision_until_display():
    substat = Substat(
        slot_index=0,
        stat_type="FLAT_HP",
        state=SubstatState.ACTIVE,
        initial_value=1.00001,
        initial_tier="70%",
        rolls=[SubstatRoll(level=4, tier="70%", increment=0.00002)],
    )
    exact_sum = substat.initial_value + sum(roll.increment for roll in substat.rolls)
    assert substat.value == exact_sum
    assert substat.value != round(exact_sum, 4)
    assert format_stat_value("FLAT_HP", substat.value) == "1"


@pytest.mark.parametrize("stat_type", ["NOT_A_STAT", "", None])
def test_formatter_rejects_unknown_stat_identifier(stat_type):
    with pytest.raises(ValueError, match="Unsupported artifact stat type"):
        format_stat_value(stat_type, 1.0)


@pytest.mark.parametrize("value", [True, False, "3.5", None])
def test_formatter_rejects_non_numeric_input(value):
    with pytest.raises(TypeError, match="Stat value must be"):
        format_stat_value("CRIT_RATE", value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_formatter_rejects_non_finite_input(value):
    with pytest.raises(ValueError, match="must be finite"):
        format_stat_value("CRIT_RATE", value)
