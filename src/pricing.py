"""Price estimation for the BookHotel intent.

Consumes a validated pricing configuration (from ``config.load_pricing``)
and returns a fully-quantized ``Decimal``-based ``Estimate``.

This module does not format messages, log, or call AWS. Those are the
handler's job.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

_CENTS = Decimal("0.01")


def _quantize(value):
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Estimate:
    """Immutable price breakdown for a booking estimate."""

    currency: str
    room_key: str
    room_display_name: str
    nights: int
    price_per_night: Decimal
    subtotal: Decimal
    tax: Decimal
    total: Decimal


def calculate_estimate(pricing, room_key, nights):
    """Return an ``Estimate`` for ``nights`` of ``room_key``.

    ``pricing`` must be the dict produced by ``config.load_pricing()``.
    ``room_key`` must be a lowercase room key present in ``pricing["rooms"]``.
    ``nights`` must be a positive integer within ``pricing["maxNights"]``.

    Raises ``ValueError`` on any contract violation. The handler converts
    that into a generic user-facing message, so the specific string here
    is for developers and logs, not end users.
    """
    if not isinstance(pricing, dict):
        raise ValueError("pricing must be a dict")
    rooms = pricing.get("rooms")
    if not isinstance(rooms, dict):
        raise ValueError("pricing['rooms'] must be a dict")

    if not isinstance(room_key, str):
        raise ValueError("room_key must be a string")
    key = room_key.strip().lower()
    if key not in rooms:
        raise ValueError(f"Unknown room_key: {room_key!r}")

    if isinstance(nights, bool) or not isinstance(nights, int):
        raise ValueError("nights must be an int")
    if nights < 1:
        raise ValueError("nights must be at least 1")

    max_nights = pricing.get("maxNights", 30)
    if isinstance(max_nights, int) and not isinstance(max_nights, bool):
        if nights > max_nights:
            raise ValueError(f"nights must not exceed maxNights={max_nights}")

    room = rooms[key]
    price_per_night = _quantize(Decimal(str(room["pricePerNight"])))
    subtotal = _quantize(price_per_night * nights)

    tax_rate = Decimal(str(pricing.get("taxRatePercent", 0)))
    if tax_rate < 0:
        raise ValueError("taxRatePercent cannot be negative")
    tax = _quantize(subtotal * tax_rate / Decimal("100"))

    total = _quantize(subtotal + tax)

    return Estimate(
        currency=pricing.get("currency", "INR"),
        room_key=key,
        room_display_name=room["displayName"],
        nights=nights,
        price_per_night=price_per_night,
        subtotal=subtotal,
        tax=tax,
        total=total,
    )
