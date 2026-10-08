import uuid
from typing import List, Optional, Union

from app.core.artifact.config import ArtifactConfig, load_artifact_config
from app.core.artifact.models import (
    Artifact,
    ArtifactSlot,
    EnhancementEvent,
    Substat,
    SubstatRoll,
    SubstatState,
)
from app.core.probability.engine import ProbabilityEngine
from app.core.rng.interface import RNGInterface


class ArtifactEngine:
    """Core domain engine for generating and enhancing 5★ Artifacts.

    Strictly satisfies Artifact SPEC v1:
    - 4 conceptual substat slots at all times.
    - 3-line base has 3 ACTIVE + 1 INACTIVE (previewed) substat.
    - +4 for 3-line only activates the 4th substat; no roll occurs.
    - +4 for 4-line and all +8/+12/+16/+20 enhancements perform 1 uniform upgrade.
    - All stochastic selections route strictly through ProbabilityEngine / RNGInterface.
    """

    def __init__(
        self,
        config: Optional[ArtifactConfig] = None,
        prob_engine: Optional[ProbabilityEngine] = None,
        rng: Optional[RNGInterface] = None,
    ) -> None:
        self.config: ArtifactConfig = config if config is not None else load_artifact_config()
        if prob_engine is not None:
            self.prob_engine = prob_engine
        elif rng is not None:
            self.prob_engine = ProbabilityEngine(rng=rng)
        else:
            self.prob_engine = ProbabilityEngine()

    def generate_artifact(
        self,
        set_id: str = "gladiators_finale",
        slot: Optional[Union[ArtifactSlot, str]] = None,
        main_stat: Optional[str] = None,
        initial_lines: Optional[int] = None,
        artifact_id: Optional[str] = None,
    ) -> Artifact:
        """Generate a new 5★ artifact at level 0 obeying SPEC v1 generation rules.

        OUR IMPLEMENTATION DETAIL:
        Generation sequence follows:
          1. Resolve slot
          2. Resolve main stat
          3. Resolve initial lines (3 or 4)
          4. Sequentially select substats 1, 2, 3, 4 without duplicates
          5. Assign initial roll tiers and values
        """
        # 1. Resolve slot
        if slot is None:
            slot_keys = [s.value for s in ArtifactSlot]
            chosen_slot_str = self.prob_engine.weighted_choice(slot_keys, [1] * len(slot_keys))
            resolved_slot = ArtifactSlot(chosen_slot_str)
        elif isinstance(slot, str):
            try:
                resolved_slot = ArtifactSlot(slot.upper())
            except ValueError:
                raise ValueError(f"Invalid artifact slot: {slot}")
        elif isinstance(slot, ArtifactSlot):
            resolved_slot = slot
        else:
            raise ValueError(f"Unsupported slot type: {type(slot)}")

        # 2. Resolve main stat
        slot_main_stats = self.config.main_stats.get(resolved_slot)
        if not slot_main_stats:
            raise ValueError(f"No main stat configuration defined for slot: {resolved_slot.value}")

        if main_stat is not None:
            if main_stat not in slot_main_stats:
                raise ValueError(
                    f"Main stat '{main_stat}' is invalid for slot '{resolved_slot.value}'. "
                    f"Valid stats: {list(slot_main_stats.keys())}"
                )
            resolved_main_stat = main_stat
        else:
            resolved_main_stat = self.prob_engine.weighted_choice_from_dict(slot_main_stats)

        # 3. Resolve initial line count (3 or 4)
        if initial_lines is not None:
            if initial_lines not in (3, 4):
                raise ValueError(f"initial_lines must be 3 or 4 for 5★ artifacts, got {initial_lines}")
            resolved_lines = initial_lines
        else:
            resolved_lines = self.prob_engine.weighted_choice(
                [3, 4],
                [
                    self.config.initial_line_weights.get(3, 80.0),
                    self.config.initial_line_weights.get(4, 20.0),
                ],
            )

        # 4. Filter candidate substats: cannot duplicate main stat
        available_weights = {
            k: v for k, v in self.config.substat_weights.items() if k != resolved_main_stat
        }
        if len(available_weights) < 4:
            raise ValueError(
                f"Insufficient substat candidates ({len(available_weights)}) available after filtering main stat '{resolved_main_stat}'"
            )

        # 5. Sequentially draw 4 distinct substats and their initial tier rolls
        substats: List[Substat] = []
        candidates = dict(available_weights)

        for slot_idx in range(4):
            stat_type = self.prob_engine.weighted_choice_from_dict(candidates)
            del candidates[stat_type]  # prevent duplicate substats

            tier = self.prob_engine.weighted_choice_from_dict(self.config.tier_weights)
            tier_val = self.config.roll_values[stat_type][tier]

            # 3-line base marks 4th substat as INACTIVE; 4-line base marks all ACTIVE
            if slot_idx < 3:
                state = SubstatState.ACTIVE
            else:
                state = SubstatState.ACTIVE if resolved_lines == 4 else SubstatState.INACTIVE

            substat = Substat(
                slot_index=slot_idx,
                stat_type=stat_type,
                state=state,
                initial_value=tier_val,
                initial_tier=tier,
                rolls=[],
            )
            substats.append(substat)

        actual_id = artifact_id if artifact_id is not None else str(uuid.uuid4())

        return Artifact(
            id=actual_id,
            rarity=5,
            set_id=set_id,
            slot=resolved_slot,
            level=0,
            main_stat=resolved_main_stat,
            substats=substats,
            history=[],
        )

    def enhance_artifact(self, artifact: Artifact, target_level: int = 4) -> List[EnhancementEvent]:
        """Enhance an artifact up to target_level, processing all milestone events (+4, +8, +12, +16, +20)."""
        if artifact.level >= self.config.max_level:
            raise ValueError(f"Artifact is already at maximum level ({self.config.max_level})")

        if target_level <= artifact.level:
            raise ValueError(
                f"Target level ({target_level}) must be strictly greater than current level ({artifact.level})"
            )

        if target_level > self.config.max_level:
            raise ValueError(
                f"Target level ({target_level}) cannot exceed max level ({self.config.max_level})"
            )

        milestones = [
            m for m in self.config.milestone_levels if artifact.level < m <= target_level
        ]
        generated_events: List[EnhancementEvent] = []

        for m_level in milestones:
            # Check milestone +4 for 3-line activation
            inactive_stats = artifact.inactive_substats
            if m_level == 4 and len(inactive_stats) > 0:
                # Activate the hidden fourth substat (slot index 3)
                target_substat = artifact.substats[3]
                target_substat.state = SubstatState.ACTIVE

                event = EnhancementEvent(
                    level=4,
                    event_type="ACTIVATION",
                    target_substat_index=3,
                    stat_type=target_substat.stat_type,
                    increment=0.0,
                    tier=None,
                )
                artifact.history.append(event)
                generated_events.append(event)
            else:
                # Upgrade roll: select uniformly among the four ACTIVE substats
                target_idx = self.prob_engine.weighted_choice([0, 1, 2, 3], [1, 1, 1, 1])
                target_substat = artifact.substats[target_idx]

                tier = self.prob_engine.weighted_choice_from_dict(self.config.tier_weights)
                increment = self.config.roll_values[target_substat.stat_type][tier]

                target_substat.rolls.append(
                    SubstatRoll(level=m_level, tier=tier, increment=increment)
                )

                event = EnhancementEvent(
                    level=m_level,
                    event_type="UPGRADE",
                    target_substat_index=target_idx,
                    stat_type=target_substat.stat_type,
                    increment=increment,
                    tier=tier,
                )
                artifact.history.append(event)
                generated_events.append(event)

            artifact.level = m_level

        # If target_level is between milestones or matches milestone, finalize artifact level
        artifact.level = target_level
        return generated_events

    def enhance_step(self, artifact: Artifact) -> EnhancementEvent:
        """Advance the artifact to the next enhancement milestone."""
        next_milestones = [m for m in self.config.milestone_levels if m > artifact.level]
        if not next_milestones:
            raise ValueError(f"Artifact is already at maximum level ({self.config.max_level})")
        events = self.enhance_artifact(artifact, target_level=next_milestones[0])
        return events[0]
