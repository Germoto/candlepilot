from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .config import AppConfig
from .models import Candle, Signal
from .strategy import CandleStrategy


@dataclass(slots=True)
class BacktestTrade:
    entry_time: str
    exit_time: str
    side: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    result_pips: float
    result_units: float
    reason: str


@dataclass(slots=True)
class BacktestReport:
    trades: list[BacktestTrade]
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    net_pips: float
    avg_pips: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "trades": [asdict(t) for t in self.trades],
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.win_rate,
            "net_pips": self.net_pips,
            "avg_pips": self.avg_pips,
        }


class Backtester:
    def __init__(self, config: AppConfig):
        self.config = config
        self.strategy = CandleStrategy(config)
        self.pip = config.risk.pip_value

    def run(self, candles: list[Candle]) -> BacktestReport:
        trades: list[BacktestTrade] = []
        i = max(self.config.strategy.ema_slow + 5, self.config.strategy.rsi_period + 2)

        while i < len(candles) - 1:
            window = candles[: i + 1]
            decision = self.strategy.evaluate(window)
            if decision.signal == Signal.HOLD:
                i += 1
                continue

            entry_candle = candles[i]
            next_index = i + 1
            if next_index >= len(candles):
                break
            entry_price = candles[next_index].open
            stop = decision.stop_loss_price
            take = decision.take_profit_price
            side = decision.signal.value

            exit_price = entry_price
            exit_time = candles[next_index].time
            exit_reason = "end_of_data"

            for j in range(next_index, len(candles)):
                c = candles[j]
                if decision.signal == Signal.BUY:
                    if c.low <= stop:
                        exit_price = stop
                        exit_time = c.time
                        exit_reason = "stop_loss"
                        break
                    if c.high >= take:
                        exit_price = take
                        exit_time = c.time
                        exit_reason = "take_profit"
                        break
                elif decision.signal == Signal.SELL:
                    if c.high >= stop:
                        exit_price = stop
                        exit_time = c.time
                        exit_reason = "stop_loss"
                        break
                    if c.low <= take:
                        exit_price = take
                        exit_time = c.time
                        exit_reason = "take_profit"
                        break

            if decision.signal == Signal.BUY:
                result_pips = (exit_price - entry_price) / self.pip
            else:
                result_pips = (entry_price - exit_price) / self.pip
            result_units = result_pips * self.config.risk.units * self.pip

            trades.append(
                BacktestTrade(
                    entry_time=candles[next_index].time,
                    exit_time=exit_time,
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    stop_loss=stop,
                    take_profit=take,
                    result_pips=result_pips,
                    result_units=result_units,
                    reason=exit_reason,
                )
            )
            i = max(next_index + 1, j + 1)

        wins = sum(1 for t in trades if t.result_pips > 0)
        losses = sum(1 for t in trades if t.result_pips <= 0)
        total = len(trades)
        net_pips = sum(t.result_pips for t in trades)
        avg_pips = net_pips / total if total else 0.0
        win_rate = (wins / total * 100) if total else 0.0
        return BacktestReport(trades, total, wins, losses, win_rate, net_pips, avg_pips)
