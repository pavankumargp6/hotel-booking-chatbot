import pytest


@pytest.fixture(autouse=True)
def _mock_save_booking(monkeypatch):
    """Mock DynamoDB persistence for all handler tests by default.

    Tests that want real persistence override this fixture or patch
    `lambda_handler.save_booking` themselves.
    """
    import lambda_handler

    def _fake(*args, **kwargs):
        return "bk_00000000000000000000000000000000"

    monkeypatch.setattr(lambda_handler, "save_booking", _fake)
