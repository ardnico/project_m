"""NATS JetStream helper utilities."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Awaitable, Callable, Optional

from nats.aio.client import Client as NATS
from nats.js.client import JetStreamContext
from structlog import get_logger

from ..config import NatsConfig

logger = get_logger(__name__)


@dataclass(slots=True)
class JetStreamPublisherConfig:
    """Configuration for publishing signals to JetStream."""

    subject: str
    stream: str
    ordered: bool = True
    timeout: float = 2.0


class JetStreamClient:
    """Wrapper around the NATS JetStream client."""

    def __init__(self, config: NatsConfig) -> None:
        self._config = config
        self._nc: Optional[NATS] = None
        self._js: Optional[JetStreamContext] = None

    async def connect(self) -> None:
        """Connect to NATS and prepare JetStream context."""

        if self._nc is not None:
            return

        self._nc = NATS()
        await self._nc.connect(servers=self._config.servers)
        self._js = self._nc.jetstream()
        logger.info("jetstream.connected", servers=self._config.servers)

    async def close(self) -> None:
        """Close underlying NATS connection."""

        if self._nc is not None:
            await self._nc.drain()
            await self._nc.close()
            logger.info("jetstream.closed")
        self._nc = None
        self._js = None

    @property
    def jetstream(self) -> JetStreamContext:
        if self._js is None:
            raise RuntimeError("JetStream client not connected")
        return self._js

    async def publish(self, config: JetStreamPublisherConfig, payload: bytes) -> None:
        """Publish payload to JetStream subject with optional ordering."""

        js = self.jetstream
        await js.publish(config.subject, payload, timeout=config.timeout)
        logger.debug(
            "jetstream.publish",
            subject=config.subject,
            size=len(payload),
        )

    @asynccontextmanager
    async def subscription(
        self,
        subject: str,
        durable: Optional[str] = None,
        cb: Optional[Callable[[bytes], Awaitable[None]]] = None,
    ) -> AsyncIterator[None]:
        """Create a JetStream subscription with managed lifecycle."""

        js = self.jetstream
        sub = await js.pull_subscribe(
            subject=subject,
            durable=durable or self._config.durable,
        )
        logger.info("jetstream.subscribed", subject=subject, durable=durable)
        try:
            if cb is not None:
                await self._consume_loop(sub, cb)
            yield
        finally:
            await sub.unsubscribe()
            logger.info("jetstream.unsubscribed", subject=subject, durable=durable)

    async def _consume_loop(self, sub, cb: Callable[[bytes], Awaitable[None]]) -> None:
        while True:
            msgs = await sub.fetch(1, timeout=1)
            for msg in msgs:
                try:
                    await cb(msg.data)
                    await msg.ack()
                except Exception:  # pragma: no cover - defensive logging
                    logger.exception("jetstream.consumer.error")
                    await msg.nak()


__all__ = ["JetStreamClient", "JetStreamPublisherConfig"]
