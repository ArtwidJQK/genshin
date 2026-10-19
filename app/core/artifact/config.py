import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, TYPE_CHECKING

from app.core.artifact.models import (
    CANONICAL_SUBSTATS,
    VALID_MAIN_STATS,
    ArtifactSlot,
)

if TYPE_CHECKING:
    from app.core.artifact.models import Artifact

EXPECTED_TIERS = frozenset({"70%", "80%", "90%", "100%"})


@dataclass
class ArtifactConfig:
    """Strongly-typed container for all data-driven artifact configurations."""
    main_stats: Dict[ArtifactSlot, Dict[str, float]]
    substat_weights: Dict[str, float]
    roll_values: Dict[str, Dict[str, float]]
    tier_weights: Dict[str, float]
    initial_line_weights: Dict[int, float]
    rarity: int = 5
    num_substat_slots: int = 4
    max_level: int = 20
    milestone_levels: List[int] = field(default_factory=lambda: [4, 8, 12, 16, 20])
    main_stat_scaling: Optional[Dict[str, Dict[int, float]]] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate configuration integrity, weights, tiers, and stat consistency."""
        # 1. Rules validation
        if self.rarity != 5:
            raise ValueError(f"Configuration rarity must be 5, got {self.rarity}")
        if self.num_substat_slots != 4:
            raise ValueError(f"Configuration num_substat_slots must be 4, got {self.num_substat_slots}")
        if self.max_level != 20:
            raise ValueError(f"Configuration max_level must be 20, got {self.max_level}")
        if self.milestone_levels != [4, 8, 12, 16, 20]:
            raise ValueError(f"Configuration milestone_levels must be [4, 8, 12, 16, 20], got {self.milestone_levels}")

        # 2. Substat weights validation
        if set(self.substat_weights.keys()) != CANONICAL_SUBSTATS:
            diff = set(self.substat_weights.keys()).symmetric_difference(CANONICAL_SUBSTATS)
            raise ValueError(f"Substat weights must contain exactly the 10 canonical substats, mismatch: {diff}")

        substat_total = 0.0
        for stat, w in self.substat_weights.items():
            if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w):
                raise ValueError(f"Substat weight for '{stat}' must be a finite number, got {w}")
            if w < 0:
                raise ValueError(f"Substat weight for '{stat}' must be non-negative, got {w}")
            substat_total += w
        if substat_total <= 0:
            raise ValueError("Total substat weight must be strictly greater than 0")

        # 3. Main-stat weights validation
        if set(self.main_stats.keys()) != set(ArtifactSlot):
            diff = set(self.main_stats.keys()).symmetric_difference(set(ArtifactSlot))
            raise ValueError(f"Main stats configuration must define all artifact slots, mismatch: {diff}")

        for slot, stats in self.main_stats.items():
            if not stats:
                raise ValueError(f"Main stats for slot '{slot.value}' cannot be empty")
            slot_total = 0.0
            for stat, w in stats.items():
                if stat not in VALID_MAIN_STATS:
                    raise ValueError(f"Unsupported main stat identifier '{stat}' in slot '{slot.value}'")
                if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w):
                    raise ValueError(f"Main stat weight for '{stat}' in slot '{slot.value}' must be a finite number, got {w}")
                if w < 0:
                    raise ValueError(f"Main stat weight for '{stat}' in slot '{slot.value}' must be non-negative, got {w}")
                slot_total += w
            if slot_total <= 0:
                raise ValueError(f"Total main stat weight for slot '{slot.value}' must be strictly greater than 0")

        # 4. Roll tiers validation
        if set(self.tier_weights.keys()) != EXPECTED_TIERS:
            diff = set(self.tier_weights.keys()).symmetric_difference(EXPECTED_TIERS)
            raise ValueError(f"Roll tier weights must define exactly tiers {sorted(EXPECTED_TIERS)}, mismatch: {diff}")

        tier_total = 0.0
        for tier, w in self.tier_weights.items():
            if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w):
                raise ValueError(f"Tier weight for '{tier}' must be a finite number, got {w}")
            if w < 0:
                raise ValueError(f"Tier weight for '{tier}' must be non-negative, got {w}")
            tier_total += w
        if tier_total <= 0:
            raise ValueError("Total tier weight must be strictly greater than 0")

        # 5. Roll values validation
        if set(self.roll_values.keys()) != CANONICAL_SUBSTATS:
            diff = set(self.roll_values.keys()).symmetric_difference(CANONICAL_SUBSTATS)
            raise ValueError(f"Roll values must define entries for all canonical substats, mismatch: {diff}")

        for stat, tier_dict in self.roll_values.items():
            if set(tier_dict.keys()) != EXPECTED_TIERS:
                diff = set(tier_dict.keys()).symmetric_difference(EXPECTED_TIERS)
                raise ValueError(f"Roll values for '{stat}' must contain exactly tiers {sorted(EXPECTED_TIERS)}, mismatch: {diff}")
            for tier, val in tier_dict.items():
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                    raise ValueError(f"Roll value for '{stat}' at tier '{tier}' must be a finite number, got {val}")
                if val <= 0:
                    raise ValueError(f"Roll value for '{stat}' at tier '{tier}' must be strictly greater than 0, got {val}")

        # 6. Initial line distribution validation
        if set(self.initial_line_weights.keys()) != {3, 4}:
            raise ValueError(f"Initial line distribution must only define keys 3 and 4, got {set(self.initial_line_weights.keys())}")

        lines_total = 0.0
        for lines, w in self.initial_line_weights.items():
            if isinstance(w, bool) or not isinstance(w, (int, float)) or not math.isfinite(w):
                raise ValueError(f"Initial line weight for {lines}-line must be a finite number, got {w}")
            if w < 0:
                raise ValueError(f"Initial line weight for {lines}-line must be non-negative, got {w}")
            lines_total += w
        if lines_total <= 0:
            raise ValueError("Total initial line weight must be strictly greater than 0")

        # 7. Main stat scaling validation (if provided)
        if self.main_stat_scaling is not None:
            if set(self.main_stat_scaling.keys()) != VALID_MAIN_STATS:
                diff = set(self.main_stat_scaling.keys()).symmetric_difference(VALID_MAIN_STATS)
                raise ValueError(f"main_stat_scaling must contain exactly the 18 valid main stats, mismatch: {diff}")
            expected_levels = set(range(self.max_level + 1))
            for stat, levels in self.main_stat_scaling.items():
                if set(levels.keys()) != expected_levels:
                    diff = set(levels.keys()).symmetric_difference(expected_levels)
                    raise ValueError(f"main_stat_scaling['{stat}'] must contain levels 0-{self.max_level}, mismatch: {diff}")
                prev = None
                for lvl in range(self.max_level + 1):
                    val = levels[lvl]
                    if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
                        raise ValueError(f"main_stat_scaling['{stat}'][{lvl}] must be a finite number, got {val}")
                    if val <= 0:
                        raise ValueError(f"main_stat_scaling['{stat}'][{lvl}] must be strictly positive, got {val}")
                    if prev is not None and val <= prev:
                        raise ValueError(f"main_stat_scaling['{stat}'][{lvl}] ({val}) is not strictly greater than previous level ({prev})")
                    prev = val

            # Consistency check: verify that every main stat configured across all artifact slots
            # is accounted for in main_stat_scaling.
            all_slot_stats = set()
            for slot_stats in self.main_stats.values():
                all_slot_stats.update(slot_stats.keys())
            if all_slot_stats != set(self.main_stat_scaling.keys()):
                diff = all_slot_stats.symmetric_difference(set(self.main_stat_scaling.keys()))
                raise ValueError(f"Mismatch between configured slot main stats and main_stat_scaling: {diff}")

    def get_main_stat_value(
        self,
        target: Union["Artifact", str],
        level: Optional[int] = None,
    ) -> float:
        """Retrieve the exact numerical main stat value using this configuration.

        Args:
            target: Either an Artifact instance or a canonical 5★ main stat string.
            level: Artifact level in [0, 20]. Must be None if target is an Artifact;
                   required if target is a stat_type string.

        Returns:
            float: Exact unrounded internal floating-point value.
        """
        from app.core.artifact.scaling import get_main_stat_value
        return get_main_stat_value(target, level=level, config=self)


def load_artifact_config(config_dir: Union[Path, str, None] = None) -> ArtifactConfig:
    """Load and validate artifact configuration files from the specified or default directory."""
    if config_dir is None:
        base_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "artifacts"
    else:
        base_path = Path(config_dir)

    main_stats_path = base_path / "main_stats.json"
    substats_path = base_path / "substats.json"
    roll_values_path = base_path / "roll_values.json"
    rules_path = base_path / "rules.json"

    for p in (main_stats_path, substats_path, roll_values_path, rules_path):
        if not p.exists():
            raise FileNotFoundError(f"Required artifact configuration file not found: {p}")

    with open(main_stats_path, "r", encoding="utf-8") as f:
        main_stats_raw = json.load(f)

    with open(substats_path, "r", encoding="utf-8") as f:
        substats_raw = json.load(f)

    with open(roll_values_path, "r", encoding="utf-8") as f:
        roll_values_raw = json.load(f)

    with open(rules_path, "r", encoding="utf-8") as f:
        rules_raw = json.load(f)

    main_stats: Dict[ArtifactSlot, Dict[str, float]] = {}
    for slot_name, stats in main_stats_raw.items():
        try:
            slot_enum = ArtifactSlot(slot_name)
        except ValueError:
            raise ValueError(f"Invalid artifact slot in main_stats configuration: {slot_name}")
        main_stats[slot_enum] = {k: float(v) for k, v in stats.items()}

    substat_weights = {k: float(v) for k, v in substats_raw["weights"].items()}
    tier_weights = {k: float(v) for k, v in roll_values_raw["tier_weights"].items()}
    roll_values = roll_values_raw["values"]

    initial_line_weights = {int(k): float(v) for k, v in rules_raw["initial_line_count_weights"].items()}
    rarity = int(rules_raw.get("rarity", 5))
    num_substat_slots = int(rules_raw.get("num_substat_slots", 4))
    max_level = int(rules_raw.get("max_level", 20))
    milestone_levels = [int(x) for x in rules_raw.get("milestone_levels", [4, 8, 12, 16, 20])]

    main_stat_scaling_path = base_path / "main_stat_scaling.json"
    main_stat_scaling: Optional[Dict[str, Dict[int, float]]] = None
    if main_stat_scaling_path.exists():
        with open(main_stat_scaling_path, "r", encoding="utf-8") as f:
            scaling_raw = json.load(f)
        stats_dict = scaling_raw.get("stats", scaling_raw)
        main_stat_scaling = {
            stat: {int(k): float(v) for k, v in levels.items()}
            for stat, levels in stats_dict.items()
        }

    return ArtifactConfig(
        main_stats=main_stats,
        substat_weights=substat_weights,
        roll_values=roll_values,
        tier_weights=tier_weights,
        initial_line_weights=initial_line_weights,
        rarity=rarity,
        num_substat_slots=num_substat_slots,
        max_level=max_level,
        milestone_levels=milestone_levels,
        main_stat_scaling=main_stat_scaling,
    )


def load_and_validate_artifact_config(
    config_dir: Union[Path, str, None] = None,
    fidelity_mode: Optional[Union["FidelityMode", str]] = None,
) -> ArtifactConfig:
    """
    Load, validate against Pydantic schema, and check provenance fidelity mode.
    Raises ValueError if schemas are invalid or if constants violate the fidelity mode.
    """
    from app.core.artifact.schema import (
        FidelityMode,
        MainStatsConfigSchema,
        MainStatScalingConfigSchema,
        RollValuesConfigSchema,
        RulesConfigSchema,
        SubstatsConfigSchema,
        validate_config_provenance_fidelity,
    )

    if config_dir is None:
        base_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "artifacts"
    else:
        base_path = Path(config_dir)

    # 1. Validate raw JSON via Pydantic schemas
    with open(base_path / "main_stats.json", "r", encoding="utf-8") as f:
        MainStatsConfigSchema.model_validate(json.load(f))
    with open(base_path / "substats.json", "r", encoding="utf-8") as f:
        SubstatsConfigSchema.model_validate(json.load(f))
    with open(base_path / "roll_values.json", "r", encoding="utf-8") as f:
        RollValuesConfigSchema.model_validate(json.load(f))
    with open(base_path / "rules.json", "r", encoding="utf-8") as f:
        RulesConfigSchema.model_validate(json.load(f))
    scaling_path = base_path / "main_stat_scaling.json"
    if scaling_path.exists():
        with open(scaling_path, "r", encoding="utf-8") as f:
            MainStatScalingConfigSchema.model_validate(json.load(f))

    # 2. If fidelity_mode specified, validate against provenance records
    if fidelity_mode is not None:
        prov_path = base_path / "provenance.json"
        if not prov_path.exists():
            raise FileNotFoundError(f"Provenance catalog required for fidelity mode verification: {prov_path}")
        violations = validate_config_provenance_fidelity(prov_path, mode=fidelity_mode)
        if violations:
            mode_str = fidelity_mode.value if isinstance(fidelity_mode, FidelityMode) else str(fidelity_mode)
            raise ValueError(
                f"Configuration does not satisfy fidelity mode '{mode_str}'. "
                f"Violations ({len(violations)}):\n" + "\n".join(violations[:5])
            )

    return load_artifact_config(config_dir=base_path)

