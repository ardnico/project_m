from __future__ import annotations

import logging
import time
from typing import Iterable, Optional

from src.infra.db import store_price
from src.infra.ig_client import AuthenticationError, IGClient, IGClientError


class PricePoller:
    def __init__(
        self,
        ig_client: IGClient,
        epics: Iterable[str],
        interval_seconds: int,
        db_conn,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.ig_client = ig_client
        self.epics = list(epics)
        self.interval_seconds = interval_seconds
        self.db_conn = db_conn
        self.logger = logger or logging.getLogger(__name__)

    def run(self, iterations: Optional[int] = None) -> None:
        """Run the polling loop.

        Args:
            iterations: When provided, limit the number of polling cycles (for testing).
        """

        self.logger.info("Starting price poller for %d epics", len(self.epics))
        remaining = iterations
        while True:
            try:
                for epic in self.epics:
                    snapshot = self.ig_client.fetch_price(epic)
                    store_price(self.db_conn, snapshot)
                    self.logger.info("Fetched price for %s @ %s", epic, snapshot.timestamp.isoformat())
                if remaining is not None:
                    remaining -= 1
                    if remaining <= 0:
                        break
                time.sleep(self.interval_seconds)
            except KeyboardInterrupt:
                self.logger.info("Received interrupt; stopping poller")
                break
            except AuthenticationError:
                self.logger.error("Authentication failure; stopping poller")
                raise
            except IGClientError as exc:
                self.logger.warning("Transient error: %s", exc)
                time.sleep(self.interval_seconds)
                continue

            if remaining is not None and remaining <= 0:
                break


__all__ = ["PricePoller"]
