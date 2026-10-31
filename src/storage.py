"""DynamoDB persistence for hotel booking estimates.

Writes one immutable record per successful fulfillment of the BookHotel
intent. The record is an audit trail of the estimated price; it is NOT
a real reservation (the confirmation message says so explicitly).

Idempotency: `bookingId` is derived from the Lex `sessionId` plus all
booking parameters, so a retried fulfillment for the same session
produces the same key. The condition expression makes the second write
a no-op, not a duplicate.
"""

import hashlib
import logging
import os
from datetime import UTC, datetime, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

DEFAULT_TABLE_NAME = "hotel-bookings"
TTL_DAYS = 30
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("dynamodb")
    return _client


def _table_name(table_name):
    return table_name or os.environ.get("BOOKINGS_TABLE", DEFAULT_TABLE_NAME)


def _derive_booking_id(session_id, location, check_in_date, nights, room_key):
    material = f"{session_id}|{location}|{check_in_date}|{nights}|{room_key}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def save_booking(
    estimate, *, session_id, location, check_in_date,
    table_name=None, client=None,
):
    """Persist one booking record. Returns the bookingId.

    Raises on failure other than a benign duplicate write.
    """
    booking_id = _derive_booking_id(
        session_id, location, check_in_date,
        estimate.nights, estimate.room_key,
    )
    now = datetime.now(UTC)
    expires_at = int((now + timedelta(days=TTL_DAYS)).timestamp())

    item = {
        "bookingId": {"S": booking_id},
        "createdAt": {"S": now.isoformat()},
        "sessionId": {"S": session_id},
        "location": {"S": location},
        "checkInDate": {"S": check_in_date},
        "nights": {"N": str(estimate.nights)},
        "roomType": {"S": estimate.room_key},
        "subtotal": {"S": str(estimate.subtotal)},
        "tax": {"S": str(estimate.tax)},
        "total": {"S": str(estimate.total)},
        "currency": {"S": estimate.currency},
        "status": {"S": "SIMULATED"},
        "expiresAt": {"N": str(expires_at)},
    }

    try:
        (client or _get_client()).put_item(
            TableName=_table_name(table_name),
            Item=item,
            ConditionExpression="attribute_not_exists(bookingId)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            logger.info("Booking %s already persisted (idempotent retry)", booking_id)
            return booking_id
        raise

    logger.info("Persisted booking %s", booking_id)
    return booking_id
