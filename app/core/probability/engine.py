import math
from typing import Mapping, Sequence, TypeVar

from app.core.probability.interface import ProbabilityEngineInterface
from app.core.rng.engine import PythonRNG
from app.core.rng.interface import RNGInterface

T = TypeVar("T")


class ProbabilityEngine(ProbabilityEngineInterface):
    """Generic probability engine responsible for probability-selection logic.

    Decouples probability logic from RNG mechanisms. Uses dependency injection
    for the underlying RNGInterface implementation to guarantee reproducibility
    and isolation from Python's global random state.
    """

    def __init__(self, rng: RNGInterface | None = None) -> None:
        """Initialize the ProbabilityEngine with an isolated RNG instance.

        Args:
            rng: An implementation of RNGInterface. Defaults to a new PythonRNG.
        """
        self.rng: RNGInterface = rng if rng is not None else PythonRNG()

    def weighted_choice(
        self,
        outcomes: Sequence[T],
        weights: Sequence[float | int],
    ) -> T:
        """Select a single outcome based on relative weights.

        Enforces strict validation:
        1. outcomes must not be empty.
        2. weights must not be empty.
        3. outcomes and weights must have identical lengths.
        4. weights must be numeric (excluding bool), finite, and >= 0.
        5. total weight must be strictly > 0.
        6. zero-weight outcomes are never selected.
        """
        if len(outcomes) == 0:
            raise ValueError("Outcomes cannot be empty")
        if len(weights) == 0:
            raise ValueError("Weights cannot be empty")
        if len(outcomes) != len(weights):
            raise ValueError(
                f"Length mismatch: {len(outcomes)} outcomes vs {len(weights)} weights"
            )

        total_weight = 0.0
        for w in weights:
            if isinstance(w, bool) or not isinstance(w, (int, float)) or math.isnan(w) or math.isinf(w):
                raise ValueError(f"Invalid weight: {w}. Must be a finite number.")
            if w < 0:
                raise ValueError(f"Weights must be non-negative, got {w}")
            total_weight += w

        if total_weight <= 0:
            raise ValueError("Total weight must be strictly greater than 0")
        if not math.isfinite(total_weight):
            raise ValueError(
                f"Total weight overflow: cumulative weight is not finite ({total_weight})"
            )

        # Delegate randomized selection to the injected RNG abstraction.
        # Single-outcome selection delegates consistently to ensure identical RNG stream consumption
        # across all weighted_choice invocations for deterministic replay and step debugging.
        return self.rng.weighted_choice(outcomes, weights)

    def weighted_choice_from_dict(
        self,
        distribution: Mapping[T, float | int],
    ) -> T:
        """Select a single outcome from a distribution mapping of {outcome: weight}."""
        if not distribution:
            raise ValueError("Distribution mapping cannot be empty")
        outcomes = list(distribution.keys())
        weights = list(distribution.values())
        return self.weighted_choice(outcomes, weights)
