from __future__ import annotations

from typing import Iterable, List


def ema(values: Iterable[float], period: int) -> List[float]:
    values = list(values)
    if period <= 0:
        raise ValueError("period must be > 0")
    if len(values) < period:
        raise ValueError("not enough values for EMA")

    multiplier = 2 / (period + 1)
    seed = sum(values[:period]) / period
    result = [seed]
    prev = seed
    for value in values[period:]:
        prev = (value - prev) * multiplier + prev
        result.append(prev)
    return result


def rsi(values: Iterable[float], period: int = 14) -> float:
    closes = list(values)
    if len(closes) <= period:
        raise ValueError("not enough values for RSI")
    gains = []
    losses = []
    for prev, curr in zip(closes[:-1], closes[1:]):
        change = curr - prev
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))
