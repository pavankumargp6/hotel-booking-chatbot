"""Load and validate hotel booking pricing configuration.

Pricing is read from the ``PRICING_CONFIG`` environment variable as JSON.
If the variable is unset, safe defaults matching the original README are
used. Invalid configuration raises ``ValueError`` at load time so the
Lambda handler fails fast instead of serving wrong prices.
"""

import copy
import json
import os
from decimal import Decimal

DEFAULT_PRICING = {
    "currency": "INR",
    "maxNights": 30,
    "taxRatePercent": 0,
    "rooms": {
        "classic": {"displayName": "Classic", "pricePerNight": 2000},
        "deluxe": {"displayName": "Deluxe", "pricePerNight": 3000},
        "duplex": {"displayName": "Duplex", "pricePerNight": 5000},
        "suite": {"displayName": "Suite", "pricePerNight": 7000},
    },
}

REQUIRED_ROOMS = {"classic", "deluxe", "duplex", "suite"}


def load_pricing():
    """Return a validated pricing configuration dict.

    Reads ``PRICING_CONFIG`` from the environment. Falls back to
    ``DEFAULT_PRICING`` when the variable is unset or empty.
    """
    raw = os.environ.get("PRICING_CONFIG", "").strip()
    if not raw:
        return copy.deepcopy(DEFAULT_PRICING)

    try:
        pricing = json.loads(raw, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise ValueError("PRICING_CONFIG must be valid JSON") from exc

    if not isinstance(pricing, dict):
        raise ValueError("PRICING_CONFIG must be a JSON object")

    rooms = pricing.get("rooms")
    if not isinstance(rooms, dict):
        raise ValueError("PRICING_CONFIG must contain a 'rooms' object")

    missing = REQUIRED_ROOMS - set(rooms)
    if missing:
        raise ValueError(
            f"PRICING_CONFIG is missing rooms: {sorted(missing)}"
        )

    for key, room in rooms.items():
        if not isinstance(room, dict):
            raise ValueError(f"Room '{key}' must be a JSON object")
        if "displayName" not in room or "pricePerNight" not in room:
            raise ValueError(
                f"Room '{key}' must define both displayName and pricePerNight"
            )
        if not isinstance(room["displayName"], str) or not room["displayName"]:
            raise ValueError(
                f"Room '{key}' displayName must be a non-empty string"
            )
        price = room["pricePerNight"]
        if isinstance(price, bool) or not isinstance(price, (int, Decimal)):
            raise ValueError(
                f"Room '{key}' pricePerNight must be a number"
            )
        if price <= 0:
            raise ValueError(
                f"Room '{key}' pricePerNight must be greater than zero"
            )

    pricing.setdefault("currency", "INR")
    pricing.setdefault("maxNights", 30)
    pricing.setdefault("taxRatePercent", 0)

    max_nights = pricing["maxNights"]
    if isinstance(max_nights, bool) or not isinstance(max_nights, int):
        raise ValueError("PRICING_CONFIG maxNights must be an integer")
    if max_nights < 1:
        raise ValueError("PRICING_CONFIG maxNights must be at least 1")

    tax = pricing["taxRatePercent"]
    if isinstance(tax, bool) or not isinstance(tax, (int, Decimal)):
        raise ValueError("PRICING_CONFIG taxRatePercent must be a number")
    if tax < 0:
        raise ValueError("PRICING_CONFIG taxRatePercent cannot be negative")

    return pricing
