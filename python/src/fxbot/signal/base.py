"""Signal generation base class."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

from structlog import get_logger

from ..config import Settings
from ..messaging.jetstream import JetStreamClient, JetStreamPublisherConfig
from ..models.signal import OrderSide, OrderType, TradeSignalModel

logger = get_logger(__name__)


class StrategyBase(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or Settings()
        self._client = JetStreamClient(self.settings.nats)
        self._publisher_cfg = JetStreamPublisherConfig(
            subject=self.settings.nats.subject,
            stream=self.settings.nats.stream,
        )

    async def run(self) -> None:
        """Connect to JetStream and run the strategy loop."""

        await self._client.connect()
        logger.info("strategy.started", strategy=self.strategy_id)
        try:
            await self._loop()
        finally:
            await self._client.close()
            logger.info("strategy.stopped", strategy=self.strategy_id)

    async def _loop(self) -> None:
        async for signal in self.generate_signals():
            await self.publish_signal(signal)

    async def publish_signal(self, signal: TradeSignalModel) -> None:
        """Publish a signal via JetStream."""

        payload = signal.serialize()
        await self._client.publish(self._publisher_cfg, payload)
        logger.info(
            "strategy.signal_published",
            signal_id=signal.signal_id,
            strategy=self.strategy_id,
            symbol=signal.symbol,
        )

    @property
    def strategy_id(self) -> str:
        return self.__class__.__name__.lower()

    @abstractmethod
    async def generate_signals(self):
        """Async iterator yielding TradeSignalModel objects."""

    def build_signal(
        self,
        *,
        signal_id: str,
        symbol: str,
        side: OrderSide,
        size: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        slippage_tolerance: float = 0.0,
        ts: Optional[datetime] = None,
    ) -> TradeSignalModel:
        return TradeSignalModel(
            signal_id=signal_id,
            ts=ts or datetime.now(timezone.utc),
            strategy_id=self.strategy_id,
            symbol=symbol,
            side=side,
            size=size,
            order_type=order_type,
            limit_price=limit_price,
            slippage_tolerance=slippage_tolerance,
        )


SignalMessage = TradeSignalModel

__all__ = ["StrategyBase", "SignalMessage"]
