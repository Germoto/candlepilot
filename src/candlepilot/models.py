from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(slots=True)
class Candle:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    complete: bool = True

    @property
    def bullish(self) -> bool:
        return self.close > self.open

    @property
    def bearish(self) -> bool:
        return self.close < self.open


@dataclass(slots=True)
class StrategyDecision:
    signal: Signal
    reason: str
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


@dataclass(slots=True)
class OrderRequest:
    instrument: str
    units: int
    side: Signal
    stop_loss_price: float
    take_profit_price: float


@dataclass(slots=True)
class BotState:
    trade_date: str
    trades_today: int = 0
    consecutive_losses: int = 0

    def reset_for_new_day(self, new_date: str) -> None:
        self.trade_date = new_date
        self.trades_today = 0
        self.consecutive_losses = 0
