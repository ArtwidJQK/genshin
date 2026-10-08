from abc import ABC, abstractmethod
from typing import Mapping, Sequence, TypeVar

T = TypeVar("T")


class ProbabilityEngineInterface(ABC):
    """Abstract interface defining probability-selection operations."""

    @abstractmethod
    def weighted_choice(
        self,
        outcomes: Sequence[T],
        weights: Sequence[float | int],
    ) -> T:
        """Select a single outcome based on relative weights.

        Validates inputs:
        - outcomes and weights must have identical lengths.
        - outcomes must not be empty.
        - weights must not be empty.
        - weights must be numeric, finite, and non-negative.
        - total weight must be strictly greater than 0.
        - zero-weight outcomes must never be selected.
        """
        pass

    @abstractmethod
    def weighted_choice_from_dict(
        self,
        distribution: Mapping[T, float | int],
    ) -> T:
        """Select a single outcome from a distribution mapping of {outcome: weight}."""
        pass
