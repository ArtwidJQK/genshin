import math
import random
from typing import Any, MutableSequence, Sequence, TypeVar

from app.core.rng.interface import RNGInterface

T = TypeVar("T")


class PythonRNG(RNGInterface):
    """Deterministic RNG engine wrapping Python's standard `random.Random`.

    Ensures that RNG state is completely isolated from global random state.
    """

    def __init__(self, seed: int | str | bytes | bytearray | None = None) -> None:
        self._rng: random.Random = random.Random(seed)

    def seed(self, a: int | str | bytes | bytearray | None = None) -> None:
        """Seed the isolated random instance."""
        self._rng.seed(a)

    def random(self) -> float:
        """Return the next random float in [0.0, 1.0)."""
        return self._rng.random()

    def random_int(self, a: int, b: int) -> int:
        """Return a random integer in range [a, b] inclusive."""
        if a > b:
            raise ValueError(f"Lower bound ({a}) cannot exceed upper bound ({b})")
        return self._rng.randint(a, b)

    def random_float(self, a: float, b: float) -> float:
        """Return a random floating point number between a and b."""
        if a > b:
            raise ValueError(f"Lower bound ({a}) cannot exceed upper bound ({b})")
        return self._rng.uniform(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        """Choose a random element from a non-empty sequence."""
        if not seq:
            raise ValueError("Cannot choose from an empty sequence")
        return self._rng.choice(seq)

    def weighted_choice(
        self,
        outcomes: Sequence[T],
        weights: Sequence[float | int],
    ) -> T:
        """Select one element from outcomes given corresponding weights.

        Normalization is handled inherently by dividing or scaling via total weight.
        """
        if len(outcomes) == 0:
            raise ValueError("Outcomes cannot be empty")
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

        # Select deterministically using encapsulated RNG instance
        return self._rng.choices(outcomes, weights=weights, k=1)[0]

    def shuffle(self, seq: MutableSequence[T]) -> None:
        """Shuffle a mutable sequence in-place."""
        self._rng.shuffle(seq)

    def get_state(self) -> Any:
        """Capture and return the current generator internal state."""
        return self._rng.getstate()

    def set_state(self, state: Any) -> None:
        """Restore the generator internal state."""
        self._rng.setstate(state)
