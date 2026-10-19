from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import json
import math

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.artifact.models import CANONICAL_SUBSTATS, VALID_MAIN_STATS, ArtifactSlot


class EvidenceLevel(str, Enum):
    """Epistemological evidence classification according to AGENTS.md Section 5."""
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"


class FidelityMode(str, Enum):
    """Engine operational fidelity mode according to AGENTS.md Section 5.2."""
    STRICT = "strict"          # Only VERIFIED constants allowed
    BEST_EFFORT = "best_effort"  # VERIFIED and INFERRED allowed
    EXPERIMENTAL = "experimental"  # VERIFIED, INFERRED, and ASSUMED allowed


class ProvenanceRecord(BaseModel):
    """Mandatory provenance record for every game constant (AGENTS.md Section 5.1)."""
    model_config = ConfigDict(frozen=True)

    value: Any
    evidence: EvidenceLevel
    source: str
    retrieved_on: str
    valid_from_version: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("source")
    @classmethod
    def validate_source_not_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Provenance record source and exact locator must not be empty.")
        return clean

    def is_allowed_in_fidelity(self, mode: Union[FidelityMode, str]) -> bool:
        """Check if this constant's evidence level satisfies the target fidelity mode."""
        mode_enum = FidelityMode(mode) if isinstance(mode, str) else mode
        if self.evidence == EvidenceLevel.UNKNOWN:
            # UNKNOWN is never usable by the engine in any fidelity mode
            return False

        if mode_enum == FidelityMode.STRICT:
            return self.evidence == EvidenceLevel.VERIFIED
        elif mode_enum == FidelityMode.BEST_EFFORT:
            return self.evidence in (EvidenceLevel.VERIFIED, EvidenceLevel.INFERRED)
        elif mode_enum == FidelityMode.EXPERIMENTAL:
            return self.evidence in (
                EvidenceLevel.VERIFIED,
                EvidenceLevel.INFERRED,
                EvidenceLevel.ASSUMED,
            )
        return False


class MainStatsConfigSchema(BaseModel):
    """Pydantic validation schema for config/artifacts/main_stats.json."""
    model_config = ConfigDict(extra="forbid")

    FLOWER: Dict[str, float]
    PLUME: Dict[str, float]
    SANDS: Dict[str, float]
    GOBLET: Dict[str, float]
    CIRCLET: Dict[str, float]

    @model_validator(mode="after")
    def validate_main_stats(self) -> "MainStatsConfigSchema":
        for slot in ("FLOWER", "PLUME", "SANDS", "GOBLET", "CIRCLET"):
            weights = getattr(self, slot)
            if not weights:
                raise ValueError(f"Main stats pool for '{slot}' cannot be empty.")
            total = 0.0
            for stat, w in weights.items():
                if stat not in VALID_MAIN_STATS:
                    raise ValueError(f"Invalid main stat identifier '{stat}' in '{slot}'.")
                if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w):
                    raise ValueError(f"Weight for '{stat}' in '{slot}' must be a finite number.")
                if w < 0:
                    raise ValueError(f"Weight for '{stat}' in '{slot}' must be non-negative.")
                total += float(w)
            if total <= 0:
                raise ValueError(f"Total main stat weight for '{slot}' must be > 0.")
        return self


class SubstatsConfigSchema(BaseModel):
    """Pydantic validation schema for config/artifacts/substats.json."""
    model_config = ConfigDict(extra="forbid")

    weights: Dict[str, float]

    @model_validator(mode="after")
    def validate_substats(self) -> "SubstatsConfigSchema":
        if set(self.weights.keys()) != CANONICAL_SUBSTATS:
            diff = set(self.weights.keys()).symmetric_difference(CANONICAL_SUBSTATS)
            raise ValueError(f"Substat weights must define exactly the 10 canonical substats; mismatch: {diff}")
        total = 0.0
        for stat, w in self.weights.items():
            if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w):
                raise ValueError(f"Weight for '{stat}' must be a finite number.")
            if w < 0:
                raise ValueError(f"Weight for '{stat}' must be non-negative.")
            total += float(w)
        if total <= 0:
            raise ValueError("Total substat weight must be > 0.")
        return self


class RollValuesConfigSchema(BaseModel):
    """Pydantic validation schema for config/artifacts/roll_values.json."""
    model_config = ConfigDict(extra="forbid")

    tiers: List[str]
    tier_weights: Dict[str, float]
    values: Dict[str, Dict[str, float]]

    @model_validator(mode="after")
    def validate_roll_values(self) -> "RollValuesConfigSchema":
        expected_tiers = {"70%", "80%", "90%", "100%"}
        if set(self.tiers) != expected_tiers:
            raise ValueError(f"Tiers list must contain exactly {expected_tiers}")
        if set(self.tier_weights.keys()) != expected_tiers:
            raise ValueError(f"tier_weights must contain keys {expected_tiers}")
        if set(self.values.keys()) != CANONICAL_SUBSTATS:
            raise ValueError("values must define all 10 canonical substats.")
        for stat, tier_vals in self.values.items():
            if set(tier_vals.keys()) != expected_tiers:
                raise ValueError(f"Values for '{stat}' must contain tiers {expected_tiers}")
            for t, val in tier_vals.items():
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val <= 0:
                    raise ValueError(f"Roll value for '{stat}' at '{t}' must be positive and finite.")
        return self


class RulesConfigSchema(BaseModel):
    """Pydantic validation schema for config/artifacts/rules.json."""
    model_config = ConfigDict(extra="forbid")

    rarity: int = 5
    max_level: int = 20
    milestone_levels: List[int] = Field(default_factory=lambda: [4, 8, 12, 16, 20])
    num_substat_slots: int = 4
    initial_line_count_weights: Dict[str, float]

    @model_validator(mode="after")
    def validate_rules(self) -> "RulesConfigSchema":
        if self.rarity != 5:
            raise ValueError("Only 5-star artifacts are supported in this phase.")
        if self.num_substat_slots != 4:
            raise ValueError("5-star artifacts strictly have 4 substat slots.")
        if self.max_level != 20:
            raise ValueError("Max level must be 20.")
        if self.milestone_levels != [4, 8, 12, 16, 20]:
            raise ValueError("Milestone levels must be [4, 8, 12, 16, 20].")
        if set(self.initial_line_count_weights.keys()) != {"3", "4"}:
            raise ValueError("Initial line count weights must define keys '3' and '4'.")
        return self


class MainStatScalingConfigSchema(BaseModel):
    """Pydantic validation schema for config/artifacts/main_stat_scaling.json."""
    model_config = ConfigDict(extra="forbid")

    rarity: int = 5
    max_level: int = 20
    stats: Dict[str, Dict[str, float]]

    @model_validator(mode="after")
    def validate_scaling(self) -> "MainStatScalingConfigSchema":
        if self.rarity != 5:
            raise ValueError(f"Rarity must be 5, got {self.rarity}")
        if self.max_level != 20:
            raise ValueError(f"Max level must be 20, got {self.max_level}")
        if set(self.stats.keys()) != VALID_MAIN_STATS:
            diff = set(self.stats.keys()).symmetric_difference(VALID_MAIN_STATS)
            raise ValueError(f"Main stat scaling must define exactly the 18 valid main stats, mismatch: {diff}")
        expected_levels = {str(i) for i in range(self.max_level + 1)}
        for stat, levels in self.stats.items():
            if set(levels.keys()) != expected_levels:
                diff = set(levels.keys()).symmetric_difference(expected_levels)
                raise ValueError(f"Stat '{stat}' must contain levels 0-{self.max_level}, mismatch: {diff}")
            prev = None
            for i in range(self.max_level + 1):
                val = levels[str(i)]
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val <= 0:
                    raise ValueError(f"Value for '{stat}' at level {i} must be positive and finite, got {val}")
                if prev is not None and val <= prev:
                    raise ValueError(
                        f"Value for '{stat}' at level {i} ({val}) is not strictly greater than level {i-1} ({prev})"
                    )
                prev = val
        return self


def load_provenance_catalog(provenance_path: Union[Path, str]) -> Dict[str, Dict[str, ProvenanceRecord]]:
    """Load and parse the provenance catalog JSON file."""
    path = Path(provenance_path)
    if not path.exists():
        raise FileNotFoundError(f"Provenance catalog not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    catalog: Dict[str, Dict[str, ProvenanceRecord]] = {}
    for section, records in raw.items():
        catalog[section] = {}
        for key, entry in records.items():
            catalog[section][key] = ProvenanceRecord.model_validate(entry)
    return catalog


def validate_config_provenance_fidelity(
    provenance_path: Union[Path, str],
    mode: Union[FidelityMode, str] = FidelityMode.STRICT,
) -> List[str]:
    """
    Validate that all constants in the provenance catalog satisfy the target fidelity mode.
    Returns a list of violation messages (empty list if all constants satisfy the mode).
    """
    mode_enum = FidelityMode(mode) if isinstance(mode, str) else mode
    catalog = load_provenance_catalog(provenance_path)
    violations: List[str] = []

    for section, entries in catalog.items():
        for key, record in entries.items():
            if not record.is_allowed_in_fidelity(mode_enum):
                violations.append(
                    f"Constant '{section}.{key}' has evidence level '{record.evidence.value}', "
                    f"which is not permitted in fidelity mode '{mode_enum.value}'."
                )
    return violations
