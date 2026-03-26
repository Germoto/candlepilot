from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import AppConfig


@dataclass(slots=True)
class FilterDecision:
    allowed: bool
    reason: str


class ExecutionFilters:
    def __init__(self, config: AppConfig):
        self.config = config

    def session_allowed(self, candle_time: str | None) -> FilterDecision:
        runtime = self.config.runtime
        if not runtime.session_filter_enabled:
            return FilterDecision(True, "session filter disabled")
        if not candle_time:
            return FilterDecision(False, "missing candle time for session filter")
        dt = datetime.fromisoformat(candle_time.replace("Z", "+00:00"))
        local = dt.astimezone(ZoneInfo(runtime.timezone))
        start_h, start_m = map(int, runtime.session_start.split(":"))
        end_h, end_m = map(int, runtime.session_end.split(":"))
        current_minutes = local.hour * 60 + local.minute
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        if start_minutes <= current_minutes <= end_minutes:
            return FilterDecision(True, f"within session {runtime.session_start}-{runtime.session_end} {runtime.timezone}")
        return FilterDecision(False, f"outside session {runtime.session_start}-{runtime.session_end} {runtime.timezone}")

    def spread_allowed(self, spread_pips: float | None) -> FilterDecision:
        runtime = self.config.runtime
        if not runtime.spread_filter_enabled:
            return FilterDecision(True, "spread filter disabled")
        if spread_pips is None:
            return FilterDecision(False, "spread unavailable")
        if spread_pips <= runtime.max_spread_pips:
            return FilterDecision(True, f"spread {spread_pips:.2f} <= {runtime.max_spread_pips:.2f}")
        return FilterDecision(False, f"spread {spread_pips:.2f} > {runtime.max_spread_pips:.2f}")
