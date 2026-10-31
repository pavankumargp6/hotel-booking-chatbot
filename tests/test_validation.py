from datetime import date, timedelta

import pytest

import validation
from validation import (
    SLOT_CHECK_IN_DATE,
    SLOT_LOCATION,
    SLOT_NIGHTS,
    SLOT_ROOM_TYPE,
    validate_check_in_date,
    validate_location,
    validate_nights,
    validate_room_type,
)

ROOMS = {
    "classic": {"displayName": "Classic", "pricePerNight": 2000},
    "deluxe": {"displayName": "Deluxe", "pricePerNight": 3000},
    "duplex": {"displayName": "Duplex", "pricePerNight": 5000},
    "suite": {"displayName": "Suite", "pricePerNight": 7000},
}


# ---- Location -------------------------------------------------------------


@pytest.mark.parametrize("value", ["", "   ", None, 123])
def test_location_rejects_empty_or_non_string(value):
    error = validate_location(value)
    assert error is not None
    assert error.slot_name == SLOT_LOCATION


@pytest.mark.parametrize("value", ["Bangalore", "  Bangalore  ", "Paris"])
def test_location_accepts_non_empty_string(value):
    assert validate_location(value) is None


# ---- CheckInDate ----------------------------------------------------------


def test_check_in_date_accepts_future_date():
    future = (validation._today_utc() + timedelta(days=1)).isoformat()
    assert validate_check_in_date(future) is None


def test_check_in_date_accepts_today():
    # Same-day check-in is allowed; the comparison is strictly "<".
    # Use the same "today" the production code uses (UTC), otherwise this
    # test is flaky for users in non-UTC timezones (e.g. IST evening).
    today = validation._today_utc().isoformat()
    assert validate_check_in_date(today) is None


def test_check_in_date_rejects_past_date():
    past = (validation._today_utc() - timedelta(days=1)).isoformat()
    error = validate_check_in_date(past)
    assert error is not None
    assert error.slot_name == SLOT_CHECK_IN_DATE
    assert "past" in error.message.lower()


def test_check_in_date_rejects_unparseable_value():
    for bad in ["tomorrow", "2026-13-01", "01/02/2026", "2026-02-30"]:
        error = validate_check_in_date(bad)
        assert error is not None, bad
        assert error.slot_name == SLOT_CHECK_IN_DATE


def test_check_in_date_rejects_empty():
    for empty in ["", "   ", None]:
        error = validate_check_in_date(empty)
        assert error is not None
        assert error.slot_name == SLOT_CHECK_IN_DATE


def test_check_in_date_uses_injected_today(monkeypatch):
    # Pin "today" so the test does not depend on the wall clock.
    monkeypatch.setattr(validation, "_today_utc", lambda: date(2026, 6, 1))
    assert validate_check_in_date("2026-06-01") is None
    assert validate_check_in_date("2026-05-31") is not None
    assert validate_check_in_date("2026-06-02") is None


# ---- Nights ---------------------------------------------------------------


@pytest.mark.parametrize("value", ["1", "2", "10", "30"])
def test_nights_accepts_within_range(value):
    assert validate_nights(value, max_nights=30) is None


@pytest.mark.parametrize("value", ["0", "-1", "31", "1000"])
def test_nights_rejects_out_of_range(value):
    error = validate_nights(value, max_nights=30)
    assert error is not None
    assert error.slot_name == SLOT_NIGHTS


@pytest.mark.parametrize("value", ["3.0", "3.5", "3e0", "abc", "", None])
def test_nights_rejects_non_integer_or_empty(value):
    error = validate_nights(value, max_nights=30)
    assert error is not None
    assert error.slot_name == SLOT_NIGHTS


def test_nights_respects_configured_max():
    assert validate_nights("7", max_nights=7) is None
    error = validate_nights("8", max_nights=7)
    assert error is not None
    assert "1 and 7" in error.message


# ---- RoomType -------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["classic", "Deluxe", "DUPLEX", " suite ", "SUITE"],
)
def test_room_type_is_case_and_whitespace_insensitive(value):
    assert validate_room_type(value, ROOMS) is None


@pytest.mark.parametrize("value", ["penthouse", "single", "suite plus"])
def test_room_type_rejects_unknown(value):
    error = validate_room_type(value, ROOMS)
    assert error is not None
    assert error.slot_name == SLOT_ROOM_TYPE
    assert "Classic" in error.message


@pytest.mark.parametrize("value", ["", "   ", None])
def test_room_type_rejects_empty(value):
    error = validate_room_type(value, ROOMS)
    assert error is not None
    assert error.slot_name == SLOT_ROOM_TYPE


def test_room_type_message_lists_all_rooms():
    error = validate_room_type("penthouse", ROOMS)
    for display in ["Classic", "Deluxe", "Duplex", "Suite"]:
        assert display in error.message
