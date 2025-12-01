from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterator


from src.app.price_poller import PricePoller
from src.infra.db import init_db
from src.infra.ig_client import PriceSnapshot


class StubIGClient:
    def __init__(self, snapshots: Iterator[PriceSnapshot]):
        self.snapshots = snapshots

    def fetch_price(self, epic: str) -> PriceSnapshot:
        return next(self.snapshots)


class StopAfterOnePrice(Exception):
    pass


def test_price_poller_persists_snapshot(tmp_path) -> None:
    db_path = tmp_path / "prices.db"
    conn = init_db(str(db_path))

    snapshots = iter(
        [
            PriceSnapshot(
                epic="EPIC1",
                bid=1.0,
                ask=2.0,
                mid=1.5,
                timestamp=datetime.fromisoformat("2024-01-01T00:00:00"),
            )
        ]
    )
    client = StubIGClient(snapshots)

    poller = PricePoller(client, ["EPIC1"], 0, conn, logger=None)
    poller.run(iterations=1)

    rows = list(conn.execute("SELECT epic, bid, ask, mid, timestamp FROM prices"))
    assert len(rows) == 1
    assert rows[0][0] == "EPIC1"
