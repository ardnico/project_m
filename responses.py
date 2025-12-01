from __future__ import annotations

from typing import Any, Dict, List, Tuple

import requests

GET = "GET"
POST = "POST"


class RequestsMock:
    def __init__(self) -> None:
        self._registry: List[Tuple[str, str, requests.Response]] = []
        self._previous_registry = None

    def __enter__(self) -> "RequestsMock":
        self._previous_registry = requests._mock_registry
        requests._mock_registry = self._registry
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        requests._mock_registry = self._previous_registry

    def add(self, method: str, url: str, json: Any = None, headers: Dict[str, str] | None = None, status: int = 200) -> None:
        response = requests.Response(status_code=status, _json=json, headers=headers or {})
        self._registry.append((method, url, response))


__all__ = ["RequestsMock", "GET", "POST"]
