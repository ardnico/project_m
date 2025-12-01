from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


def load_dotenv(path: str | None = None, override: bool = False) -> Dict[str, str]:
    env_path = Path(path or ".env")
    if not env_path.exists():
        return {}
    loaded: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override or key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded


__all__ = ["load_dotenv"]
