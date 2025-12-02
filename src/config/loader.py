from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import yaml


class SettingsLoadError(Exception):
    """Raised when configuration cannot be loaded or validated."""


@dataclass
class Settings:
    ig_base_url: str = "https://demo-api.ig.com/gateway/deal"
    api_key: str = ""
    username: str = ""
    password: str = ""
    epics: list[str] = field(default_factory=list)
    polling_interval_seconds: int = 2
    db_path: str = "data/trading.db"
    log_level: str = "INFO"
    demo_mode: bool = False
    demo_starting_balance: float = 100_000.0
    demo_price_seed: Optional[int] = None

    def __post_init__(self) -> None:
        missing = [name for name in ["api_key", "username", "password"] if not getattr(self, name)]
        if missing and not self.demo_mode:
            raise SettingsLoadError(f"Missing required settings: {', '.join(missing)}")
        if not isinstance(self.epics, list):
            raise SettingsLoadError("epics must be a list of strings")


def _coerce_types(data: Dict[str, Any]) -> Dict[str, Any]:
    if "demo_mode" in data:
        value = data["demo_mode"]
        if isinstance(value, str):
            data["demo_mode"] = value.strip().lower() in {"1", "true", "yes", "y", "on"}
        else:
            data["demo_mode"] = bool(value)
    if "polling_interval_seconds" in data:
        try:
            data["polling_interval_seconds"] = int(data["polling_interval_seconds"])
        except (TypeError, ValueError):
            raise SettingsLoadError("polling_interval_seconds must be an integer")
    if "demo_price_seed" in data and data["demo_price_seed"] is not None:
        try:
            data["demo_price_seed"] = int(data["demo_price_seed"])
        except (TypeError, ValueError):
            raise SettingsLoadError("demo_price_seed must be an integer if provided")
    if "demo_starting_balance" in data:
        try:
            data["demo_starting_balance"] = float(data["demo_starting_balance"])
        except (TypeError, ValueError):
            raise SettingsLoadError("demo_starting_balance must be numeric")
    if "epics" in data and isinstance(data["epics"], str):
        data["epics"] = [data["epics"]]
    return data


def _read_config_file(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    suffix = config_path.suffix.lower()
    text = config_path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    if suffix == ".toml":
        import tomllib  # Python 3.11+

        return tomllib.loads(text)
    raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def load_settings(config_path: Optional[str] = None, cli_overrides: Optional[Dict[str, Any]] = None) -> Settings:
    """Load configuration from .env, optional YAML/TOML file, and CLI overrides.

    Environment variables (prefixed with IG_) override file values. CLI overrides
    (e.g., `{"demo_mode": True}`) are merged last.
    """

    load_dotenv(override=False)
    data: Dict[str, Any] = {}

    if config_path:
        file_path = Path(config_path)
        data = _read_config_file(file_path)

    env_overrides = {
        "api_key": os.getenv("IG_API_KEY"),
        "username": os.getenv("IG_USERNAME"),
        "password": os.getenv("IG_PASSWORD"),
        "ig_base_url": os.getenv("IG_BASE_URL"),
        "polling_interval_seconds": os.getenv("IG_POLLING_INTERVAL_SECONDS"),
        "db_path": os.getenv("IG_DB_PATH"),
        "log_level": os.getenv("IG_LOG_LEVEL"),
        "demo_mode": os.getenv("IG_DEMO_MODE"),
        "demo_starting_balance": os.getenv("IG_DEMO_STARTING_BALANCE"),
        "demo_price_seed": os.getenv("IG_DEMO_PRICE_SEED"),
    }
    merged = {**data, **{k: v for k, v in env_overrides.items() if v is not None}}
    if cli_overrides:
        merged.update({k: v for k, v in cli_overrides.items() if v is not None})
    merged = _coerce_types(merged)

    try:
        return Settings(**merged)
    except TypeError as exc:
        raise SettingsLoadError(str(exc)) from exc


__all__ = ["Settings", "SettingsLoadError", "load_settings"]
