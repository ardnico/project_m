from __future__ import annotations

from datetime import datetime

from src.infra.demo_client import DemoIGClient


def test_demo_client_login_and_prices() -> None:
    client = DemoIGClient(epics=["EPIC1"], starting_balance=12345.0, seed=1)
    tokens = client.login()
    assert tokens["CST"].startswith("DEMO")

    first = client.fetch_price("EPIC1")
    second = client.fetch_price("EPIC1")
    assert first.epic == "EPIC1"
    assert first.bid < first.ask
    assert first.mid > 0
    assert isinstance(first.timestamp, datetime)
    assert second.mid != first.mid
    assert second.timestamp >= first.timestamp

    third = client.fetch_price("NEW")
    assert third.epic == "NEW"
    assert third.bid > 0
