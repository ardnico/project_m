from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


class HTTPError(Exception):
    pass


@dataclass
class Response:
    status_code: int
    _json: Any = None
    headers: Dict[str, str] | None = None

    def json(self) -> Any:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPError(f"HTTP {self.status_code}")


_mock_registry: List[Tuple[str, str, Response]] | None = None


class Session:
    def __init__(self) -> None:
        pass

    def close(self) -> None:
        return None

    def _dispatch(self, method: str, url: str, **kwargs: Any) -> Response:
        global _mock_registry
        if _mock_registry is None:
            raise ConnectionError(f"No mock registered for {method} {url}")
        for idx, (m, u, response) in enumerate(_mock_registry):
            if m == method and u == url:
                return _mock_registry.pop(idx)[2]
        raise ConnectionError(f"No mock registered for {method} {url}")

    def post(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> Response:
        return self._dispatch("POST", url)

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> Response:
        return self._dispatch("GET", url)


__all__ = ["Session", "Response", "HTTPError", "_mock_registry"]
