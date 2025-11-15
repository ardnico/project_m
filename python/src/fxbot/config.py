"""Application configuration models."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field


class NatsConfig(BaseModel):
    """Configuration for NATS JetStream connectivity."""

    servers: list[str] = Field(default_factory=lambda: ["nats://localhost:4222"])
    stream: str = "signals"
    subject: str = "signal.*"
    durable: str = "signal-worker"
    ordered: bool = True


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    dsn: str = "sqlite+aiosqlite:///./fxbot.db"


class BacktestConfig(BaseModel):
    """Configuration for backtest execution model parameters."""

    execution_model: dict[str, object] = Field(default_factory=dict)


class Settings(BaseModel):
    """Top level settings object for Python components."""

    environment: Literal["live", "paper", "backtest"] = "paper"
    nats: NatsConfig = Field(default_factory=NatsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    @staticmethod
    @lru_cache(1)
    def load(path: Optional[str | Path] = None) -> "Settings":
        """Load settings from a YAML file or return defaults."""

        if path is None:
            return Settings()

        from yaml import safe_load

        with open(path, "r", encoding="utf-8") as fp:
            data = safe_load(fp) or {}
        return Settings(**data)


__all__ = ["Settings", "NatsConfig", "DatabaseConfig", "BacktestConfig"]
