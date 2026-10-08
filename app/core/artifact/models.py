from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

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

VALID_MAIN_STATS = frozenset(
    CANONICAL_SUBSTATS
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
        return round(total, 4)


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
        """Validate all domain invariants for a 5★ Artifact."""
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

    @property
    def active_substats(self) -> List[Substat]:
        """Return all currently active substats."""
        return [s for s in self.substats if s.state == SubstatState.ACTIVE]

    @property
    def inactive_substats(self) -> List[Substat]:
        """Return all currently inactive/previewed substats."""
        return [s for s in self.substats if s.state == SubstatState.INACTIVE]
