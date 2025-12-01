from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from src.app.price_poller import PricePoller
from src.config.loader import SettingsLoadError, load_settings
from src.infra.db import init_db, store_session
from src.infra.ig_client import IGClient


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IG price poller")
    parser.add_argument("--config", help="Path to YAML/TOML config file", required=False)
    parser.add_argument("--dry-run", action="store_true", help="Run one login + price fetch and exit")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    try:
        settings = load_settings(args.config)
    except SettingsLoadError as exc:
        print(f"Failed to load settings: {exc}", file=sys.stderr)
        return 1

    configure_logging(settings.log_level)
    logger = logging.getLogger("ig-poller")

    db_conn = init_db(settings.db_path)
    client = IGClient(
        base_url=settings.ig_base_url,
        api_key=settings.api_key,
        username=settings.username,
        password=settings.password,
        logger=logging.getLogger("ig-client"),
    )

    try:
        tokens = client.login()
        store_session(db_conn, tokens)
        poller = PricePoller(
            ig_client=client,
            epics=settings.epics,
            interval_seconds=settings.polling_interval_seconds,
            db_conn=db_conn,
            logger=logging.getLogger("price-poller"),
        )
        if args.dry_run:
            for epic in settings.epics:
                snapshot = client.fetch_price(epic)
                logger.info("Dry run fetched %s: %s", epic, snapshot)
            return 0
        poller.run()
    except Exception:
        logger.exception("Fatal error in main loop")
        return 1
    finally:
        client.close()
        db_conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
