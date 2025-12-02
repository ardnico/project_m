from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.config.loader import Settings, load_settings


def test_load_settings_from_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
api_key: key123
username: user
password: pass
log_level: DEBUG
epics:
  - EPIC1
polling_interval_seconds: 5
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("IG_API_KEY", "env_key")
    settings = load_settings(str(config_path))
    assert settings.api_key == "env_key"  # env overrides file
    assert settings.username == "user"
    assert settings.polling_interval_seconds == 5
    assert settings.epics == ["EPIC1"]


def test_load_settings_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IG_API_KEY", raising=False)
    with pytest.raises(Exception):
        load_settings()


def test_load_settings_allows_demo_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "demo.yaml"
    config_path.write_text("epics: [EPIC1]\ndemo_mode: true\ndemo_starting_balance: 5000", encoding="utf-8")
    settings = load_settings(str(config_path))
    assert settings.demo_mode is True
    assert settings.demo_starting_balance == 5000.0
    assert settings.api_key == ""


def test_load_settings_cli_override_enables_demo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = tmp_path / "demo.yaml"
    config_path.write_text("epics: [EPIC1]", encoding="utf-8")
    settings = load_settings(str(config_path), cli_overrides={"demo_mode": True})
    assert settings.demo_mode is True
