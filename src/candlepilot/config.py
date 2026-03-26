from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, SecretStr


class BrokerConfig(BaseModel):
    provider: Literal["oanda"] = "oanda"
    account_id: str
    api_token: SecretStr
    environment: Literal["practice", "live"] = "practice"


class StrategyConfig(BaseModel):
    instrument: str = "EUR_USD"
    granularity: str = "M5"
    candle_count: int = 250
    ema_fast: int = 9
    ema_slow: int = 21
    rsi_period: int = 14
    rsi_buy_threshold: float = 55
    rsi_sell_threshold: float = 45


class RiskConfig(BaseModel):
    risk_per_trade_pct: float = Field(default=1.0, gt=0, le=5)
    stop_loss_pips: float = Field(default=10, gt=0)
    take_profit_pips: float = Field(default=15, gt=0)
    pip_value: float = Field(default=0.0001, gt=0)
    max_daily_trades: int = Field(default=5, gt=0)
    max_consecutive_losses: int = Field(default=3, gt=0)
    units: int = Field(default=1000, gt=0)


class RuntimeConfig(BaseModel):
    state_dir: str = "state"
    log_dir: str = "logs"
    timezone: str = "UTC"
    allow_live_orders: bool = False


class AppConfig(BaseModel):
    mode: Literal["dry_run", "live"] = "dry_run"
    broker: BrokerConfig
    strategy: StrategyConfig
    risk: RiskConfig
    runtime: RuntimeConfig = RuntimeConfig()


def load_config(path: str | Path) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text())
    return AppConfig.model_validate(raw)
