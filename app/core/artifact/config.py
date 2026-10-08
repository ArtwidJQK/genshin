import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union

from app.core.artifact.models import ArtifactSlot


@dataclass
class ArtifactConfig:
    """Strongly-typed container for all data-driven artifact configurations."""
    main_stats: Dict[ArtifactSlot, Dict[str, float]]
    substat_weights: Dict[str, float]
    roll_values: Dict[str, Dict[str, float]]
    tier_weights: Dict[str, float]
    initial_line_weights: Dict[int, float]
    max_level: int = 20
    milestone_levels: List[int] = field(default_factory=lambda: [4, 8, 12, 16, 20])


def load_artifact_config(config_dir: Union[Path, str, None] = None) -> ArtifactConfig:
    """Load and validate artifact configuration files from the specified or default directory."""
    if config_dir is None:
        # Default to project_root/config/artifacts
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

    # Convert main_stats slot keys to ArtifactSlot enum
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
    max_level = int(rules_raw.get("max_level", 20))
    milestone_levels = [int(x) for x in rules_raw.get("milestone_levels", [4, 8, 12, 16, 20])]

    return ArtifactConfig(
        main_stats=main_stats,
        substat_weights=substat_weights,
        roll_values=roll_values,
        tier_weights=tier_weights,
        initial_line_weights=initial_line_weights,
        max_level=max_level,
        milestone_levels=milestone_levels,
    )
