"""Pydantic models that mirror the protobuf definitions."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class TradeSignalModel(BaseModel):
    signal_id: str
    ts: datetime
    strategy_id: str
    symbol: str
    side: OrderSide
    size: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    slippage_tolerance: float = Field(default=0.0, ge=0.0)

    @validator("limit_price")
    def _limit_price_required(cls, value: Optional[float], values: dict[str, object]):
        if values.get("order_type") == OrderType.LIMIT and value is None:
            raise ValueError("limit_price is required for limit orders")
        return value

    def as_proto_dict(self) -> dict[str, object]:
        """Return a proto-compatible dictionary representation."""

        return {
            "signal_id": self.signal_id,
            "ts": self.ts.isoformat(),
            "strategy_id": self.strategy_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "size": float(self.size),
            "order_type": self.order_type.value,
            "limit_price": float(self.limit_price) if self.limit_price is not None else 0.0,
            "slippage_tolerance": float(self.slippage_tolerance),
        }

    def serialize(self) -> bytes:
        """Serialize the model to bytes using JSON as an interim encoding.

        The system is designed around protobuf messages but JSON is retained
        here to avoid the requirement for code generation during early
        development.  The executor implements protobuf decoding ensuring the
        contract remains stable once proto generation is wired into CI.
        """

        from json import dumps

        return dumps(self.as_proto_dict(), separators=(",", ":"), sort_keys=True).encode("utf-8")


__all__ = ["TradeSignalModel", "OrderSide", "OrderType"]
