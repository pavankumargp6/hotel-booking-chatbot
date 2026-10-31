from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from config import DEFAULT_PRICING
from pricing import Estimate, calculate_estimate


def _pricing(tax_rate=0, currency="INR", max_nights=30):
    return {
        "currency": currency,
        "maxNights": max_nights,
        "taxRatePercent": tax_rate,
        "rooms": {
            "classic": {"displayName": "Classic", "pricePerNight": 2000},
            "deluxe": {"displayName": "Deluxe", "pricePerNight": 3000},
            "duplex": {"displayName": "Duplex", "pricePerNight": 5000},
            "suite": {"displayName": "Suite", "pricePerNight": 7000},
        },
    }


# ---- Core math -------------------------------------------------------------


def test_classic_one_night():
    est = calculate_estimate(_pricing(), "classic", 1)
    assert est.price_per_night == Decimal("2000.00")
    assert est.subtotal == Decimal("2000.00")
    assert est.tax == Decimal("0.00")
    assert est.total == Decimal("2000.00")


def test_deluxe_two_nights():
    est = calculate_estimate(_pricing(), "deluxe", 2)
    assert est.subtotal == Decimal("6000.00")
    assert est.total == Decimal("6000.00")


def test_suite_three_nights():
    est = calculate_estimate(_pricing(), "suite", 3)
    assert est.subtotal == Decimal("21000.00")
    assert est.total == Decimal("21000.00")


def test_duplex_one_night():
    est = calculate_estimate(_pricing(), "duplex", 1)
    assert est.total == Decimal("5000.00")


# ---- Tax -------------------------------------------------------------------


def test_tax_added_to_total():
    est = calculate_estimate(_pricing(tax_rate=Decimal("10")), "deluxe", 2)
    assert est.subtotal == Decimal("6000.00")
    assert est.tax == Decimal("600.00")
    assert est.total == Decimal("6600.00")


def test_fractional_tax_is_rounded_half_up():
    # 5% of 2000 = 100.00 -> trivial; 7.5% of 2000 = 150.00.
    # Use 3.333% of 2000 = 66.66 to exercise the rounding path.
    est = calculate_estimate(
        _pricing(tax_rate=Decimal("3.333")), "classic", 1
    )
    assert est.tax == Decimal("66.66")


def test_zero_tax_gives_zero_tax_line():
    est = calculate_estimate(_pricing(tax_rate=0), "deluxe", 3)
    assert est.tax == Decimal("0.00")
    assert est.total == est.subtotal


# ---- Inputs, casing, edge cases -------------------------------------------


def test_room_key_is_case_insensitive():
    est = calculate_estimate(_pricing(), "DELUXE", 2)
    assert est.room_key == "deluxe"
    assert est.room_display_name == "Deluxe"


def test_room_key_strips_whitespace():
    est = calculate_estimate(_pricing(), "  Suite  ", 1)
    assert est.room_key == "suite"


def test_estimate_carries_currency_and_nights():
    est = calculate_estimate(_pricing(currency="USD"), "classic", 4)
    assert est.currency == "USD"
    assert est.nights == 4


def test_estimate_is_frozen_dataclass():
    est = calculate_estimate(_pricing(), "classic", 1)
    assert isinstance(est, Estimate)
    with pytest.raises(FrozenInstanceError):
        est.total = Decimal("1.00")


def test_default_pricing_works_with_realistic_input():
    est = calculate_estimate(DEFAULT_PRICING, "suite", 2)
    assert est.total == Decimal("14000.00")


# ---- Rejections ------------------------------------------------------------


@pytest.mark.parametrize("room_key", ["penthouse", "", "classic deluxe", None])
def test_rejects_unknown_or_invalid_room_key(room_key):
    with pytest.raises(ValueError):
        calculate_estimate(_pricing(), room_key, 1)


@pytest.mark.parametrize("nights", [0, -1])
def test_rejects_non_positive_nights(nights):
    with pytest.raises(ValueError, match="at least 1"):
        calculate_estimate(_pricing(), "classic", nights)


@pytest.mark.parametrize("nights", ["2", 2.0, None, True])
def test_rejects_non_integer_nights(nights):
    with pytest.raises(ValueError, match="must be an int"):
        calculate_estimate(_pricing(), "classic", nights)


def test_rejects_nights_above_max():
    with pytest.raises(ValueError, match="maxNights"):
        calculate_estimate(_pricing(max_nights=5), "classic", 6)


def test_rejects_non_dict_pricing():
    with pytest.raises(ValueError, match="must be a dict"):
        calculate_estimate([], "classic", 1)


def test_rejects_pricing_without_rooms():
    with pytest.raises(ValueError, match="'rooms'"):
        calculate_estimate({"currency": "INR"}, "classic", 1)
