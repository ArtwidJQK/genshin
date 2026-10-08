from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


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
        if self.rarity != 5:
            raise ValueError(f"Artifact SPEC v1 only supports 5★ artifacts, got rarity {self.rarity}")
        if len(self.substats) != 4:
            raise ValueError(f"Artifact must have exactly 4 conceptual substat slots, got {len(self.substats)}")

    @property
    def active_substats(self) -> List[Substat]:
        """Return all currently active substats."""
        return [s for s in self.substats if s.state == SubstatState.ACTIVE]

    @property
    def inactive_substats(self) -> List[Substat]:
        """Return all currently inactive/previewed substats."""
        return [s for s in self.substats if s.state == SubstatState.INACTIVE]
