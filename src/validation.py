"""Slot validation for the BookHotel intent.

Each validator accepts the interpreted slot value as a string and returns
``None`` when valid, or a ``SlotError`` describing which slot failed and
what to ask the user next.

These functions are pure: they do not read environment variables, call
AWS, or log. That keeps them trivially unit-testable.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime

SLOT_LOCATION = "Location"
SLOT_CHECK_IN_DATE = "CheckInDate"
SLOT_NIGHTS = "Nights"
SLOT_ROOM_TYPE = "RoomType"

REQUIRED_SLOTS = (
    SLOT_LOCATION,
    SLOT_CHECK_IN_DATE,
    SLOT_NIGHTS,
    SLOT_ROOM_TYPE,
)


@dataclass(frozen=True)
class SlotError:
    """Validation failure for a single slot.

    ``slot_name`` must match the slot name configured in the Lex bot.
    ``message`` is shown to the user verbatim.
    """

    slot_name: str
    message: str


def _today_utc():
    """Return today's date in UTC.

    Wrapped in a function so tests can freeze time via monkeypatch if
    needed, and so the value is always computed at call time rather than
    at import time.
    """
    return datetime.now(UTC).date()


def validate_location(value):
    if not isinstance(value, str) or not value.strip():
        return SlotError(
            SLOT_LOCATION,
            "Which city would you like to stay in?",
        )
    return None


def validate_check_in_date(value):
    if not isinstance(value, str) or not value.strip():
        return SlotError(
            SLOT_CHECK_IN_DATE,
            "What is your check-in date? Please use YYYY-MM-DD.",
        )

    raw = value.strip()
    try:
        # date.fromisoformat accepts "YYYY-MM-DD" but not "YYYY-MM-DDTHH:MM".
        check_in = date.fromisoformat(raw)
    except ValueError:
        return SlotError(
            SLOT_CHECK_IN_DATE,
            "Please provide the check-in date in YYYY-MM-DD format.",
        )

    if check_in < _today_utc():
        return SlotError(
            SLOT_CHECK_IN_DATE,
            "Check-in date cannot be in the past. Please choose a future date.",
        )

    return None


def validate_nights(value, max_nights):
    if not isinstance(value, str) or not value.strip():
        return SlotError(SLOT_NIGHTS, "How many nights will you stay?")

    raw = value.strip()

    # Reject floats and negatives explicitly so the message is friendly.
    if "." in raw or "e" in raw.lower():
        return SlotError(
            SLOT_NIGHTS,
            "Number of nights must be a whole number.",
        )

    try:
        nights = int(raw)
    except ValueError:
        return SlotError(
            SLOT_NIGHTS,
            "Number of nights must be a whole number.",
        )

    if nights < 1 or nights > max_nights:
        return SlotError(
            SLOT_NIGHTS,
            f"Number of nights must be between 1 and {max_nights}.",
        )

    return None


def validate_room_type(value, rooms):
    if not isinstance(value, str) or not value.strip():
        return SlotError(
            SLOT_ROOM_TYPE,
            "Which room type would you like? "
            f"Choose from: {_allowed_rooms(rooms)}.",
        )

    key = value.strip().lower()
    if key not in rooms:
        return SlotError(
            SLOT_ROOM_TYPE,
            f"Please choose a valid room type: {_allowed_rooms(rooms)}.",
        )

    return None


def _allowed_rooms(rooms):
    return ", ".join(room["displayName"] for room in rooms.values())
