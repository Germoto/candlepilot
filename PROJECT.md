# CandlePilot Project Documentation

## Goal
Build a usable, auditable trading bot for candle-based trading with:
- OANDA integration
- dry-run, practice, and live modes
- a basic web interface
- historical backtesting
- strong guardrails around risk and execution

## High-level architecture

### 1. Configuration layer
`config.py`
- loads YAML config
- validates broker, strategy, risk, and runtime settings
- separates environment (`practice` vs `live`) from mode (`dry_run` vs `live`)

### 2. Market access layer
`oanda.py`
- fetch candles
- list open trades
- submit market orders with stop loss / take profit
- chooses API base URL depending on OANDA practice/live environment

### 3. Strategy layer
`strategy.py`
- deterministic candle strategy
- no AI / ML dependency
- returns `BUY`, `SELL`, or `HOLD`
- calculates stop loss and take profit prices at signal time

### 4. Risk layer
`risk.py`
- max trades per day
- max consecutive losses
- trade units sign handling for buy vs sell
- daily state reset

### 5. Execution engine
`engine.py`
- orchestrates config + broker + strategy + risk
- checks for open trades
- fetches candles
- evaluates signal
- logs actions
- submits order or dry-runs it
- persists bot state

### 6. Backtesting engine
`backtest.py`
- reuses the same strategy rules
- simulates entries/exits over historical candles
- reports trade list and summary stats

### 7. Web interface
`web.py`
- Flask-based UI
- stores a simple JSON web config
- supports one-click save, run-once, and backtest
- shows latest backtest summary

## Trading modes

### Dry-run
- safest mode
- calculates signals
- logs hypothetical orders
- does not submit real orders

### Practice/demo
- uses OANDA `practice` environment
- can still place orders if:
  - `mode = live`
  - `allow_live_orders = true`
- recommended first execution environment

### Real/live
- uses OANDA `live` environment
- should only be used after validation
- guarded by explicit config flags

## Runtime flow
1. Load config.
2. Load current bot state from JSON.
3. Check day rollover and reset counters if needed.
4. Check daily trade and loss limits.
5. Check whether the instrument already has an open trade.
6. Fetch recent candles.
7. Evaluate strategy.
8. If HOLD: do nothing.
9. If BUY/SELL:
   - build order request
   - dry-run log it, or
   - place real order if live execution is explicitly enabled.
10. Persist updated state.

## Strategy details

### Indicators
- EMA fast = 9
- EMA slow = 21
- RSI = 14

### Long setup
- EMA fast above EMA slow
- RSI above buy threshold
- bullish latest candle
- latest close above previous high

### Short setup
- EMA fast below EMA slow
- RSI below sell threshold
- bearish latest candle
- latest close below previous low

### Exits
In live trading:
- stop loss attached on fill
- take profit attached on fill

In backtest:
- entry on next candle open
- candle-by-candle scan until SL or TP hit

## Files produced at runtime

### Logs
- `logs/candlepilot.log`

### State
- `state/bot_state.json`
- `state/last_backtest.json`

### Web config
- `web_config.json`

## Security considerations
- prefer environment variables or local secrets storage for API tokens
- never commit real config files with live tokens
- keep dry-run as default
- use practice credentials first
- keep live order enablement explicit and rare

## Known limitations
- backtesting does not yet model spread/slippage dynamically
- no websocket streaming yet
- no session-based filter yet
- no broker-neutral abstraction yet
- no chart visualization yet
- no production deployment unit/service file yet

## Recommended next improvements
1. Add ATR-based dynamic SL/TP.
2. Add CSV import backtesting from local datasets.
3. Add performance charts.
4. Add notification channels.
5. Add Docker deployment.

## v3 implementation notes
- Added `filters.py` for pre-trade spread/session checks.
- Added OANDA pricing query support for live spread estimation.
- Added backtest exporters to JSON and CSV.
- Expanded web UI with guardrail controls and export downloads.
