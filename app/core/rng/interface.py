from abc import ABC, abstractmethod
from typing import Any, MutableSequence, Sequence, TypeVar

T = TypeVar("T")


class RNGInterface(ABC):
    """Abstract interface defining required random number generator capabilities.

    All randomized operations in the simulation must funnel through implementations
    of this interface to ensure isolation, reproducibility, and deterministic replay.
    """

    @abstractmethod
    def seed(self, a: int | str | bytes | bytearray | None = None) -> None:
        """Seed the underlying RNG with a specific value."""
        pass

    @abstractmethod
    def random(self) -> float:
        """Return the next random floating point number in the range [0.0, 1.0)."""
        pass

    @abstractmethod
    def random_int(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""
        pass

    @abstractmethod
    def random_float(self, a: float, b: float) -> float:
        """Return a random floating point number N such that a <= N <= b."""
        pass

    @abstractmethod
    def choice(self, seq: Sequence[T]) -> T:
        """Return a random element from a non-empty sequence."""
        pass

    @abstractmethod
    def weighted_choice(
        self,
        outcomes: Sequence[T],
        weights: Sequence[float | int],
    ) -> T:
        """Select a single outcome based on relative weights.

        Validates inputs:
        - outcomes and weights cannot be empty
        - outcomes and weights must have identical lengths
        - weights must be non-negative real numbers
        - sum of weights must be strictly greater than 0
        """
        pass

    @abstractmethod
    def shuffle(self, seq: MutableSequence[T]) -> None:
        """Shuffle the sequence in-place."""
        pass

    @abstractmethod
    def get_state(self) -> Any:
        """Capture and return the internal state of the RNG."""
        pass

    @abstractmethod
    def set_state(self, state: Any) -> None:
        """Restore the internal state of the RNG."""
        pass
