from candlepilot.config import AppConfig, BrokerConfig, RiskConfig, StrategyConfig
from candlepilot.models import Candle, Signal
from candlepilot.strategy import CandleStrategy


def make_config() -> AppConfig:
    return AppConfig(
        mode="dry_run",
        broker=BrokerConfig(account_id="x", api_token="token"),
        strategy=StrategyConfig(),
        risk=RiskConfig(),
    )


def test_strategy_buy_signal():
    cfg = make_config()
    strategy = CandleStrategy(cfg)
    candles = []
    price = 1.1000
    for i in range(40):
        open_ = price
        close = price + 0.0003
        high = close + 0.0001
        low = open_ - 0.0001
        candles.append(Candle(time=str(i), open=open_, high=high, low=low, close=close, complete=True))
        price = close
    candles[-2] = Candle(time="prev", open=1.1100, high=1.1110, low=1.1095, close=1.1108, complete=True)
    candles[-1] = Candle(time="last", open=1.1109, high=1.1120, low=1.1108, close=1.1115, complete=True)
    decision = strategy.evaluate(candles)
    assert decision.signal == Signal.BUY
