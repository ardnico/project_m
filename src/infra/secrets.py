from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


def load_env(env_path: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from an optional .env file without overriding existing values."""

    if env_path:
        load_dotenv(dotenv_path=Path(env_path), override=False)
    else:
        load_dotenv(override=False)
    return dict(os.environ)


def redact(value: Optional[str], placeholder: str = "***") -> str:
    if value is None:
        return placeholder
    if len(value) <= 4:
        return placeholder
    return f"{value[:2]}{placeholder}{value[-2:]}"


__all__ = ["load_env", "redact"]
