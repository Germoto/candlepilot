# CandlePilot Project Documentation

## Goal
Build an auditable MVP trading bot that can evaluate a simple candle strategy and, if explicitly allowed, place OANDA orders.

## Core principles
1. Deterministic rules before any ML/AI.
2. Dry-run by default.
3. Single strategy, single instrument, single open position.
4. Strong operational visibility through logs and state files.
5. Small, testable modules.

## Runtime flow
1. Load YAML config.
2. Pull recent candles from OANDA.
3. Skip if there is already an open position.
4. Skip if risk limits are hit.
5. Compute EMA/RSI on closed candles.
6. Build a signal: BUY / SELL / HOLD.
7. In dry-run, log hypothetical order.
8. In live mode, submit a market order with attached stop-loss / take-profit.
9. Persist state such as trade counters and consecutive losses.

## Current implementation scope
- OANDA REST integration for candles, open trades, and market orders.
- Deterministic candle strategy.
- State persistence in JSON.
- CLI runner.
- Unit tests for indicators/strategy/risk.

## Not included yet
- News filter
- Broker websocket streaming
- advanced position sizing by ATR
- portfolio/multi-asset support
- dashboard UI
- cloud deployment manifests

## Suggested roadmap
1. Validate in OANDA practice for 2-4 weeks.
2. Add spread filter and trading session windows.
3. Add backtesting module.
4. Add notifications (Slack/Telegram/email).
5. Add optional paper broker abstraction for easier simulation.
