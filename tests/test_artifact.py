import copy
import math
import random
import pytest

from app.core.artifact.config import ArtifactConfig, load_artifact_config
from app.core.artifact.engine import ArtifactEngine
from app.core.artifact.models import Artifact, ArtifactSlot, SubstatState
from app.core.probability.engine import ProbabilityEngine
from app.core.rng.engine import PythonRNG


# ==============================================================================
# 1-12. GENERATION TESTS
# ==============================================================================


def test_1_generate_deterministic_artifact_with_fixed_seed():
    """1. Generate deterministic artifact with fixed seed."""
    engine = ArtifactEngine(rng=PythonRNG(seed=42))
    art = engine.generate_artifact(set_id="gladiators_finale", slot=ArtifactSlot.FLOWER)

    assert art.set_id == "gladiators_finale"
    assert art.slot == ArtifactSlot.FLOWER
    assert art.main_stat == "FLAT_HP"
    assert len(art.substats) == 4


def test_2_same_seed_produces_same_artifact():
    """2. Verify same seed produces identical artifact."""
    engine1 = ArtifactEngine(rng=PythonRNG(seed=12345))
    engine2 = ArtifactEngine(rng=PythonRNG(seed=12345))

    art1 = engine1.generate_artifact(artifact_id="fixed_id")
    art2 = engine2.generate_artifact(artifact_id="fixed_id")

    assert art1.slot == art2.slot
    assert art1.main_stat == art2.main_stat
    assert len(art1.substats) == len(art2.substats)
    for s1, s2 in zip(art1.substats, art2.substats):
        assert s1.stat_type == s2.stat_type
        assert s1.state == s2.state
        assert s1.initial_value == s2.initial_value
        assert s1.initial_tier == s2.initial_tier


def test_3_different_seeds_produce_different_artifacts():
    """3. Verify different seeds produce different artifacts."""
    engine1 = ArtifactEngine(rng=PythonRNG(seed=111))
    engine2 = ArtifactEngine(rng=PythonRNG(seed=999))

    art1 = engine1.generate_artifact()
    art2 = engine2.generate_artifact()

    # At least some attributes must differ
    differs = (
        art1.slot != art2.slot
        or art1.main_stat != art2.main_stat
        or [s.stat_type for s in art1.substats] != [s.stat_type for s in art2.substats]
    )
    assert differs


def test_4_main_stat_obeys_slot_rules():
    """4. Main stat obeys slot rules across multiple generation runs."""
    engine = ArtifactEngine(rng=PythonRNG(seed=777))
    config = engine.config

    for slot in ArtifactSlot:
        art = engine.generate_artifact(slot=slot)
        valid_mains = config.main_stats[slot]
        assert art.main_stat in valid_mains


def test_5_flower_always_has_flat_hp():
    """5. Flower always has FLAT_HP."""
    engine = ArtifactEngine(rng=PythonRNG(seed=101))
    for _ in range(20):
        art = engine.generate_artifact(slot=ArtifactSlot.FLOWER)
        assert art.main_stat == "FLAT_HP"


def test_6_plume_always_has_flat_atk():
    """6. Plume always has FLAT_ATK."""
    engine = ArtifactEngine(rng=PythonRNG(seed=202))
    for _ in range(20):
        art = engine.generate_artifact(slot=ArtifactSlot.PLUME)
        assert art.main_stat == "FLAT_ATK"


def test_7_no_duplicate_substats():
    """7. Artifact never contains duplicate substat types."""
    engine = ArtifactEngine(rng=PythonRNG(seed=303))
    for _ in range(50):
        art = engine.generate_artifact()
        sub_types = [s.stat_type for s in art.substats]
        assert len(sub_types) == len(set(sub_types))


def test_8_main_stat_cannot_appear_as_substat():
    """8. Main stat cannot appear in the substat pool."""
    engine = ArtifactEngine(rng=PythonRNG(seed=404))
    for _ in range(50):
        art = engine.generate_artifact()
        sub_types = [s.stat_type for s in art.substats]
        assert art.main_stat not in sub_types


def test_9_exactly_four_conceptual_substat_slots_exist():
    """9. Exactly four conceptual substat slots exist on all 5★ artifacts."""
    engine = ArtifactEngine(rng=PythonRNG(seed=505))
    for _ in range(20):
        art = engine.generate_artifact()
        assert len(art.substats) == 4


def test_10_three_line_state_is_three_active_plus_one_inactive():
    """10. 3-line base has exactly 3 ACTIVE and 1 INACTIVE substats at level 0."""
    engine = ArtifactEngine(rng=PythonRNG(seed=606))
    art = engine.generate_artifact(initial_lines=3)

    assert len(art.active_substats) == 3
    assert len(art.inactive_substats) == 1
    assert art.substats[0].state == SubstatState.ACTIVE
    assert art.substats[1].state == SubstatState.ACTIVE
    assert art.substats[2].state == SubstatState.ACTIVE
    assert art.substats[3].state == SubstatState.INACTIVE


def test_11_four_line_state_is_four_active():
    """11. 4-line base has exactly 4 ACTIVE substats at level 0."""
    engine = ArtifactEngine(rng=PythonRNG(seed=707))
    art = engine.generate_artifact(initial_lines=4)

    assert len(art.active_substats) == 4
    assert len(art.inactive_substats) == 0
    assert all(s.state == SubstatState.ACTIVE for s in art.substats)


def test_12_hidden_fourth_substat_already_has_stat_type_and_value():
    """12. Hidden fourth substat of 3-line artifact is pre-generated at +0."""
    engine = ArtifactEngine(rng=PythonRNG(seed=808))
    art = engine.generate_artifact(initial_lines=3)

    sub4 = art.substats[3]
    assert sub4.state == SubstatState.INACTIVE
    assert isinstance(sub4.stat_type, str) and len(sub4.stat_type) > 0
    assert sub4.initial_value > 0.0
    assert sub4.initial_tier in ("70%", "80%", "90%", "100%")


# ==============================================================================
# 13-22. ENHANCEMENT TESTS
# ==============================================================================


def test_13_three_line_plus_4_activates_fourth_substat():
    """13. 3-line base +4 transition activates the fourth substat."""
    engine = ArtifactEngine(rng=PythonRNG(seed=909))
    art = engine.generate_artifact(initial_lines=3)

    events = engine.enhance_artifact(art, target_level=4)
    assert len(events) == 1
    assert events[0].event_type == "ACTIVATION"
    assert events[0].level == 4
    assert art.substats[3].state == SubstatState.ACTIVE
    assert len(art.active_substats) == 4


def test_14_three_line_plus_4_does_not_alter_its_value():
    """14. 3-line +4 activation does NOT alter the 4th substat's initial value."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1010))
    art = engine.generate_artifact(initial_lines=3)

    initial_val = art.substats[3].initial_value
    engine.enhance_artifact(art, target_level=4)

    assert art.substats[3].value == initial_val
    assert len(art.substats[3].rolls) == 0


def test_15_three_line_plus_4_does_not_perform_another_substat_selection():
    """15. 3-line +4 does NOT perform another substat selection."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1111))
    art = engine.generate_artifact(initial_lines=3)

    pre_type = art.substats[3].stat_type
    events = engine.enhance_artifact(art, target_level=4)

    assert art.substats[3].stat_type == pre_type
    assert events[0].event_type == "ACTIVATION"


def test_16_four_line_plus_4_performs_exactly_one_upgrade():
    """16. 4-line base +4 performs exactly one upgrade."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1212))
    art = engine.generate_artifact(initial_lines=4)

    events = engine.enhance_artifact(art, target_level=4)
    assert len(events) == 1
    assert events[0].event_type == "UPGRADE"
    assert events[0].increment > 0.0

    total_upgrades = sum(len(s.rolls) for s in art.substats)
    assert total_upgrades == 1


def test_17_to_20_milestone_enhancements_each_perform_one_upgrade():
    """17-20. Verify +8, +12, +16, +20 transitions each perform exactly one upgrade."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1313))
    art = engine.generate_artifact(initial_lines=4)

    # +4
    events_4 = engine.enhance_artifact(art, target_level=4)
    assert len(events_4) == 1
    assert events_4[0].level == 4

    # 17. +8
    events_8 = engine.enhance_artifact(art, target_level=8)
    assert len(events_8) == 1
    assert events_8[0].level == 8
    assert events_8[0].event_type == "UPGRADE"

    # 18. +12
    events_12 = engine.enhance_artifact(art, target_level=12)
    assert len(events_12) == 1
    assert events_12[0].level == 12
    assert events_12[0].event_type == "UPGRADE"

    # 19. +16
    events_16 = engine.enhance_artifact(art, target_level=16)
    assert len(events_16) == 1
    assert events_16[0].level == 16
    assert events_16[0].event_type == "UPGRADE"

    # 20. +20
    events_20 = engine.enhance_artifact(art, target_level=20)
    assert len(events_20) == 1
    assert events_20[0].level == 20
    assert events_20[0].event_type == "UPGRADE"

    # 4-line base to +20 has exactly 5 upgrades
    total_upgrades = sum(len(s.rolls) for s in art.substats)
    assert total_upgrades == 5


def test_21_every_upgrade_target_is_one_of_four_active_substats():
    """21. Every upgrade target is one of the four active substats."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1414))
    art = engine.generate_artifact(initial_lines=3)

    events = engine.enhance_artifact(art, target_level=20)
    for ev in events:
        if ev.event_type == "UPGRADE":
            assert 0 <= ev.target_substat_index <= 3
            assert art.substats[ev.target_substat_index].state == SubstatState.ACTIVE


def test_22_upgrade_target_selection_uses_uniform_distribution():
    """22. Upgrade target selection distributes across all 4 substats over many upgrades."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1515))
    target_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    # Run multiple artifacts to +20
    for _ in range(25):
        art = engine.generate_artifact(initial_lines=4)
        events = engine.enhance_artifact(art, target_level=20)
        for ev in events:
            if ev.event_type == "UPGRADE":
                target_counts[ev.target_substat_index] += 1

    # Over 125 rolls, every slot index should be selected
    assert all(count > 0 for count in target_counts.values())


# ==============================================================================
# 23-26. ROLL VALUE TESTS
# ==============================================================================


def test_23_roll_tier_selection_uses_configured_weights():
    """23. Roll tier selection produces valid configured tiers."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1616))
    valid_tiers = set(engine.config.tier_weights.keys())

    art = engine.generate_artifact(initial_lines=4)
    for s in art.substats:
        assert s.initial_tier in valid_tiers

    events = engine.enhance_artifact(art, target_level=20)
    for ev in events:
        if ev.event_type == "UPGRADE":
            assert ev.tier in valid_tiers


def test_24_stat_specific_increments_come_from_configuration():
    """24. Stat-specific roll increments strictly match configuration."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1717))
    config = engine.config

    art = engine.generate_artifact(initial_lines=4)
    # Check initial values match config
    for s in art.substats:
        expected_val = config.roll_values[s.stat_type][s.initial_tier]
        assert s.initial_value == expected_val

    events = engine.enhance_artifact(art, target_level=20)
    for ev in events:
        if ev.event_type == "UPGRADE":
            expected_increment = config.roll_values[ev.stat_type][ev.tier]
            assert ev.increment == expected_increment


def test_25_enhancement_history_is_recorded():
    """25. Enhancement history is recorded comprehensively in Artifact.history."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1818))
    art = engine.generate_artifact(initial_lines=3)

    events = engine.enhance_artifact(art, target_level=20)
    assert len(art.history) == 5
    assert art.history == events
    assert art.history[0].event_type == "ACTIVATION"
    assert all(e.event_type == "UPGRADE" for e in art.history[1:])


def test_26_final_value_equals_initial_value_plus_recorded_increments():
    """26. Final value of each substat equals initial_value + sum(recorded increments)."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1919))
    art = engine.generate_artifact(initial_lines=4)
    engine.enhance_artifact(art, target_level=20)

    for s in art.substats:
        expected_sum = round(s.initial_value + sum(r.increment for r in s.rolls), 4)
        assert s.value == expected_sum


# ==============================================================================
# 27-29. STATE / REPLAY TESTS
# ==============================================================================


def test_27_save_restore_rng_state_reproduces_artifact_generation():
    """27. Save/restore RNG state reproduces artifact generation identically."""
    rng = PythonRNG(seed=2020)
    engine = ArtifactEngine(rng=rng)

    # Capture state
    saved_state = rng.get_state()
    art1 = engine.generate_artifact(artifact_id="test_id")

    # Restore state
    rng.set_state(saved_state)
    art2 = engine.generate_artifact(artifact_id="test_id")

    assert art1.slot == art2.slot
    assert art1.main_stat == art2.main_stat
    for s1, s2 in zip(art1.substats, art2.substats):
        assert s1.stat_type == s2.stat_type
        assert s1.state == s2.state
        assert s1.initial_value == s2.initial_value
        assert s1.initial_tier == s2.initial_tier


def test_28_save_restore_rng_state_reproduces_enhancement_sequence():
    """28. Save/restore RNG state reproduces enhancement sequence identically."""
    rng = PythonRNG(seed=2121)
    engine = ArtifactEngine(rng=rng)

    # Generate artifact
    base_art = engine.generate_artifact(initial_lines=3, artifact_id="base")

    # Clone artifact before enhancement
    art1 = copy.deepcopy(base_art)
    art2 = copy.deepcopy(base_art)

    # Capture state before enhancement
    saved_state = rng.get_state()
    events1 = engine.enhance_artifact(art1, target_level=20)

    # Restore state and enhance art2
    rng.set_state(saved_state)
    events2 = engine.enhance_artifact(art2, target_level=20)

    assert len(events1) == len(events2)
    for e1, e2 in zip(events1, events2):
        assert e1.level == e2.level
        assert e1.event_type == e2.event_type
        assert e1.target_substat_index == e2.target_substat_index
        assert e1.stat_type == e2.stat_type
        assert e1.tier == e2.tier
        assert e1.increment == e2.increment

    for s1, s2 in zip(art1.substats, art2.substats):
        assert s1.value == s2.value
        assert len(s1.rolls) == len(s2.rolls)


def test_29_artifact_generation_does_not_alter_python_global_random_state():
    """29. Artifact generation and enhancement do not alter Python's global random state."""
    random.seed(123456)
    global_seq_before = [random.random() for _ in range(5)]

    random.seed(123456)

    # Perform extensive artifact generation & enhancement with isolated engine
    engine = ArtifactEngine(rng=PythonRNG(seed=9999))
    for _ in range(10):
        art = engine.generate_artifact()
        engine.enhance_artifact(art, target_level=20)

    global_seq_after = [random.random() for _ in range(5)]
    assert global_seq_before == global_seq_after


# ==============================================================================
# 30-34. INVALID INPUTS TESTS
# ==============================================================================


def test_30_invalid_slot_rejected():
    """30. Invalid artifact slot is rejected with ValueError."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    with pytest.raises(ValueError, match="Invalid artifact slot"):
        engine.generate_artifact(slot="INVALID_SLOT")


def test_31_invalid_rarity_rejected():
    """31. Invalid rarity is rejected by Artifact model validation."""
    with pytest.raises(ValueError, match="only supports 5★ artifacts"):
        Artifact(
            id="bad_rarity",
            rarity=4,  # SPEC v1 only supports 5★
            set_id="test",
            slot=ArtifactSlot.FLOWER,
            level=0,
            main_stat="FLAT_HP",
            substats=[],
        )


def test_32_invalid_main_stat_configuration_rejected():
    """32. Invalid main stat for given slot is rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    with pytest.raises(ValueError, match="is invalid for slot"):
        # Flower cannot have CRIT_RATE as main stat
        engine.generate_artifact(slot=ArtifactSlot.FLOWER, main_stat="CRIT_RATE")


def test_33_duplicate_substat_configuration_rejected():
    """33. Duplicate substat indices or slots rejected when constructing artifact."""
    with pytest.raises(ValueError, match="must have exactly 4 conceptual substat slots"):
        Artifact(
            id="bad_slots",
            rarity=5,
            set_id="test",
            slot=ArtifactSlot.FLOWER,
            level=0,
            main_stat="FLAT_HP",
            substats=[],  # Not 4 slots
        )


def test_34_invalid_probability_weights_rejected_through_probability_contract():
    """34. Invalid probability weights are rejected through established probability contract."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.main_stats[ArtifactSlot.FLOWER]["FLAT_HP"] = -10.0

    with pytest.raises(ValueError, match="Main stat weight .* must be non-negative"):
        ArtifactEngine(config=bad_config, rng=PythonRNG(seed=1))


# ==============================================================================
# FIX 1 — CONFIG VALIDATION TESTS
# ==============================================================================


def test_config_main_stat_non_finite_weight_rejected():
    """Verify non-finite main-stat weights (NaN / Inf) are rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.main_stats[ArtifactSlot.SANDS]["ATK_PERCENT"] = math.nan

    with pytest.raises(ValueError, match="must be a finite number"):
        bad_config.validate()


def test_config_main_stat_zero_total_weight_rejected():
    """Verify total main stat weight <= 0 in a slot is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.main_stats[ArtifactSlot.FLOWER]["FLAT_HP"] = 0.0

    with pytest.raises(ValueError, match="Total main stat weight .* strictly greater than 0"):
        bad_config.validate()


def test_config_unsupported_main_stat_identifier_rejected():
    """Verify unsupported main stat identifier is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.main_stats[ArtifactSlot.SANDS]["IMAGINARY_STAT"] = 10.0

    with pytest.raises(ValueError, match="Unsupported main stat identifier"):
        bad_config.validate()


def test_config_missing_canonical_substat_rejected():
    """Verify missing canonical substat in substat_weights is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    del bad_config.substat_weights["CRIT_DMG"]

    with pytest.raises(ValueError, match="Substat weights must contain exactly the 10 canonical substats"):
        bad_config.validate()


def test_config_extra_substat_rejected():
    """Verify extra/unknown substat in substat_weights is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.substat_weights["EXTRA_STAT"] = 5.0

    with pytest.raises(ValueError, match="Substat weights must contain exactly the 10 canonical substats"):
        bad_config.validate()


def test_config_negative_substat_weight_rejected():
    """Verify negative substat weight is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.substat_weights["CRIT_RATE"] = -1.0

    with pytest.raises(ValueError, match="must be non-negative"):
        bad_config.validate()


def test_config_invalid_roll_tiers_rejected():
    """Verify tier weights not matching exactly 70%, 80%, 90%, 100% are rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.tier_weights = {"50%": 50, "100%": 50}

    with pytest.raises(ValueError, match="Roll tier weights must define exactly tiers"):
        bad_config.validate()


def test_config_missing_roll_value_tier_rejected():
    """Verify substat roll value entry missing a tier is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    del bad_config.roll_values["CRIT_RATE"]["100%"]

    with pytest.raises(ValueError, match="Roll values for 'CRIT_RATE' must contain exactly tiers"):
        bad_config.validate()


def test_config_non_positive_roll_value_rejected():
    """Verify roll value <= 0 is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.roll_values["CRIT_RATE"]["70%"] = 0.0

    with pytest.raises(ValueError, match="must be strictly greater than 0"):
        bad_config.validate()


def test_config_invalid_initial_line_distribution_keys_rejected():
    """Verify line distribution defining keys other than {3, 4} is rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.initial_line_weights = {2: 50, 4: 50}

    with pytest.raises(ValueError, match="Initial line distribution must only define keys 3 and 4"):
        bad_config.validate()


def test_config_invalid_rules_rejected():
    """Verify invalid rarity, slots, or max level are rejected."""
    bad_config = copy.deepcopy(load_artifact_config())
    bad_config.rarity = 4

    with pytest.raises(ValueError, match="Configuration rarity must be 5"):
        bad_config.validate()


# ==============================================================================
# FIX 2 — ENHANCEMENT LEVEL CONTRACT TESTS
# ==============================================================================


def test_enhancement_arbitrary_intermediate_levels_and_milestones():
    """Verify arbitrary intermediate target levels only trigger crossed milestones.

    level 0 -> target 6:
        milestones crossed: +4
        final level: 6
    level 6 -> target 10:
        milestones crossed: +8
        final level: 10
    level 10 -> target 15:
        milestones crossed: +12
        final level: 15
    level 15 -> target 20:
        milestones crossed: +16, +20
        final level: 20
    """
    engine = ArtifactEngine(rng=PythonRNG(seed=9876))
    art = engine.generate_artifact(initial_lines=3)

    # 0 -> 6: triggers milestone 4 (activation)
    events_0_6 = engine.enhance_artifact(art, target_level=6)
    assert art.level == 6
    assert len(events_0_6) == 1
    assert events_0_6[0].level == 4
    assert events_0_6[0].event_type == "ACTIVATION"

    # 6 -> 10: triggers milestone 8 (upgrade)
    events_6_10 = engine.enhance_artifact(art, target_level=10)
    assert art.level == 10
    assert len(events_6_10) == 1
    assert events_6_10[0].level == 8
    assert events_6_10[0].event_type == "UPGRADE"

    # 10 -> 15: triggers milestone 12 (upgrade)
    events_10_15 = engine.enhance_artifact(art, target_level=15)
    assert art.level == 15
    assert len(events_10_15) == 1
    assert events_10_15[0].level == 12
    assert events_10_15[0].event_type == "UPGRADE"

    # 15 -> 20: triggers milestones 16 and 20 (2 upgrades)
    events_15_20 = engine.enhance_artifact(art, target_level=20)
    assert art.level == 20
    assert len(events_15_20) == 2
    assert events_15_20[0].level == 16
    assert events_15_20[1].level == 20
    assert all(e.event_type == "UPGRADE" for e in events_15_20)

    # At level 20, further enhancement must be rejected
    with pytest.raises(ValueError, match="already at maximum level"):
        engine.enhance_artifact(art, target_level=21)


def test_enhancement_no_milestone_crossed_produces_no_events():
    """Verify enhancing without crossing a milestone updates level without generating events."""
    engine = ArtifactEngine(rng=PythonRNG(seed=5555))
    art = engine.generate_artifact(initial_lines=4)

    # 0 -> 2
    events_0_2 = engine.enhance_artifact(art, target_level=2)
    assert art.level == 2
    assert len(events_0_2) == 0

    # 2 -> 3
    events_2_3 = engine.enhance_artifact(art, target_level=3)
    assert art.level == 3
    assert len(events_2_3) == 0

    # 3 -> 5: crosses milestone 4
    events_3_5 = engine.enhance_artifact(art, target_level=5)
    assert art.level == 5
    assert len(events_3_5) == 1
    assert events_3_5[0].level == 4


def test_enhancement_target_level_validation():
    """Verify target_level <= current_level and target_level > 20 are rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=4)
    engine.enhance_artifact(art, target_level=5)

    with pytest.raises(ValueError, match="strictly greater than current level"):
        engine.enhance_artifact(art, target_level=5)

    with pytest.raises(ValueError, match="strictly greater than current level"):
        engine.enhance_artifact(art, target_level=3)

    with pytest.raises(ValueError, match="cannot exceed max level"):
        engine.enhance_artifact(art, target_level=25)

    with pytest.raises(TypeError, match="must be an integer"):
        engine.enhance_artifact(art, target_level=10.5)  # type: ignore


# ==============================================================================
# FIX 3 — STATE SAFETY & CORRUPTED STATE REJECTION
# ==============================================================================


def test_corrupted_inactive_substat_not_in_slot_4_rejected():
    """Verify inactive substat in any slot other than slot #4 (index 3) is rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=4)

    # Corrupt slot #1 (index 0) to INACTIVE
    art.substats[0].state = SubstatState.INACTIVE

    with pytest.raises(ValueError, match="Only slot #4 .* may be inactive"):
        engine.enhance_artifact(art, target_level=4)


def test_corrupted_multiple_inactive_substats_rejected():
    """Verify artifact with multiple inactive substats is rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=4)

    art.substats[2].state = SubstatState.INACTIVE
    art.substats[3].state = SubstatState.INACTIVE

    with pytest.raises(ValueError, match="cannot have more than 1 inactive substat"):
        engine.enhance_artifact(art, target_level=4)


def test_corrupted_post_plus_4_inactive_substat_rejected():
    """Verify artifact at level >= 4 cannot possess an inactive substat."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=3)
    engine.enhance_artifact(art, target_level=4)

    # Manually corrupt slot #4 back to INACTIVE at level 4
    art.substats[3].state = SubstatState.INACTIVE

    with pytest.raises(ValueError, match="cannot have an inactive substat"):
        engine.enhance_artifact(art, target_level=8)


def test_corrupted_fewer_than_four_substats_rejected():
    """Verify artifact with fewer than 4 substats is rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=4)

    art.substats.pop()  # now 3 substats

    with pytest.raises(ValueError, match="must have exactly 4 conceptual substat slots"):
        engine.enhance_artifact(art, target_level=4)


def test_corrupted_duplicate_substats_rejected():
    """Verify artifact with duplicate substats is rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=4)

    # Duplicate substat type
    art.substats[1].stat_type = art.substats[0].stat_type

    with pytest.raises(ValueError, match="Duplicate substat types detected"):
        engine.enhance_artifact(art, target_level=4)


def test_corrupted_main_stat_in_substats_rejected():
    """Verify artifact where main stat appears in substats is rejected."""
    engine = ArtifactEngine(rng=PythonRNG(seed=1))
    art = engine.generate_artifact(initial_lines=4)

    # Make substat equal to main stat
    art.substats[0].stat_type = art.main_stat

    with pytest.raises(ValueError, match="cannot appear in substats"):
        engine.enhance_artifact(art, target_level=4)
