"""Backtest execution model utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(slots=True)
class LatencyProfile:
    p50: float
    p95: float
    p99: float


@dataclass(slots=True)
class VolatilityScaledSlippage:
    base: float
    vol_factor: float

    def compute(self, volatility: float) -> float:
        return self.base + volatility * self.vol_factor


@dataclass(slots=True)
class ExecutionModel:
    slippage: VolatilityScaledSlippage
    latency: LatencyProfile
    rejection_rate: Mapping[str, float]

    def effective_price(self, price: float, volatility: float, side: str) -> float:
        slip = self.slippage.compute(volatility)
        return price + (slip if side == "BUY" else -slip)

    def expected_latency(self, quantile: float) -> float:
        if quantile <= 0.5:
            return self.latency.p50
        if quantile <= 0.95:
            return self.latency.p95
        return self.latency.p99


__all__ = ["ExecutionModel", "VolatilityScaledSlippage", "LatencyProfile"]
