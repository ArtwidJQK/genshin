"""Artifact loot sources domain engine for Domains of Blessing and Mystic Offering Strongbox.

Strictly satisfies:
- P3 Artifact Loot Sources Specification v1.3.0
- ADR-002: Loot Sources Design, 4★ Fodder Abstraction, and Fidelity Policy
- AGENTS.md: deterministic RNG injection, strict-mode refusal, audit trail, pure domain logic
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Sequence, Union

from app.core.artifact.engine import ArtifactEngine
from app.core.artifact.models import Artifact


class FidelityViolationError(ValueError):
    """Raised when execution cannot proceed within the requested fidelity constraints."""
    pass


class LootFidelityMode(str, Enum):
    """Fidelity modes governing loot acquisition execution."""
    STRICT = "STRICT"
    BEST_EFFORT = "BEST_EFFORT"
    EXPERIMENTAL = "EXPERIMENTAL"

    @classmethod
    def from_value(cls, val: Union["LootFidelityMode", str]) -> "LootFidelityMode":
        """Normalize string or enum into a canonical LootFidelityMode."""
        if isinstance(val, cls):
            return val
        if isinstance(val, str):
            clean = val.strip().upper()
            try:
                return cls(clean)
            except ValueError:
                # Handle lowercase 'strict', 'best_effort', 'experimental'
                for member in cls:
                    if member.value == clean or member.name == clean:
                        return member
        raise ValueError(f"Unknown LootFidelityMode: {val}")


class LootSourceType(str, Enum):
    """Canonical identifier for artifact loot acquisition channels."""
    DOMAIN_OF_BLESSING = "DOMAIN_OF_BLESSING"
    ARTIFACT_STRONGBOX = "ARTIFACT_STRONGBOX"


@dataclass(frozen=True)
class LootAuditEvent:
    """Audit record capturing an atomic stochastic step in a loot transaction."""
    cycle_index: int                       # 0 (or 1 for condensed resin second cycle, or output index for strongbox)
    source_type: LootSourceType            # DOMAIN_OF_BLESSING or ARTIFACT_STRONGBOX
    event_type: str                        # "SET_SELECTION", "SECONDARY_5STAR_ROLL", "SECONDARY_FODDER_ROLL", "LINE_COUNT_ROLL"
    roll_value: Optional[float]            # Drawn uniform random float in [0, 1), if applicable
    threshold: Optional[float]             # Probability threshold tested against, if applicable
    outcome: Any                           # Chosen outcome (e.g. set_id, initial_lines, count)
    evidence_level: str                    # Evidence tier of the evaluated rule ("VERIFIED", "INFERRED", "ASSUMED")


@dataclass(frozen=True)
class DomainDropResult:
    """Represents the complete reward output of a Domain of Blessing run."""
    domain_id: str
    artifacts: List[Artifact]              # Concrete 5★ Artifact instances generated
    count_4star_fodder: int                # Abstracted count of 4★ fodder artifacts (Decision 1A)
    resin_spent: int                       # 20 (normal) or 40 (condensed)
    runs_executed: int                     # 1 (normal) or 2 (condensed)
    fidelity_mode: LootFidelityMode
    weakest_evidence_level: str            # "INFERRED" in best_effort, "EXPERIMENTAL" in experimental
    source_type: LootSourceType = LootSourceType.DOMAIN_OF_BLESSING
    audit_events: List[LootAuditEvent] = field(default_factory=list)


@dataclass(frozen=True)
class StrongboxResult:
    """Represents the complete output of an Artifact Strongbox craft."""
    target_set: str
    artifacts: List[Artifact]              # Concrete 5★ Artifact instances generated
    sacrificed_count: int                  # Total 5★ artifacts consumed (multiple of 3)
    fidelity_mode: LootFidelityMode
    weakest_evidence_level: str            # "INFERRED" (due to 66/34 line distribution)
    source_type: LootSourceType = LootSourceType.ARTIFACT_STRONGBOX
    audit_events: List[LootAuditEvent] = field(default_factory=list)


def run_domain_of_blessing(
    domain_id: str = "domain_of_blessing",
    sets: Optional[Sequence[str]] = None,
    use_condensed: bool = False,
    fidelity_mode: Union[LootFidelityMode, str] = LootFidelityMode.BEST_EFFORT,
    engine: Optional[ArtifactEngine] = None,
) -> DomainDropResult:
    """Execute a Level 90 Domain of Blessing run consuming 20 Original Resin or 1 Condensed Resin.

    Parameters:
        domain_id: Logical identifier for the domain instance.
        sets: Exactly 2 distinct 5★ artifact set identifiers dropped by this domain.
        use_condensed: True if consuming 1 Condensed Resin (40 resin equivalent, 2 sequential runs).
        fidelity_mode: STRICT, BEST_EFFORT, or EXPERIMENTAL.
        engine: Injected ArtifactEngine providing deterministic PRNG and generation rules.

    Raises:
        FidelityViolationError: If fidelity_mode is STRICT, as required drop rates/affixes are INFERRED.
        ValueError: If sets is not exactly 2 distinct set identifiers.
    """
    mode = LootFidelityMode.from_value(fidelity_mode)
    if mode == LootFidelityMode.STRICT:
        raise FidelityViolationError(
            f"Cannot execute {LootSourceType.DOMAIN_OF_BLESSING.value} in STRICT fidelity mode: "
            f"required parameters (set_distribution, initial_lines, substat_weights) have "
            f"evidence level INFERRED. STRICT mode permits only VERIFIED rules. "
            f"Use BEST_EFFORT mode for empirical simulation."
        )

    if sets is None:
        resolved_sets = ("gladiators_finale", "wanderers_troupe")
    else:
        resolved_sets = tuple(sets)

    if len(resolved_sets) != 2 or len(set(resolved_sets)) != 2:
        raise ValueError("Domain requires exactly 2 distinct 5★ sets.")

    resolved_engine = engine if engine is not None else ArtifactEngine()

    runs = 2 if use_condensed else 1
    resin_spent = 40 if use_condensed else 20

    # Retrieve configuration parameters (with default empirical fallbacks)
    if resolved_engine.config.loot_sources is not None:
        dom_cfg = resolved_engine.config.loot_sources.domain_of_blessing
        sec_prob = dom_cfg.secondary_5star_probability
        fodder_base = dom_cfg.fodder_4star_baseline
        fodder_sec_prob = dom_cfg.fodder_4star_secondary_probability
        line3_w = dom_cfg.initial_line_count_weights.get(3, 80.0)
        line4_w = dom_cfg.initial_line_count_weights.get(4, 20.0)
        line_thresh = line3_w / (line3_w + line4_w)
    else:
        sec_prob = 0.0654
        fodder_base = 2
        fodder_sec_prob = 0.48
        line_thresh = 0.80

    all_artifacts: List[Artifact] = []
    all_audit_events: List[LootAuditEvent] = []
    total_fodder: int = 0

    rng = resolved_engine.prob_engine.rng

    for cycle_index in range(runs):
        # 1. 5★ Quantity Resolution (1 guaranteed + Bernoulli trial for 2nd)
        r5 = rng.random()
        count_5star = 2 if r5 < sec_prob else 1
        all_audit_events.append(
            LootAuditEvent(
                cycle_index=cycle_index,
                source_type=LootSourceType.DOMAIN_OF_BLESSING,
                event_type="SECONDARY_5STAR_ROLL",
                roll_value=r5,
                threshold=sec_prob,
                outcome=count_5star,
                evidence_level="INFERRED",
            )
        )

        # 2. 4★ Fodder Quantity Resolution (fodder_base + Bernoulli trial for 3rd)
        r4 = rng.random()
        fodder_count = fodder_base + (1 if r4 < fodder_sec_prob else 0)
        total_fodder += fodder_count
        all_audit_events.append(
            LootAuditEvent(
                cycle_index=cycle_index,
                source_type=LootSourceType.DOMAIN_OF_BLESSING,
                event_type="SECONDARY_FODDER_ROLL",
                roll_value=r4,
                threshold=fodder_sec_prob,
                outcome=fodder_count,
                evidence_level="INFERRED",
            )
        )

        # 3. 5★ Artifact Generation
        for _ in range(count_5star):
            # Set selection (50/50)
            r_set = rng.random()
            chosen_set = resolved_sets[0] if r_set < 0.50 else resolved_sets[1]
            all_audit_events.append(
                LootAuditEvent(
                    cycle_index=cycle_index,
                    source_type=LootSourceType.DOMAIN_OF_BLESSING,
                    event_type="SET_SELECTION",
                    roll_value=r_set,
                    threshold=0.50,
                    outcome=chosen_set,
                    evidence_level="INFERRED",
                )
            )

            # Initial line count (80% 3-line vs 20% 4-line)
            r_lines = rng.random()
            chosen_lines = 3 if r_lines < line_thresh else 4
            all_audit_events.append(
                LootAuditEvent(
                    cycle_index=cycle_index,
                    source_type=LootSourceType.DOMAIN_OF_BLESSING,
                    event_type="LINE_COUNT_ROLL",
                    roll_value=r_lines,
                    threshold=line_thresh,
                    outcome=chosen_lines,
                    evidence_level="INFERRED",
                )
            )

            art = resolved_engine.generate_artifact(set_id=chosen_set, initial_lines=chosen_lines)
            all_artifacts.append(art)

    weakest_evidence = "EXPERIMENTAL" if mode == LootFidelityMode.EXPERIMENTAL else "INFERRED"

    return DomainDropResult(
        domain_id=domain_id,
        artifacts=all_artifacts,
        count_4star_fodder=total_fodder,
        resin_spent=resin_spent,
        runs_executed=runs,
        fidelity_mode=mode,
        weakest_evidence_level=weakest_evidence,
        source_type=LootSourceType.DOMAIN_OF_BLESSING,
        audit_events=all_audit_events,
    )


def craft_strongbox(
    target_set: str,
    sacrifice_artifacts: List[Artifact],
    fidelity_mode: Union[LootFidelityMode, str] = LootFidelityMode.BEST_EFFORT,
    engine: Optional[ArtifactEngine] = None,
) -> StrongboxResult:
    """Execute Mystic Offering Artifact Strongbox craft converting 5★ artifacts at 3:1 ratio.

    Parameters:
        target_set: Set identifier for the crafted artifacts.
        sacrifice_artifacts: Non-empty list of 5★ Artifact instances, length must be a multiple of 3.
        fidelity_mode: STRICT, BEST_EFFORT, or EXPERIMENTAL.
        engine: Injected ArtifactEngine providing deterministic PRNG and generation rules.

    Raises:
        TypeError: If sacrifice_artifacts is not a list of Artifact instances.
        ValueError: If sacrifice_artifacts count is < 3, not a multiple of 3, contains non-5★, or target_set is empty.
        FidelityViolationError: If fidelity_mode is STRICT, as initial line distribution is INFERRED.
    """
    if not isinstance(sacrifice_artifacts, list):
        raise TypeError("sacrifice_artifacts must be a list of Artifact instances.")

    if len(sacrifice_artifacts) < 3:
        raise ValueError(f"Strongbox requires at least 3 artifacts to craft, got {len(sacrifice_artifacts)}.")

    if len(sacrifice_artifacts) % 3 != 0:
        raise ValueError(f"Sacrifice count ({len(sacrifice_artifacts)}) must be an exact multiple of 3.")

    for art in sacrifice_artifacts:
        if not isinstance(art, Artifact) or art.rarity != 5:
            art_id = getattr(art, "id", "unknown")
            rarity_val = getattr(art, "rarity", "unknown")
            raise ValueError(f"Strongbox only accepts 5★ artifacts; artifact '{art_id}' has rarity {rarity_val}.")

    if not target_set or not target_set.strip():
        raise ValueError("target_set must not be empty.")

    clean_target = target_set.strip()

    mode = LootFidelityMode.from_value(fidelity_mode)
    if mode == LootFidelityMode.STRICT:
        raise FidelityViolationError(
            f"Cannot execute {LootSourceType.ARTIFACT_STRONGBOX.value} in STRICT fidelity mode: "
            f"required parameters (initial_lines, substat_weights) have evidence level INFERRED. "
            f"STRICT mode permits only VERIFIED rules. Use BEST_EFFORT mode for empirical simulation."
        )

    resolved_engine = engine if engine is not None else ArtifactEngine()

    if resolved_engine.config.loot_sources is not None:
        sb_cfg = resolved_engine.config.loot_sources.artifact_strongbox
        line3_w = sb_cfg.initial_line_count_weights.get(3, 66.0)
        line4_w = sb_cfg.initial_line_count_weights.get(4, 34.0)
        line_thresh = line3_w / (line3_w + line4_w)
    else:
        line_thresh = 0.66

    output_count = len(sacrifice_artifacts) // 3
    crafted_artifacts: List[Artifact] = []
    audit_events: List[LootAuditEvent] = []

    rng = resolved_engine.prob_engine.rng

    for j in range(output_count):
        r_lines = rng.random()
        chosen_lines = 3 if r_lines < line_thresh else 4
        audit_events.append(
            LootAuditEvent(
                cycle_index=j,
                source_type=LootSourceType.ARTIFACT_STRONGBOX,
                event_type="LINE_COUNT_ROLL",
                roll_value=r_lines,
                threshold=line_thresh,
                outcome=chosen_lines,
                evidence_level="INFERRED",
            )
        )

        art = resolved_engine.generate_artifact(set_id=clean_target, initial_lines=chosen_lines)
        crafted_artifacts.append(art)

    weakest_evidence = "EXPERIMENTAL" if mode == LootFidelityMode.EXPERIMENTAL else "INFERRED"

    return StrongboxResult(
        target_set=clean_target,
        artifacts=crafted_artifacts,
        sacrificed_count=len(sacrifice_artifacts),
        fidelity_mode=mode,
        weakest_evidence_level=weakest_evidence,
        source_type=LootSourceType.ARTIFACT_STRONGBOX,
        audit_events=audit_events,
    )
