from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from .config import AppConfig
from .filters import ExecutionFilters
from .models import BotState, OrderRequest, Signal
from .oanda import OandaClient
from .risk import RiskManager
from .strategy import CandleStrategy

log = logging.getLogger(__name__)


class TradingEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = OandaClient(config.broker)
        self.strategy = CandleStrategy(config)
        self.risk = RiskManager(config)
        self.filters = ExecutionFilters(config)
        self.state_path = Path(config.runtime.state_dir) / "bot_state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self) -> BotState:
        if self.state_path.exists():
            data = json.loads(self.state_path.read_text())
            return BotState(**data)
        return BotState(trade_date=self.risk.today_key())

    def _save_state(self) -> None:
        self.state_path.write_text(json.dumps(self.state.__dict__, indent=2))

    def _record_trade_attempt(self) -> None:
        self.state.trades_today += 1
        self._save_state()

    def run_once(self) -> None:
        self.state = self.risk.ensure_current_day(self.state)
        can_trade, reason = self.risk.can_trade(self.state)
        if not can_trade:
            log.warning("Trading blocked by risk manager: %s", reason)
            return

        if self.client.has_open_trade_for(self.config.strategy.instrument):
            log.info("Open trade already exists for %s; skipping", self.config.strategy.instrument)
            return

        candles = self.client.fetch_candles(
            self.config.strategy.instrument,
            self.config.strategy.granularity,
            self.config.strategy.candle_count,
        )
        latest_closed = [c for c in candles if c.complete]
        latest_time = latest_closed[-1].time if latest_closed else None

        session_decision = self.filters.session_allowed(latest_time)
        if not session_decision.allowed:
            log.info("Session filter blocked trade: %s", session_decision.reason)
            return

        spread_pips = self.client.current_spread_pips(self.config.strategy.instrument, self.config.risk.pip_value)
        spread_decision = self.filters.spread_allowed(spread_pips)
        if not spread_decision.allowed:
            log.info("Spread filter blocked trade: %s", spread_decision.reason)
            return

        decision = self.strategy.evaluate(candles)
        log.info("Decision: %s | %s", decision.signal.value, decision.reason)

        if decision.signal == Signal.HOLD:
            return

        order = OrderRequest(
            instrument=self.config.strategy.instrument,
            units=self.risk.units_for(decision),
            side=decision.signal,
            stop_loss_price=decision.stop_loss_price,
            take_profit_price=decision.take_profit_price,
        )

        if self.config.mode == "dry_run" or not self.config.runtime.allow_live_orders:
            log.info("DRY RUN order: %s", order)
            self._record_trade_attempt()
            return

        response = self.client.place_market_order(order)
        log.info("Order response: %s", response)
        self._record_trade_attempt()

    def run_forever(self, poll_seconds: int = 15) -> None:
        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # pragma: no cover
                log.exception("Engine loop error: %s", exc)
            time.sleep(poll_seconds)
