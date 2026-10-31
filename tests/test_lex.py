from lex import (
    close_failed,
    close_fulfilled,
    delegate,
    elicit_slot,
    get_slot_value,
)


def _intent(slots):
    return {"name": "BookHotel", "slots": slots, "state": "InProgress"}


def _slot(interpreted):
    return {"value": {"interpretedValue": interpreted}, "shape": "Scalar"}


# ---- get_slot_value --------------------------------------------------------


def test_get_slot_value_returns_interpreted_string():
    intent = _intent({"Location": _slot("Bangalore")})
    assert get_slot_value(intent, "Location") == "Bangalore"


def test_get_slot_value_strips_whitespace():
    intent = _intent({"Location": _slot("   Bangalore   ")})
    assert get_slot_value(intent, "Location") == "Bangalore"


def test_get_slot_value_missing_slot_returns_empty_string():
    intent = _intent({})
    assert get_slot_value(intent, "Location") == ""


def test_get_slot_value_missing_value_returns_empty_string():
    intent = _intent({"Location": {"shape": "Scalar"}})
    assert get_slot_value(intent, "Location") == ""


def test_get_slot_value_non_string_value_returns_empty_string():
    intent = _intent({"Nights": {"value": {"interpretedValue": 3}}})
    assert get_slot_value(intent, "Nights") == ""


def test_get_slot_value_handles_missing_slots_key():
    assert get_slot_value({}, "Location") == ""
    assert get_slot_value({"slots": None}, "Location") == ""


# ---- elicit_slot -----------------------------------------------------------


def test_elicit_slot_has_expected_shape():
    slots = {"Location": _slot("Bangalore")}
    response = elicit_slot(
        "BookHotel", slots, "CheckInDate", "What date will you arrive?"
    )

    assert response["sessionState"]["dialogAction"]["type"] == "ElicitSlot"
    assert (
        response["sessionState"]["dialogAction"]["slotToElicit"]
        == "CheckInDate"
    )
    assert response["sessionState"]["intent"]["state"] == "InProgress"
    assert response["sessionState"]["intent"]["name"] == "BookHotel"
    assert response["sessionState"]["intent"]["slots"] == slots
    assert response["messages"] == [
        {"contentType": "PlainText", "content": "What date will you arrive?"}
    ]


def test_elicit_slot_does_not_mutate_input_slots():
    slots = {"Location": _slot("Bangalore")}
    snapshot = {k: dict(v) for k, v in slots.items()}
    elicit_slot("BookHotel", slots, "CheckInDate", "Date?")
    assert slots == snapshot


def test_elicit_slot_tolerates_missing_slots():
    response = elicit_slot("BookHotel", None, "Location", "City?")
    assert response["sessionState"]["intent"]["slots"] == {}


# ---- delegate --------------------------------------------------------------


def test_delegate_has_no_messages():
    response = delegate("BookHotel", {"Location": _slot("Paris")})
    assert response["sessionState"]["dialogAction"]["type"] == "Delegate"
    assert response["sessionState"]["intent"]["state"] == "InProgress"
    assert "messages" not in response


# ---- close_fulfilled -------------------------------------------------------


def test_close_fulfilled_sets_state_and_message():
    response = close_fulfilled(
        "BookHotel", {"Location": _slot("Bangalore")}, "Booking estimated."
    )
    assert response["sessionState"]["dialogAction"]["type"] == "Close"
    assert response["sessionState"]["intent"]["state"] == "Fulfilled"
    assert response["messages"] == [
        {"contentType": "PlainText", "content": "Booking estimated."}
    ]


# ---- close_failed ----------------------------------------------------------


def test_close_failed_sets_state_and_message():
    response = close_failed(
        "BookHotel", None, "Sorry, something went wrong."
    )
    assert response["sessionState"]["dialogAction"]["type"] == "Close"
    assert response["sessionState"]["intent"]["state"] == "Failed"
    assert response["sessionState"]["intent"]["slots"] == {}
    assert response["messages"][0]["content"] == "Sorry, something went wrong."


# ---- message content type --------------------------------------------------


def test_all_builders_use_plain_text_messages():
    builders = [
        elicit_slot("BookHotel", {}, "Location", "x"),
        close_fulfilled("BookHotel", {}, "x"),
        close_failed("BookHotel", {}, "x"),
    ]
    for response in builders:
        assert response["messages"][0]["contentType"] == "PlainText"
