from candlepilot.config import AppConfig, BrokerConfig, RiskConfig, RuntimeConfig, StrategyConfig
from candlepilot.filters import ExecutionFilters


def make_config() -> AppConfig:
    return AppConfig(
        mode="dry_run",
        broker=BrokerConfig(account_id="x", api_token="token"),
        strategy=StrategyConfig(),
        risk=RiskConfig(),
        runtime=RuntimeConfig(
            timezone="UTC",
            spread_filter_enabled=True,
            max_spread_pips=2.0,
            session_filter_enabled=True,
            session_start="07:00",
            session_end="18:00",
        ),
    )


def test_spread_filter_blocks_high_spread():
    f = ExecutionFilters(make_config())
    decision = f.spread_allowed(3.5)
    assert decision.allowed is False


def test_spread_filter_allows_small_spread():
    f = ExecutionFilters(make_config())
    decision = f.spread_allowed(1.2)
    assert decision.allowed is True


def test_session_filter_blocks_outside_window():
    f = ExecutionFilters(make_config())
    decision = f.session_allowed("2026-03-26T06:00:00Z")
    assert decision.allowed is False


def test_session_filter_allows_inside_window():
    f = ExecutionFilters(make_config())
    decision = f.session_allowed("2026-03-26T10:00:00Z")
    assert decision.allowed is True
