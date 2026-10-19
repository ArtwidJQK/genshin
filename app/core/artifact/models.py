from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

CANONICAL_SUBSTATS = frozenset({
    "FLAT_HP",
    "FLAT_ATK",
    "FLAT_DEF",
    "HP_PERCENT",
    "ATK_PERCENT",
    "DEF_PERCENT",
    "ENERGY_RECHARGE",
    "ELEMENTAL_MASTERY",
    "CRIT_RATE",
    "CRIT_DMG",
})

# Flat DEF is never a valid main stat on any 5★ artifact slot in Genshin Impact.
# The valid 5★ main stat set contains exactly 18 properties.
VALID_MAIN_STATS = frozenset(
    (CANONICAL_SUBSTATS - {"FLAT_DEF"})
    | {
        "PHYSICAL_DMG_BONUS",
        "PYRO_DMG_BONUS",
        "HYDRO_DMG_BONUS",
        "CRYO_DMG_BONUS",
        "ELECTRO_DMG_BONUS",
        "ANEMO_DMG_BONUS",
        "GEO_DMG_BONUS",
        "DENDRO_DMG_BONUS",
        "HEALING_BONUS",
    }
)

ALL_ARTIFACT_PROPERTIES = frozenset(CANONICAL_SUBSTATS | VALID_MAIN_STATS)


class ArtifactSlot(str, Enum):
    FLOWER = "FLOWER"
    PLUME = "PLUME"
    SANDS = "SANDS"
    GOBLET = "GOBLET"
    CIRCLET = "CIRCLET"


class SubstatState(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass
class SubstatRoll:
    """Represents a single enhancement roll increment."""
    level: int
    tier: str
    increment: float


@dataclass
class Substat:
    """Represents one of the four conceptual substat slots on an artifact."""
    slot_index: int
    stat_type: str
    state: SubstatState
    initial_value: float
    initial_tier: str
    rolls: List[SubstatRoll] = field(default_factory=list)

    @property
    def value(self) -> float:
        """Total current value computed as initial value + all enhancement increments."""
        total = self.initial_value + sum(r.increment for r in self.rolls)
        return total


@dataclass
class EnhancementEvent:
    """Audit record capturing an enhancement step at +4, +8, +12, +16, or +20."""
    level: int
    event_type: str  # "ACTIVATION" or "UPGRADE"
    target_substat_index: int
    stat_type: str
    increment: float = 0.0
    tier: Optional[str] = None


@dataclass
class Artifact:
    """Represents a 5★ Artifact entity according to Artifact SPEC v1."""
    id: str
    rarity: int
    set_id: str
    slot: ArtifactSlot
    level: int
    main_stat: str
    substats: List[Substat]
    history: List[EnhancementEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate_state()

    def validate_state(self) -> None:
        """Validate all domain invariants for a 5★ Artifact.

        Checks include:
        - Rarity and level bounds.
        - Exactly 4 substat slots, each with valid enum state and slot_index.
        - No duplicate substat types; no substat matching main stat.
        - Inactive constraints (at most 1, must be slot 3, not allowed at level ≥ 4).
        - Roll integrity: INACTIVE substats must have zero roll records.
        - Total upgrade rolls must not exceed the physical maximum (5 for any 5★ artifact).
        """
        if self.rarity != 5:
            raise ValueError(f"Artifact SPEC v1 only supports 5★ artifacts, got rarity {self.rarity}")
        if not (0 <= self.level <= 20):
            raise ValueError(f"Artifact level must be between 0 and 20 inclusive, got {self.level}")
        if len(self.substats) != 4:
            raise ValueError(f"Artifact must have exactly 4 conceptual substat slots, got {len(self.substats)}")

        for idx, s in enumerate(self.substats):
            if not isinstance(s.state, SubstatState):
                raise ValueError(
                    f"Substat state at slot {idx} must be an instance of SubstatState enum, got {type(s.state).__name__}: {s.state!r}"
                )
            if s.state not in (SubstatState.ACTIVE, SubstatState.INACTIVE):
                raise ValueError(
                    f"Substat state at slot {idx} must be SubstatState.ACTIVE or SubstatState.INACTIVE, got {s.state!r}"
                )
            if s.slot_index != idx:
                raise ValueError(f"Substat slot_index mismatch at position {idx}: got {s.slot_index}")
            if s.stat_type not in CANONICAL_SUBSTATS:
                raise ValueError(f"Unsupported substat type: {s.stat_type}")

            # Roll integrity: an INACTIVE substat must have zero enhancement roll records.
            # (The 4th substat of a 3-line artifact is pre-generated but never rolled until active.)
            if s.state == SubstatState.INACTIVE and len(s.rolls) > 0:
                raise ValueError(
                    f"Substat at slot {idx} is INACTIVE but has {len(s.rolls)} roll record(s); "
                    "an inactive substat must have no enhancement rolls."
                )

        sub_types = [s.stat_type for s in self.substats]
        if len(set(sub_types)) != 4:
            raise ValueError(f"Duplicate substat types detected: {sub_types}")

        if self.main_stat not in VALID_MAIN_STATS:
            raise ValueError(f"Unsupported main stat type: {self.main_stat}")

        if self.main_stat in sub_types:
            raise ValueError(f"Main stat '{self.main_stat}' cannot appear in substats: {sub_types}")

        inactive_indices = [idx for idx, s in enumerate(self.substats) if s.state == SubstatState.INACTIVE]
        if len(inactive_indices) > 1:
            raise ValueError(f"Artifact cannot have more than 1 inactive substat, found {len(inactive_indices)}")
        if len(inactive_indices) == 1 and inactive_indices[0] != 3:
            raise ValueError(f"Only slot #4 (index 3) may be inactive, found inactive at index {inactive_indices[0]}")
        if self.level >= 4 and len(inactive_indices) > 0:
            raise ValueError(f"Artifact at level {self.level} cannot have an inactive substat")

        # Roll-count integrity: the physical maximum is 5 upgrade rolls per artifact
        # (4-line base: 5 upgrades across all milestones; 3-line base: 4 upgrades).
        # We enforce the hard upper bound of 5 here; the lower bound (4 for 3-line) is
        # verified by the enhancement state machine and history, not by validate_state alone.
        MAX_UPGRADE_ROLLS = 5
        total_rolls = sum(len(s.rolls) for s in self.substats)
        if total_rolls > MAX_UPGRADE_ROLLS:
            raise ValueError(
                f"Total enhancement roll count ({total_rolls}) exceeds the maximum allowed "
                f"({MAX_UPGRADE_ROLLS}) for a 5★ artifact."
            )

    @property
    def active_substats(self) -> List[Substat]:
        """Return all currently active substats."""
        return [s for s in self.substats if s.state == SubstatState.ACTIVE]

    @property
    def inactive_substats(self) -> List[Substat]:
        """Return all currently inactive/previewed substats."""
        return [s for s in self.substats if s.state == SubstatState.INACTIVE]

    def get_main_stat_value(self, config: Optional[Any] = None) -> float:
        """Return the exact unrounded numerical main stat value for this artifact at its current level."""
        from app.core.artifact.scaling import get_main_stat_value
        return get_main_stat_value(self, config=config)
