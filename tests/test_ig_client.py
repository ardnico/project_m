from __future__ import annotations

from datetime import datetime

import pytest
import responses

from src.infra.ig_client import AuthenticationError, IGClient


@pytest.fixture()
def client() -> IGClient:
    return IGClient(
        base_url="https://demo-api.ig.com/gateway/deal",
        api_key="key",
        username="user",
        password="pass",
    )


def test_login_success(client: IGClient) -> None:
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://demo-api.ig.com/gateway/deal/session",
            json={"accountId": "ABC"},
            headers={"CST": "cst123", "X-SECURITY-TOKEN": "sec456"},
            status=200,
        )
        tokens = client.login()
        assert tokens["CST"] == "cst123"
        assert tokens["X-SECURITY-TOKEN"] == "sec456"


def test_login_auth_failure(client: IGClient) -> None:
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.POST,
            "https://demo-api.ig.com/gateway/deal/session",
            json={},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client.login()


def test_fetch_price_success(client: IGClient) -> None:
    client.tokens = {"CST": "cst123", "X-SECURITY-TOKEN": "sec456"}
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://demo-api.ig.com/gateway/deal/prices/EPIC1",
            json={
                "prices": [
                    {
                        "bid": 1.0,
                        "ask": 2.0,
                        "snapshotTimeUTC": "2024-01-01T00:00:00",
                    }
                ]
            },
            status=200,
        )
        snapshot = client.fetch_price("EPIC1")
        assert snapshot.mid == 1.5
        assert isinstance(snapshot.timestamp, datetime)
