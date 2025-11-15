"""Collector base logic for streaming market data."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncIterator, Iterable

from structlog import get_logger

from ..messaging.jetstream import JetStreamClient, JetStreamPublisherConfig
from ..config import Settings

logger = get_logger(__name__)


class CollectorBase(ABC):
    """Base class that handles lifecycle and JetStream publication."""

    subject: str = "ticks.raw"
    stream: str = "ticks"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._client = JetStreamClient(self.settings.nats)
        self._publisher_cfg = JetStreamPublisherConfig(
            subject=self.subject,
            stream=self.stream,
        )

    async def run(self) -> None:
        await self._client.connect()
        logger.info("collector.started", collector=self.__class__.__name__)
        try:
            async for payload in self.iter_events():
                await self._client.publish(self._publisher_cfg, payload)
        finally:
            await self._client.close()
            logger.info("collector.stopped", collector=self.__class__.__name__)

    @abstractmethod
    async def iter_events(self) -> AsyncIterator[bytes]:
        """Yield serialized TickEvent protobuf payloads."""
