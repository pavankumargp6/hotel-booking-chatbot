import json
from decimal import Decimal

import pytest

from config import DEFAULT_PRICING, load_pricing


def _complete_rooms(**overrides):
    rooms = {
        "classic": {"displayName": "Classic", "pricePerNight": 2000},
        "deluxe": {"displayName": "Deluxe", "pricePerNight": 3000},
        "duplex": {"displayName": "Duplex", "pricePerNight": 5000},
        "suite": {"displayName": "Suite", "pricePerNight": 7000},
    }
    for key, value in overrides.items():
        rooms[key] = value
    return rooms


def test_returns_defaults_when_env_unset(monkeypatch):
    monkeypatch.delenv("PRICING_CONFIG", raising=False)
    pricing = load_pricing()
    assert pricing["currency"] == "INR"
    assert pricing["maxNights"] == 30
    assert pricing["rooms"]["deluxe"]["pricePerNight"] == 3000


def test_returns_defaults_when_env_blank(monkeypatch):
    monkeypatch.setenv("PRICING_CONFIG", "   ")
    assert load_pricing() == DEFAULT_PRICING


def test_defaults_are_not_shared_by_reference(monkeypatch):
    monkeypatch.delenv("PRICING_CONFIG", raising=False)
    first = load_pricing()
    first["rooms"]["deluxe"]["pricePerNight"] = 999999
    second = load_pricing()
    assert second["rooms"]["deluxe"]["pricePerNight"] == 3000


def test_parses_valid_config(monkeypatch):
    custom = {
        "currency": "USD",
        "maxNights": 7,
        "taxRatePercent": 10,
        "rooms": _complete_rooms(
            suite={"displayName": "Suite", "pricePerNight": 400},
        ),
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(custom))
    pricing = load_pricing()
    assert pricing["currency"] == "USD"
    assert pricing["maxNights"] == 7
    assert pricing["taxRatePercent"] == 10
    assert pricing["rooms"]["suite"]["pricePerNight"] == 400


def test_float_prices_are_parsed_as_decimal(monkeypatch):
    custom = {
        "rooms": _complete_rooms(
            classic={"displayName": "Classic", "pricePerNight": 1999.99},
        ),
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(custom))
    pricing = load_pricing()
    price = pricing["rooms"]["classic"]["pricePerNight"]
    assert isinstance(price, Decimal)
    assert price == Decimal("1999.99")


def test_optional_fields_get_defaults(monkeypatch):
    minimal = {"rooms": _complete_rooms()}
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(minimal))
    pricing = load_pricing()
    assert pricing["currency"] == "INR"
    assert pricing["maxNights"] == 30
    assert pricing["taxRatePercent"] == 0


def test_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv("PRICING_CONFIG", "{not json")
    with pytest.raises(ValueError, match="valid JSON"):
        load_pricing()


def test_rejects_non_object_root(monkeypatch):
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(["nope"]))
    with pytest.raises(ValueError, match="JSON object"):
        load_pricing()


def test_rejects_missing_rooms(monkeypatch):
    monkeypatch.setenv("PRICING_CONFIG", json.dumps({"currency": "INR"}))
    with pytest.raises(ValueError, match="rooms"):
        load_pricing()


def test_rejects_missing_required_room(monkeypatch):
    partial = {
        "rooms": {"classic": {"displayName": "Classic", "pricePerNight": 2000}}
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(partial))
    with pytest.raises(ValueError, match="missing rooms"):
        load_pricing()


def test_rejects_room_missing_fields(monkeypatch):
    bad = {
        "rooms": _complete_rooms(
            classic={"displayName": "Classic"},
        ),
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(bad))
    with pytest.raises(ValueError, match="displayName and pricePerNight"):
        load_pricing()


def test_rejects_non_numeric_price(monkeypatch):
    bad = {
        "rooms": _complete_rooms(
            classic={"displayName": "Classic", "pricePerNight": "expensive"},
        ),
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(bad))
    with pytest.raises(ValueError, match="pricePerNight must be a number"):
        load_pricing()


def test_rejects_boolean_price(monkeypatch):
    bad = {
        "rooms": _complete_rooms(
            classic={"displayName": "Classic", "pricePerNight": True},
        ),
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(bad))
    with pytest.raises(ValueError, match="pricePerNight must be a number"):
        load_pricing()


def test_rejects_zero_or_negative_price(monkeypatch):
    bad = {
        "rooms": _complete_rooms(
            deluxe={"displayName": "Deluxe", "pricePerNight": 0},
        ),
    }
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(bad))
    with pytest.raises(ValueError, match="greater than zero"):
        load_pricing()


def test_rejects_non_integer_max_nights(monkeypatch):
    bad = {"maxNights": "many", "rooms": _complete_rooms()}
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(bad))
    with pytest.raises(ValueError, match="maxNights must be an integer"):
        load_pricing()


def test_rejects_negative_tax(monkeypatch):
    bad = {"taxRatePercent": -5, "rooms": _complete_rooms()}
    monkeypatch.setenv("PRICING_CONFIG", json.dumps(bad))
    with pytest.raises(ValueError, match="taxRatePercent cannot be negative"):
        load_pricing()
