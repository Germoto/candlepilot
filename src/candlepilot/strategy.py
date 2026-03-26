from __future__ import annotations

from .config import AppConfig
from .indicators import ema, rsi
from .models import Candle, Signal, StrategyDecision


class CandleStrategy:
    def __init__(self, config: AppConfig):
        self.config = config

    def evaluate(self, candles: list[Candle]) -> StrategyDecision:
        if len(candles) < max(self.config.strategy.ema_slow + 5, self.config.strategy.rsi_period + 2):
            return StrategyDecision(Signal.HOLD, "Not enough candles")

        closed = [c for c in candles if c.complete]
        if len(closed) < 3:
            return StrategyDecision(Signal.HOLD, "Not enough closed candles")

        latest = closed[-1]
        previous = closed[-2]
        closes = [c.close for c in closed]

        ema_fast = ema(closes, self.config.strategy.ema_fast)[-1]
        ema_slow = ema(closes, self.config.strategy.ema_slow)[-1]
        momentum = rsi(closes, self.config.strategy.rsi_period)
        pip = self.config.risk.pip_value

        if (
            ema_fast > ema_slow
            and momentum > self.config.strategy.rsi_buy_threshold
            and latest.bullish
            and latest.close > previous.high
        ):
            return StrategyDecision(
                signal=Signal.BUY,
                reason=f"BUY: trend up, RSI {momentum:.2f}, bullish breakout",
                stop_loss_price=latest.close - (self.config.risk.stop_loss_pips * pip),
                take_profit_price=latest.close + (self.config.risk.take_profit_pips * pip),
            )

        if (
            ema_fast < ema_slow
            and momentum < self.config.strategy.rsi_sell_threshold
            and latest.bearish
            and latest.close < previous.low
        ):
            return StrategyDecision(
                signal=Signal.SELL,
                reason=f"SELL: trend down, RSI {momentum:.2f}, bearish breakout",
                stop_loss_price=latest.close + (self.config.risk.stop_loss_pips * pip),
                take_profit_price=latest.close - (self.config.risk.take_profit_pips * pip),
            )

        return StrategyDecision(Signal.HOLD, f"No setup: EMA fast/slow or RSI filter not aligned")
