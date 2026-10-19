"""Layer 2: Domain invariant and logic unit tests for Artifact Loot Sources.

Satisfies:
- P3 Spec Section 9.2
- ADR-002 Decisions 1A, 2A, 3A, 4A
- AGENTS.md Section 9 & 10 (domain invariants, input validation, strict fidelity refusal)
"""

from typing import List
import pytest

from app.core.artifact.engine import ArtifactEngine
from app.core.artifact.loot import (
    DomainDropResult,
    FidelityViolationError,
    LootAuditEvent,
    LootFidelityMode,
    LootSourceType,
    StrongboxResult,
    craft_strongbox,
    run_domain_of_blessing,
)
from app.core.artifact.models import Artifact, ArtifactSlot, Substat, SubstatRoll, SubstatState
from app.core.rng.engine import PythonRNG


def _create_dummy_5star_artifact(art_id: str = "art_1") -> Artifact:
    """Create a minimal valid 5★ Artifact instance."""
    substats = [
        Substat(
            slot_index=0,
            stat_type="CRIT_RATE",
            state=SubstatState.ACTIVE,
            initial_value=3.9,
            initial_tier="100%",
            rolls=[],
        ),
        Substat(
            slot_index=1,
            stat_type="CRIT_DMG",
            state=SubstatState.ACTIVE,
            initial_value=7.8,
            initial_tier="100%",
            rolls=[],
        ),
        Substat(
            slot_index=2,
            stat_type="ATK_PERCENT",
            state=SubstatState.ACTIVE,
            initial_value=5.8,
            initial_tier="100%",
            rolls=[],
        ),
        Substat(
            slot_index=3,
            stat_type="ENERGY_RECHARGE",
            state=SubstatState.INACTIVE,
            initial_value=6.5,
            initial_tier="100%",
            rolls=[],
        ),
    ]
    return Artifact(
        id=art_id,
        rarity=5,
        set_id="gladiators_finale",
        slot=ArtifactSlot.FLOWER,
        level=0,
        main_stat="FLAT_HP",
        substats=substats,
    )


# ==============================================================================
# 1. Strongbox Validation Invariants (Decision 3A)
# ==============================================================================

def test_strongbox_rejects_non_list_inputs():
    """Strongbox rejects non-list sacrifice inputs with TypeError."""
    with pytest.raises(TypeError, match="must be a list of Artifact instances"):
        craft_strongbox("noblesse_oblige", "not a list")  # type: ignore

    with pytest.raises(TypeError, match="must be a list of Artifact instances"):
        craft_strongbox("noblesse_oblige", None)  # type: ignore

    with pytest.raises(TypeError, match="must be a list of Artifact instances"):
        dummy = _create_dummy_5star_artifact()
        craft_strongbox("noblesse_oblige", (dummy, dummy, dummy))  # type: ignore


def test_strongbox_rejects_fewer_than_three_artifacts():
    """Strongbox requires at least 3 artifacts to craft."""
    dummy = _create_dummy_5star_artifact()

    with pytest.raises(ValueError, match="at least 3 artifacts"):
        craft_strongbox("noblesse_oblige", [])

    with pytest.raises(ValueError, match="at least 3 artifacts"):
        craft_strongbox("noblesse_oblige", [dummy])

    with pytest.raises(ValueError, match="at least 3 artifacts"):
        craft_strongbox("noblesse_oblige", [dummy, dummy])


def test_strongbox_rejects_non_multiple_of_three():
    """Strongbox requires sacrifice count to be an exact multiple of 3."""
    dummy = _create_dummy_5star_artifact()

    with pytest.raises(ValueError, match="exact multiple of 3"):
        craft_strongbox("noblesse_oblige", [dummy] * 4)

    with pytest.raises(ValueError, match="exact multiple of 3"):
        craft_strongbox("noblesse_oblige", [dummy] * 5)

    with pytest.raises(ValueError, match="exact multiple of 3"):
        craft_strongbox("noblesse_oblige", [dummy] * 7)


def test_strongbox_rejects_non_5star_artifacts():
    """Strongbox rejects non-5★ artifacts, naming the offending artifact in the error message."""
    valid_1 = _create_dummy_5star_artifact("art_valid_1")
    valid_2 = _create_dummy_5star_artifact("art_valid_2")

    # Construct a 4★ artifact by bypassing validation or creating a minimal dummy
    invalid_4star = _create_dummy_5star_artifact("art_4star_offender")
    # Using object.__setattr__ because Artifact might validate rarity in __post_init__
    object.__setattr__(invalid_4star, "rarity", 4)

    with pytest.raises(ValueError, match="only accepts 5★ artifacts") as exc_info:
        craft_strongbox("noblesse_oblige", [valid_1, valid_2, invalid_4star])

    assert "art_4star_offender" in str(exc_info.value)
    assert "4" in str(exc_info.value)


def test_strongbox_rejects_empty_target_set():
    """Strongbox rejects empty or whitespace target_set."""
    dummy_list = [_create_dummy_5star_artifact(f"art_{i}") for i in range(3)]

    with pytest.raises(ValueError, match="target_set must not be empty"):
        craft_strongbox("", dummy_list)

    with pytest.raises(ValueError, match="target_set must not be empty"):
        craft_strongbox("   ", dummy_list)


def test_strongbox_input_list_not_mutated():
    """Strongbox execution does not mutate the passed sacrifice_artifacts list."""
    original_list = [_create_dummy_5star_artifact(f"art_{i}") for i in range(6)]
    copied_list = list(original_list)

    res = craft_strongbox("noblesse_oblige", original_list)
    assert len(original_list) == len(copied_list) == 6
    assert original_list == copied_list
    assert len(res.artifacts) == 2


def test_strongbox_exact_three_to_one_ratio():
    """Strongbox produces exactly len(sacrifices) // 3 artifacts, all belonging to target_set."""
    sacrifices = [_create_dummy_5star_artifact(f"art_{i}") for i in range(12)]
    res = craft_strongbox("crimson_witch_of_flames", sacrifices)

    assert res.sacrificed_count == 12
    assert len(res.artifacts) == 4
    assert res.target_set == "crimson_witch_of_flames"
    for art in res.artifacts:
        assert art.set_id == "crimson_witch_of_flames"
        assert art.rarity == 5
        assert art.level == 0


# ==============================================================================
# 2. Domain Execution Invariants
# ==============================================================================

def test_domain_rejects_invalid_sets():
    """Domain requires exactly 2 distinct 5★ sets."""
    with pytest.raises(ValueError, match="exactly 2 distinct 5★ sets"):
        run_domain_of_blessing(sets=("only_one_set",))  # type: ignore

    with pytest.raises(ValueError, match="exactly 2 distinct 5★ sets"):
        run_domain_of_blessing(sets=("set_a", "set_b", "set_c"))  # type: ignore

    with pytest.raises(ValueError, match="exactly 2 distinct 5★ sets"):
        run_domain_of_blessing(sets=("set_duplicate", "set_duplicate"))


def test_domain_resin_and_run_counts():
    """Domain correctly records resin_spent and runs_executed for normal vs condensed runs."""
    normal_res = run_domain_of_blessing(use_condensed=False)
    assert normal_res.resin_spent == 20
    assert normal_res.runs_executed == 1
    assert len(normal_res.artifacts) in (1, 2)

    condensed_res = run_domain_of_blessing(use_condensed=True)
    assert condensed_res.resin_spent == 40
    assert condensed_res.runs_executed == 2
    assert len(condensed_res.artifacts) in (2, 3, 4)


def test_domain_fodder_integer_invariants():
    """Domain 4★ fodder is strictly an integer satisfying empirical bounds (2-3 per 20 resin)."""
    engine = ArtifactEngine(rng=PythonRNG(seed=12345))

    for _ in range(50):
        res_normal = run_domain_of_blessing(use_condensed=False, engine=engine)
        assert isinstance(res_normal.count_4star_fodder, int)
        assert 2 <= res_normal.count_4star_fodder <= 3

        res_condensed = run_domain_of_blessing(use_condensed=True, engine=engine)
        assert isinstance(res_condensed.count_4star_fodder, int)
        assert 4 <= res_condensed.count_4star_fodder <= 6


def test_domain_generated_artifacts_satisfy_spec_invariants():
    """Every generated artifact strictly satisfies Artifact SPEC v1 invariants."""
    engine = ArtifactEngine(rng=PythonRNG(seed=999))
    res = run_domain_of_blessing(
        sets=("viridescent_venerer", "maiden_beloved"),
        use_condensed=True,
        engine=engine,
    )

    for art in res.artifacts:
        assert art.rarity == 5
        assert art.level == 0
        assert art.set_id in ("viridescent_venerer", "maiden_beloved")
        assert art.slot in set(ArtifactSlot)
        assert len(art.substats) == 4

        # Validate no duplicate substat types
        stat_types = [s.stat_type for s in art.substats]
        assert len(stat_types) == len(set(stat_types))

        # Substat cannot equal main stat
        assert art.main_stat not in stat_types

        # Valid initial states: 3 ACTIVE + 1 INACTIVE, or 4 ACTIVE
        active_count = sum(1 for s in art.substats if s.state == SubstatState.ACTIVE)
        inactive_count = sum(1 for s in art.substats if s.state == SubstatState.INACTIVE)
        assert (active_count == 3 and inactive_count == 1) or (active_count == 4 and inactive_count == 0)


# ==============================================================================
# 3. Fidelity Mode & Refusal Invariants (F1)
# ==============================================================================

def test_strict_fidelity_mode_refusal_invariant():
    """STRICT fidelity mode unconditionally raises FidelityViolationError without silent bypass."""
    # 1. Domain refusal
    with pytest.raises(FidelityViolationError, match="Cannot execute DOMAIN_OF_BLESSING in STRICT fidelity mode"):
        run_domain_of_blessing(fidelity_mode=LootFidelityMode.STRICT)

    with pytest.raises(FidelityViolationError, match="Cannot execute DOMAIN_OF_BLESSING in STRICT fidelity mode"):
        run_domain_of_blessing(fidelity_mode="strict")

    with pytest.raises(FidelityViolationError, match="Cannot execute DOMAIN_OF_BLESSING in STRICT fidelity mode"):
        run_domain_of_blessing(fidelity_mode="STRICT")

    # 2. Strongbox refusal
    dummy_list = [_create_dummy_5star_artifact(f"art_{i}") for i in range(3)]
    with pytest.raises(FidelityViolationError, match="Cannot execute ARTIFACT_STRONGBOX in STRICT fidelity mode"):
        craft_strongbox("noblesse_oblige", dummy_list, fidelity_mode=LootFidelityMode.STRICT)

    with pytest.raises(FidelityViolationError, match="Cannot execute ARTIFACT_STRONGBOX in STRICT fidelity mode"):
        craft_strongbox("noblesse_oblige", dummy_list, fidelity_mode="strict")


def test_best_effort_mode_labels_weakest_evidence_level_inferred():
    """BEST_EFFORT mode executes empirical models and truthfully reports INFERRED evidence level."""
    res_domain = run_domain_of_blessing(fidelity_mode=LootFidelityMode.BEST_EFFORT)
    assert res_domain.fidelity_mode == LootFidelityMode.BEST_EFFORT
    assert res_domain.weakest_evidence_level == "INFERRED"

    dummy_list = [_create_dummy_5star_artifact(f"art_{i}") for i in range(3)]
    res_strongbox = craft_strongbox("noblesse_oblige", dummy_list, fidelity_mode="best_effort")
    assert res_strongbox.fidelity_mode == LootFidelityMode.BEST_EFFORT
    assert res_strongbox.weakest_evidence_level == "INFERRED"


def test_experimental_mode_labels_weakest_evidence_level_experimental():
    """EXPERIMENTAL mode allows research overrides and truthfully reports EXPERIMENTAL."""
    res_domain = run_domain_of_blessing(fidelity_mode=LootFidelityMode.EXPERIMENTAL)
    assert res_domain.fidelity_mode == LootFidelityMode.EXPERIMENTAL
    assert res_domain.weakest_evidence_level == "EXPERIMENTAL"

    dummy_list = [_create_dummy_5star_artifact(f"art_{i}") for i in range(3)]
    res_strongbox = craft_strongbox("noblesse_oblige", dummy_list, fidelity_mode="experimental")
    assert res_strongbox.fidelity_mode == LootFidelityMode.EXPERIMENTAL
    assert res_strongbox.weakest_evidence_level == "EXPERIMENTAL"
