from __future__ import annotations

from datetime import datetime, timezone

from .config import AppConfig
from .models import BotState, StrategyDecision, Signal


class RiskManager:
    def __init__(self, config: AppConfig):
        self.config = config

    def today_key(self) -> str:
        return datetime.now(timezone.utc).date().isoformat()

    def ensure_current_day(self, state: BotState) -> BotState:
        today = self.today_key()
        if state.trade_date != today:
            state.reset_for_new_day(today)
        return state

    def can_trade(self, state: BotState) -> tuple[bool, str]:
        state = self.ensure_current_day(state)
        if state.trades_today >= self.config.risk.max_daily_trades:
            return False, "max daily trades reached"
        if state.consecutive_losses >= self.config.risk.max_consecutive_losses:
            return False, "max consecutive losses reached"
        return True, "ok"

    def units_for(self, decision: StrategyDecision) -> int:
        units = self.config.risk.units
        if decision.signal == Signal.SELL:
            return -abs(units)
        if decision.signal == Signal.BUY:
            return abs(units)
        return 0
