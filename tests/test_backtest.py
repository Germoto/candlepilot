from candlepilot.backtest import Backtester
from candlepilot.config import AppConfig, BrokerConfig, RiskConfig, StrategyConfig
from candlepilot.models import Candle


def make_config() -> AppConfig:
    return AppConfig(
        mode="dry_run",
        broker=BrokerConfig(account_id="x", api_token="token"),
        strategy=StrategyConfig(),
        risk=RiskConfig(),
    )


def test_backtest_runs_and_returns_report():
    cfg = make_config()
    bt = Backtester(cfg)
    candles = []
    price = 1.1000
    for i in range(60):
        open_ = price
        close = price + 0.0004
        high = close + 0.0002
        low = open_ - 0.0001
        candles.append(Candle(time=str(i), open=open_, high=high, low=low, close=close, complete=True))
        price = close
    report = bt.run(candles)
    assert report.total_trades >= 0
