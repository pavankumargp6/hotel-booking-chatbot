"""AWS Lambda handler for the HotelBookingBot (Amazon Lex V2).

Wires together:

  - ``config.load_pricing``        validated pricing configuration
  - ``validation.validate_*``      per-slot input validation
  - ``pricing.calculate_estimate`` Decimal-based price calculation
  - ``lex.*``                      Lex V2 response builders

Handles two ``invocationSource`` values:

  - ``DialogCodeHook``       validate filled slots; delegate unfilled ones
  - ``FulfillmentCodeHook``  validate everything, compute estimate, close

Any unhandled exception becomes a ``Close`` with ``Failed`` state and a
generic user-facing message; the real error is logged for CloudWatch.
"""

import logging

from config import load_pricing
from lex import (
    close_failed,
    close_fulfilled,
    delegate,
    elicit_slot,
    get_slot_value,
)
from pricing import calculate_estimate
from validation import (
    REQUIRED_SLOTS,
    SLOT_CHECK_IN_DATE,
    SLOT_LOCATION,
    SLOT_NIGHTS,
    SLOT_ROOM_TYPE,
    validate_check_in_date,
    validate_location,
    validate_nights,
    validate_room_type,
)

logger = logging.getLogger(__name__)

INTENT_NAME = "BookHotel"
GENERIC_ERROR_MESSAGE = (
    "Sorry, I could not process the booking right now. Please try again."
)
WRONG_INTENT_MESSAGE = (
    "This fulfillment handler only supports the BookHotel intent."
)


def _intent_from_event(event):
    session_state = event.get("sessionState") or {}
    return session_state.get("intent") or {}


def _validate_slot(slot_name, value, pricing):
    """Dispatch to the right validator for a single slot."""
    if slot_name == SLOT_LOCATION:
        return validate_location(value)
    if slot_name == SLOT_CHECK_IN_DATE:
        return validate_check_in_date(value)
    if slot_name == SLOT_NIGHTS:
        return validate_nights(value, pricing["maxNights"])
    if slot_name == SLOT_ROOM_TYPE:
        return validate_room_type(value, pricing["rooms"])
    return None


def _validate_filled_slots(intent, pricing):
    """Validate only slots that currently have values.

    Returns the first ``SlotError``, or ``None`` if every filled slot is
    valid. Empty slots are left for Lex to elicit.
    """
    for slot_name in REQUIRED_SLOTS:
        value = get_slot_value(intent, slot_name)
        if not value:
            continue
        error = _validate_slot(slot_name, value, pricing)
        if error:
            return error
    return None


def _first_missing_slot(intent):
    """Return the first empty required slot, in the canonical order."""
    for slot_name in REQUIRED_SLOTS:
        if not get_slot_value(intent, slot_name):
            return slot_name
    return None


def _format_money(amount):
    return f"{amount:,.2f}"


def _build_confirmation(intent, estimate):
    location = get_slot_value(intent, SLOT_LOCATION)
    check_in = get_slot_value(intent, SLOT_CHECK_IN_DATE)
    nights = get_slot_value(intent, SLOT_NIGHTS)
    currency = estimate.currency

    return (
        "Estimated booking summary\n"
        "\n"
        f"Location: {location}\n"
        f"Check-in: {check_in}\n"
        f"Nights: {nights}\n"
        f"Room: {estimate.room_display_name}\n"
        f"Price per night: {currency} "
        f"{_format_money(estimate.price_per_night)}\n"
        f"Estimated total: {currency} {_format_money(estimate.total)}\n"
        "\n"
        "This is a simulated booking estimate. "
        "No real hotel reservation has been made."
    )


def lambda_handler(event, context):
    """Lex V2 fulfillment entry point."""
    intent = _intent_from_event(event)
    intent_name = intent.get("name") or INTENT_NAME
    slots = intent.get("slots") or {}

    try:
        if intent_name != INTENT_NAME:
            logger.warning("Unexpected intent: %s", intent_name)
            return close_failed(intent_name, slots, WRONG_INTENT_MESSAGE)

        pricing = load_pricing()
        invocation_source = event.get("invocationSource")

        if invocation_source == "DialogCodeHook":
            error = _validate_filled_slots(intent, pricing)
            if error:
                return elicit_slot(
                    intent_name, slots, error.slot_name, error.message
                )
            return delegate(intent_name, slots)

        if invocation_source == "FulfillmentCodeHook":
            missing = _first_missing_slot(intent)
            if missing:
                return elicit_slot(
                    intent_name,
                    slots,
                    missing,
                    f"Please provide your {missing.lower()}.",
                )

            error = _validate_filled_slots(intent, pricing)
            if error:
                return elicit_slot(
                    intent_name, slots, error.slot_name, error.message
                )

            room_key = get_slot_value(intent, SLOT_ROOM_TYPE)
            nights = int(get_slot_value(intent, SLOT_NIGHTS))
            estimate = calculate_estimate(pricing, room_key, nights)

            logger.info(
                "Fulfilled BookHotel: room=%s nights=%s location_length=%s",
                estimate.room_key,
                nights,
                len(get_slot_value(intent, SLOT_LOCATION)),
            )

            return close_fulfilled(
                intent_name, slots, _build_confirmation(intent, estimate)
            )

        logger.warning("Unknown invocationSource: %s", invocation_source)
        return delegate(intent_name, slots)

    except Exception:
        logger.exception("Unhandled error in HotelBooking fulfillment")
        return close_failed(intent_name, slots, GENERIC_ERROR_MESSAGE)
