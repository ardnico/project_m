from __future__ import annotations

import logging
import random
from datetime import datetime
from typing import Dict, Iterable, Optional

from src.infra.ig_client import PriceSnapshot


class DemoIGClient:
    """Offline client that simulates IG price data and login tokens."""

    def __init__(
        self,
        epics: Iterable[str],
        starting_balance: float = 100_000.0,
        seed: Optional[int] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.starting_balance = starting_balance
        self.random = random.Random(seed)
        self.tokens: Dict[str, str] = {"CST": "DEMO-CST", "X-SECURITY-TOKEN": "DEMO-SECURITY"}
        self.prices: Dict[str, float] = {}
        for epic in epics:
            self.prices[epic] = self._initial_price(epic)

    def close(self) -> None:  # pragma: no cover - maintained for interface parity
        return None

    def _initial_price(self, epic: str) -> float:
        base = 100 + (abs(hash(epic)) % 50)
        return base + self.random.random()

    def login(self) -> Dict[str, str]:
        self.logger.info("Starting demo mode with virtual balance %.2f", self.starting_balance)
        return self.tokens

    def _next_mid(self, epic: str) -> float:
        mid = self.prices.get(epic, self._initial_price(epic))
        drift = self.random.uniform(-0.5, 0.5)
        mid = max(0.0001, mid + drift)
        self.prices[epic] = mid
        return mid

    def fetch_price(self, epic: str) -> PriceSnapshot:
        mid = self._next_mid(epic)
        spread = max(0.05, abs(self.random.uniform(0.05, 0.2)))
        bid = max(0.0001, mid - spread / 2)
        ask = bid + spread
        self.logger.debug("Demo price for %s: bid=%.5f ask=%.5f", epic, bid, ask)
        return PriceSnapshot(epic=epic, bid=bid, ask=ask, mid=(bid + ask) / 2, timestamp=datetime.utcnow())


__all__ = ["DemoIGClient"]
