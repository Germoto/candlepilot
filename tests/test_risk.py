from candlepilot.config import AppConfig, BrokerConfig, RiskConfig, StrategyConfig
from candlepilot.models import BotState, Signal, StrategyDecision
from candlepilot.risk import RiskManager


def make_config() -> AppConfig:
    return AppConfig(
        mode="dry_run",
        broker=BrokerConfig(account_id="x", api_token="token"),
        strategy=StrategyConfig(),
        risk=RiskConfig(max_daily_trades=5, max_consecutive_losses=3, units=1000),
    )


def test_risk_blocks_after_daily_limit():
    cfg = make_config()
    rm = RiskManager(cfg)
    state = BotState(trade_date=rm.today_key(), trades_today=5, consecutive_losses=0)
    ok, _ = rm.can_trade(state)
    assert ok is False


def test_units_for_sell_are_negative():
    cfg = make_config()
    rm = RiskManager(cfg)
    decision = StrategyDecision(signal=Signal.SELL, reason="x")
    assert rm.units_for(decision) == -1000
