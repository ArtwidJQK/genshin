"""Presentation-only formatting for artifact stat values.

Internal values are never rounded here or mutated by this module.
The display rules follow docs/SPEC_ARTIFACT.md section 3.4.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union

from app.core.artifact.models import ALL_ARTIFACT_PROPERTIES

NumericValue = Union[int, float, Decimal]
_INTEGER_DISPLAY_STATS = frozenset({"FLAT_HP", "FLAT_ATK", "FLAT_DEF", "ELEMENTAL_MASTERY"})


def format_stat_value(stat_type: str, value: NumericValue) -> str:
    """Format a stat value at the presentation boundary.

    Flat HP/ATK/DEF and Elemental Mastery are displayed as whole numbers.
    Other recognized artifact properties are displayed to one decimal place
    followed by '%'. Decimal(str(value)) keeps the chosen display rounding
    step explicit. ROUND_HALF_UP is a presentation-only convention recorded in
    docs/adr/ADR-001-display-rounding.md.

    Raises:
        ValueError: for unknown stat identifiers or non-finite numeric values.
        TypeError: for booleans and values that are not int, float, or Decimal.
    """
    if stat_type not in ALL_ARTIFACT_PROPERTIES:
        raise ValueError(f"Unsupported artifact stat type: {stat_type!r}")
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise TypeError("Stat value must be an int, float, or Decimal (bool is not accepted).")

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Stat value is not a valid finite number: {value!r}") from exc
    if not number.is_finite():
        raise ValueError(f"Stat value must be finite, got {value!r}")

    if stat_type in _INTEGER_DISPLAY_STATS:
        try:
            rounded = number.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise ValueError(f"Stat value is outside the formatter's supported range: {value!r}") from exc
        return format(rounded, ".0f")

    try:
        rounded = number.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"Stat value is outside the formatter's supported range: {value!r}") from exc
    return f"{rounded:.1f}%"
