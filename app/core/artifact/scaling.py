"""Domain logic for artifact main stat scaling lookup.

Exposes verified main stat values across levels 0–20 from client datamine
configuration loaded into ArtifactConfig.
Values are returned with full internal floating-point precision without presentation rounding.
Presentation rounding is strictly handled at the display boundary (formatting.py).
"""
import math
from typing import Optional, Union

from app.core.artifact.config import ArtifactConfig, load_artifact_config
from app.core.artifact.models import Artifact, VALID_MAIN_STATS


def get_main_stat_value(
    target: Union[Artifact, str],
    level: Optional[int] = None,
    *,
    config: Optional[ArtifactConfig] = None,
) -> float:
    """Retrieve the exact numerical main stat value for a given stat type and level, or Artifact.

    Args:
        target: Either an Artifact instance or a canonical 5★ main stat string (from VALID_MAIN_STATS).
        level: Artifact level in [0, 20]. Must be None if target is an Artifact; required if target is str.
        config: Optional ArtifactConfig instance. If omitted, loaded via load_artifact_config().

    Returns:
        float: The exact unrounded internal floating-point value from datamine scaling.

    Raises:
        TypeError: If target is not Artifact or str (or is bool), or level has invalid type/usage,
                   or config is not an ArtifactConfig instance.
        ValueError: If config lacks scaling data, or stat is not in VALID_MAIN_STATS,
                    or level is outside [0, 20], or scaling data is corrupted/missing.
    """
    # 1. Resolve and validate config
    if config is None:
        cfg = load_artifact_config()
    elif isinstance(config, ArtifactConfig):
        cfg = config
    else:
        raise TypeError(f"config must be an instance of ArtifactConfig, got {type(config).__name__}")

    if cfg.main_stat_scaling is None or len(cfg.main_stat_scaling) == 0:
        raise ValueError("ArtifactConfig does not have main_stat_scaling data loaded.")

    # 2. Resolve target and level
    if isinstance(target, bool):
        raise TypeError("Target cannot be a boolean.")
    elif isinstance(target, Artifact):
        if level is not None:
            raise TypeError(
                "Argument 'level' must not be provided when target is an Artifact; "
                f"artifact.level ({target.level}) is used automatically."
            )
        target.validate_state()
        stat_type = target.main_stat
        resolved_level = target.level
    elif isinstance(target, str):
        if level is None:
            raise TypeError("Argument 'level' is required when target is a stat_type string.")
        stat_type = target
        resolved_level = level
    else:
        raise TypeError(
            f"Target must be an Artifact instance or a stat_type string, got {type(target).__name__}"
        )

    # 3. Validate level type and bounds
    if isinstance(resolved_level, bool) or not isinstance(resolved_level, int):
        raise TypeError(
            f"Artifact level must be an integer, got {type(resolved_level).__name__}: {resolved_level!r}"
        )
    if not (0 <= resolved_level <= cfg.max_level):
        raise ValueError(
            f"Artifact level must be between 0 and {cfg.max_level} inclusive, got {resolved_level}"
        )

    # 4. Validate stat type
    if stat_type not in VALID_MAIN_STATS:
        raise ValueError(
            f"Stat '{stat_type}' is not a valid 5★ main stat."
        )

    # 5. Validate presence in config scaling data
    if stat_type not in cfg.main_stat_scaling:
        raise ValueError(
            f"Main stat '{stat_type}' is not present in scaling configuration."
        )

    stat_levels = cfg.main_stat_scaling[stat_type]
    if resolved_level not in stat_levels:
        raise ValueError(
            f"Level {resolved_level} is not present in scaling data for '{stat_type}'."
        )

    # 6. Retrieve and validate numerical value
    value = stat_levels[resolved_level]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(
            f"Invalid non-finite or non-numeric scaling value for '{stat_type}' at level {resolved_level}: {value!r}"
        )
    if value <= 0:
        raise ValueError(
            f"Scaling value for '{stat_type}' at level {resolved_level} must be strictly positive, got {value}"
        )

    return float(value)
