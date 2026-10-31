"""Amazon Lex V2 response builders.

These functions are pure: they take plain inputs and return the exact
JSON structure that a Lex V2 fulfillment Lambda is expected to return.

They do not call AWS, log, or read the environment. That keeps them
trivially testable and makes ``lambda_handler`` a thin dispatcher.

Lex V2 reference shape (simplified):

    {
      "sessionState": {
        "dialogAction": {"type": "...", "slotToElicit": "..."},
        "intent": {
          "name": "BookHotel",
          "slots": {... as received from Lex ...},
          "state": "InProgress|Fulfilled|Failed"
        }
      },
      "messages": [{"contentType": "PlainText", "content": "..."}]
    }
"""


def get_slot_value(intent, slot_name):
    """Return the interpreted value for a slot, or '' if absent.

    Lex V2 nests values as
    ``intent["slots"][slot_name]["value"]["interpretedValue"]``.
    Anything missing, empty, or non-string becomes ``""`` so that
    upstream validation always sees a string.
    """
    slots = intent.get("slots") or {}
    slot = slots.get(slot_name) or {}
    value = slot.get("value") or {}
    raw = value.get("interpretedValue")
    if not isinstance(raw, str):
        return ""
    return raw.strip()


def elicit_slot(intent_name, slots, slot_to_elicit, message):
    """Ask Lex to re-prompt for a specific slot."""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": slot_to_elicit,
            },
            "intent": {
                "name": intent_name,
                "slots": slots or {},
                "state": "InProgress",
            },
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }


def delegate(intent_name, slots):
    """Let Lex continue with its normal slot elicitation."""
    return {
        "sessionState": {
            "dialogAction": {"type": "Delegate"},
            "intent": {
                "name": intent_name,
                "slots": slots or {},
                "state": "InProgress",
            },
        }
    }


def close_fulfilled(intent_name, slots, message):
    """Close the intent successfully with a user-facing message."""
    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": intent_name,
                "slots": slots or {},
                "state": "Fulfilled",
            },
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }


def close_failed(intent_name, slots, message):
    """Close the intent as failed with a user-facing message."""
    return {
        "sessionState": {
            "dialogAction": {"type": "Close"},
            "intent": {
                "name": intent_name,
                "slots": slots or {},
                "state": "Failed",
            },
        },
        "messages": [{"contentType": "PlainText", "content": message}],
    }
