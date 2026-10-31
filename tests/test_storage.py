"""Tests for DynamoDB persistence using moto's in-memory mock."""

from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

from pricing import Estimate
from storage import save_booking

TABLE = "hotel-bookings"


@pytest.fixture
def dyn_client():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName=TABLE,
            AttributeDefinitions=[
                {"AttributeName": "bookingId", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "bookingId", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


def _estimate(room_key="deluxe", nights=2, total="6000.00"):
    total_d = Decimal(total)
    return Estimate(
        currency="INR", room_key=room_key, room_display_name=room_key.title(),
        nights=nights, price_per_night=Decimal("3000.00"),
        subtotal=total_d, tax=Decimal("0.00"), total=total_d,
    )


def _get(client, booking_id):
    return client.get_item(
        TableName=TABLE, Key={"bookingId": {"S": booking_id}}
    )["Item"]


def test_save_writes_expected_item(dyn_client):
    bid = save_booking(
        _estimate(), session_id="sess-1",
        location="Bangalore", check_in_date="2099-04-01",
        client=dyn_client,
    )
    assert isinstance(bid, str) and len(bid) == 32

    item = _get(dyn_client, bid)
    assert item["location"]["S"] == "Bangalore"
    assert item["checkInDate"]["S"] == "2099-04-01"
    assert item["roomType"]["S"] == "deluxe"
    assert item["nights"]["N"] == "2"
    assert item["total"]["S"] == "6000.00"
    assert item["status"]["S"] == "SIMULATED"
    assert "expiresAt" in item


def test_same_inputs_produce_same_id(dyn_client):
    e = _estimate()
    kw = dict(location="X", check_in_date="2099-01-01", client=dyn_client)
    a = save_booking(e, session_id="s", **kw)
    b = save_booking(e, session_id="s", **kw)
    assert a == b


def test_different_session_different_id(dyn_client):
    e = _estimate()
    kw = dict(location="X", check_in_date="2099-01-01", client=dyn_client)
    a = save_booking(e, session_id="s1", **kw)
    b = save_booking(e, session_id="s2", **kw)
    assert a != b


def test_different_check_in_date_different_id(dyn_client):
    e = _estimate()
    a = save_booking(e, session_id="s", location="X",
                     check_in_date="2099-01-01", client=dyn_client)
    b = save_booking(e, session_id="s", location="X",
                     check_in_date="2099-01-02", client=dyn_client)
    assert a != b


def test_table_name_from_env(monkeypatch, dyn_client):
    monkeypatch.setenv("BOOKINGS_TABLE", TABLE)
    bid = save_booking(
        _estimate(), session_id="env", location="X",
        check_in_date="2099-01-01", client=dyn_client,
    )
    assert _get(dyn_client, bid)["bookingId"]["S"] == bid


def test_missing_table_raises(dyn_client):
    from botocore.exceptions import ClientError
    with pytest.raises(ClientError):
        save_booking(
            _estimate(), session_id="s", location="X",
            check_in_date="2099-01-01",
            table_name="does-not-exist", client=dyn_client,
        )
