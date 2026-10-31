import logging

from lambda_handler import (
    GENERIC_ERROR_MESSAGE,
    INTENT_NAME,
    lambda_handler,
)

ALL_VALID_SLOTS = {
    "Location": {"value": {"interpretedValue": "Bangalore"}, "shape": "Scalar"},
    "CheckInDate": {"value": {"interpretedValue": "2099-04-01"}},
    "Nights": {"value": {"interpretedValue": "2"}},
    "RoomType": {"value": {"interpretedValue": "Deluxe"}},
}


def _event(invocation_source, slots, intent_name=INTENT_NAME):
    return {
        "sessionState": {
            "intent": {
                "name": intent_name,
                "slots": slots,
                "state": "InProgress",
            },
            "sessionAttributes": {},
        },
        "invocationSource": invocation_source,
        "inputMode": "Text",
    }


def _slot(value):
    return {"value": {"interpretedValue": value}, "shape": "Scalar"}


# ---- DialogCodeHook --------------------------------------------------------


def test_dialog_code_hook_empty_slots_delegates():
    response = lambda_handler(_event("DialogCodeHook", {}), None)
    assert response["sessionState"]["dialogAction"]["type"] == "Delegate"
    assert response["sessionState"]["intent"]["state"] == "InProgress"


def test_dialog_code_hook_all_valid_delegates():
    response = lambda_handler(
        _event("DialogCodeHook", ALL_VALID_SLOTS), None
    )
    assert response["sessionState"]["dialogAction"]["type"] == "Delegate"


def test_dialog_code_hook_past_date_elicits_checkin():
    slots = {"CheckInDate": _slot("2020-01-01")}
    response = lambda_handler(_event("DialogCodeHook", slots), None)
    assert response["sessionState"]["dialogAction"]["type"] == "ElicitSlot"
    assert (
        response["sessionState"]["dialogAction"]["slotToElicit"]
        == "CheckInDate"
    )
    assert "past" in response["messages"][0]["content"].lower()


def test_dialog_code_hook_invalid_room_elicits_room_type():
    slots = {"RoomType": _slot("Penthouse")}
    response = lambda_handler(_event("DialogCodeHook", slots), None)
    assert (
        response["sessionState"]["dialogAction"]["slotToElicit"] == "RoomType"
    )


def test_dialog_code_hook_invalid_nights_elicits_nights():
    slots = {"Nights": _slot("999")}
    response = lambda_handler(_event("DialogCodeHook", slots), None)
    assert response["sessionState"]["dialogAction"]["slotToElicit"] == "Nights"


# ---- FulfillmentCodeHook ---------------------------------------------------


def test_fulfillment_returns_fulfilled_estimate():
    response = lambda_handler(
        _event("FulfillmentCodeHook", ALL_VALID_SLOTS), None
    )
    assert response["sessionState"]["dialogAction"]["type"] == "Close"
    assert response["sessionState"]["intent"]["state"] == "Fulfilled"
    assert response["sessionState"]["intent"]["slots"] == ALL_VALID_SLOTS


def test_fulfillment_message_includes_disclaimer():
    response = lambda_handler(
        _event("FulfillmentCodeHook", ALL_VALID_SLOTS), None
    )
    content = response["messages"][0]["content"]
    assert "simulated booking" in content.lower()
    assert "No real hotel reservation" in content


def test_fulfillment_message_includes_expected_total():
    # Deluxe x 2 nights = INR 6000 (zero tax default).
    response = lambda_handler(
        _event("FulfillmentCodeHook", ALL_VALID_SLOTS), None
    )
    content = response["messages"][0]["content"]
    assert "6,000.00" in content
    assert "Deluxe" in content


def test_fulfillment_missing_location_elicits_location():
    slots = dict(ALL_VALID_SLOTS)
    del slots["Location"]
    response = lambda_handler(_event("FulfillmentCodeHook", slots), None)
    assert response["sessionState"]["dialogAction"]["type"] == "ElicitSlot"
    assert (
        response["sessionState"]["dialogAction"]["slotToElicit"] == "Location"
    )


def test_fulfillment_missing_multiple_elicits_first_missing():
    slots = {
        "Nights": _slot("2"),
        "RoomType": _slot("Deluxe"),
    }
    response = lambda_handler(_event("FulfillmentCodeHook", slots), None)
    assert (
        response["sessionState"]["dialogAction"]["slotToElicit"] == "Location"
    )


def test_fulfillment_invalid_room_elicits_room_type():
    slots = dict(ALL_VALID_SLOTS)
    slots["RoomType"] = _slot("Penthouse")
    response = lambda_handler(_event("FulfillmentCodeHook", slots), None)
    assert (
        response["sessionState"]["dialogAction"]["slotToElicit"] == "RoomType"
    )


def test_fulfillment_room_type_case_insensitive():
    slots = dict(ALL_VALID_SLOTS)
    slots["RoomType"] = _slot("DELUXE")
    response = lambda_handler(_event("FulfillmentCodeHook", slots), None)
    assert response["sessionState"]["intent"]["state"] == "Fulfilled"
    assert "Deluxe" in response["messages"][0]["content"]


def test_fulfillment_tax_is_applied_when_configured(monkeypatch):
    monkeypatch.setenv(
        "PRICING_CONFIG",
        (
            '{"currency":"INR","maxNights":30,"taxRatePercent":10,'
            '"rooms":{'
            '"classic":{"displayName":"Classic","pricePerNight":2000},'
            '"deluxe":{"displayName":"Deluxe","pricePerNight":3000},'
            '"duplex":{"displayName":"Duplex","pricePerNight":5000},'
            '"suite":{"displayName":"Suite","pricePerNight":7000}}}'
        ),
    )
    response = lambda_handler(
        _event("FulfillmentCodeHook", ALL_VALID_SLOTS), None
    )
    content = response["messages"][0]["content"]
    # 3000 * 2 = 6000 subtotal, +10% tax = 6600 total.
    assert "6,600.00" in content


# ---- Robustness ------------------------------------------------------------


def test_wrong_intent_closes_failed():
    response = lambda_handler(
        _event("FulfillmentCodeHook", ALL_VALID_SLOTS, intent_name="CancelHotel"),
        None,
    )
    assert response["sessionState"]["intent"]["state"] == "Failed"
    assert "BookHotel" in response["messages"][0]["content"]


def test_empty_event_delegates():
    response = lambda_handler({}, None)
    assert response["sessionState"]["dialogAction"]["type"] == "Delegate"


def test_unknown_invocation_source_delegates():
    response = lambda_handler(_event("SomeOtherSource", ALL_VALID_SLOTS), None)
    assert response["sessionState"]["dialogAction"]["type"] == "Delegate"


def test_load_pricing_error_returns_generic_failure(monkeypatch, caplog):
    def boom():
        raise ValueError("PRICING_CONFIG must be valid JSON")

    monkeypatch.setattr("lambda_handler.load_pricing", boom)

    with caplog.at_level(logging.ERROR):
        response = lambda_handler(
            _event("FulfillmentCodeHook", ALL_VALID_SLOTS), None
        )

    assert response["sessionState"]["intent"]["state"] == "Failed"
    content = response["messages"][0]["content"]
    assert content == GENERIC_ERROR_MESSAGE
    # Internal detail must not leak to the user.
    assert "PRICING_CONFIG" not in content
    # And the error must be logged for CloudWatch.
    assert any(
        "Unhandled error" in r.message for r in caplog.records
    )
