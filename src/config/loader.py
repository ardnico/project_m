from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, ValidationError


class Settings(BaseSettings):
    ig_base_url: str = Field(
        default="https://demo-api.ig.com/gateway/deal",
        description="Base URL for IG REST API (demo environment by default).",
    )
    api_key: str = Field(description="IG API key for the target account.")
    username: str = Field(description="IG account username.")
    password: str = Field(description="IG account password.")
    epics: list[str] = Field(
        default_factory=list,
        description="List of market epic identifiers to poll.",
    )
    polling_interval_seconds: int = Field(
        default=2, description="Seconds to wait between price polls."
    )
    db_path: str = Field(default="data/trading.db", description="SQLite database path.")
    log_level: str = Field(default="INFO", description="Logging level (e.g., INFO, DEBUG).")

    model_config = {
        "env_prefix": "IG_",
        "env_file": ".env",
        "case_sensitive": False,
    }


class SettingsLoadError(Exception):
    """Raised when configuration cannot be loaded or validated."""


def _read_config_file(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    suffix = config_path.suffix.lower()
    with config_path.open("r", encoding="utf-8") as file:
        if suffix in {".yaml", ".yml"}:
            return yaml.safe_load(file) or {}
        if suffix == ".toml":
            import tomllib  # Python 3.11+

            return tomllib.load(file)
    raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Load configuration from .env and optional YAML/TOML file.

    Environment variables (prefixed with IG_) override file values.
    """

    load_dotenv(override=False)
    data: Dict[str, Any] = {}

    if config_path:
        file_path = Path(config_path)
        data = _read_config_file(file_path)

    try:
        return Settings(**data)
    except ValidationError as exc:
        raise SettingsLoadError(str(exc)) from exc


__all__ = ["Settings", "SettingsLoadError", "load_settings"]
