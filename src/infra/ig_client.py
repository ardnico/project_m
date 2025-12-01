from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

import requests


@dataclass
class PriceSnapshot:
    epic: str
    bid: float
    ask: float
    mid: float
    timestamp: datetime


class IGClientError(Exception):
    """Base class for IG client exceptions."""


class AuthenticationError(IGClientError):
    """Authentication failed (invalid credentials or expired tokens)."""


class TransientAPIError(IGClientError):
    """Temporary API failure; retry may succeed."""


class IGClient:
    def __init__(self, base_url: str, api_key: str, username: str, password: str, logger: Optional[logging.Logger] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logger = logger or logging.getLogger(__name__)
        self.tokens: Dict[str, str] = {}

    def close(self) -> None:
        self.session.close()

    def _handle_response(self, response: requests.Response) -> Dict:
        if response.status_code in {401, 403}:
            raise AuthenticationError(f"Authentication failed with status {response.status_code}")
        if response.status_code >= 500:
            raise TransientAPIError(f"Server error {response.status_code}")
        response.raise_for_status()
        return response.json() or {}

    def login(self) -> Dict[str, str]:
        url = f"{self.base_url}/session"
        headers = {
            "X-IG-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"identifier": self.username, "password": self.password}
        self.logger.debug("Logging in to IG at %s", url)
        response = self.session.post(url, json=payload, headers=headers, timeout=10)
        data = self._handle_response(response)
        cst = response.headers.get("CST", "")
        security = response.headers.get("X-SECURITY-TOKEN", "")
        if not cst or not security:
            raise AuthenticationError("Missing session tokens in response headers")
        self.tokens = {"CST": cst, "X-SECURITY-TOKEN": security}
        self.logger.info("IG login succeeded")
        return self.tokens

    def _auth_headers(self) -> Dict[str, str]:
        if not self.tokens:
            raise AuthenticationError("Not authenticated; call login() first")
        return {
            "X-IG-API-KEY": self.api_key,
            "CST": self.tokens.get("CST", ""),
            "X-SECURITY-TOKEN": self.tokens.get("X-SECURITY-TOKEN", ""),
            "Accept": "application/json",
        }

    def fetch_price(self, epic: str) -> PriceSnapshot:
        url = f"{self.base_url}/prices/{epic}"
        params = {"fields": "BID,ASK", "resolution": "SECOND", "max": 1}
        headers = self._auth_headers()
        self.logger.debug("Fetching price for epic %s", epic)
        response = self.session.get(url, headers=headers, params=params, timeout=10)
        data = self._handle_response(response)
        prices = data.get("prices") or []
        if not prices:
            raise IGClientError("No price data returned")
        latest = prices[0]
        bid = float(latest.get("bid") or latest.get("closePrice", {}).get("bid"))
        ask = float(latest.get("ask") or latest.get("closePrice", {}).get("ask"))
        mid = (bid + ask) / 2
        timestamp_str = latest.get("snapshotTimeUTC") or latest.get("snapshotTime")
        timestamp = datetime.fromisoformat(timestamp_str)
        return PriceSnapshot(epic=epic, bid=bid, ask=ask, mid=mid, timestamp=timestamp)


__all__ = [
    "IGClient",
    "PriceSnapshot",
    "IGClientError",
    "AuthenticationError",
    "TransientAPIError",
]
