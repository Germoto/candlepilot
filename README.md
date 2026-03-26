# CandlePilot

CandlePilot is a small, auditable trading bot MVP for OANDA practice/live accounts.

It uses a deterministic candle strategy:
- trend filter with EMA 9 / EMA 21
- momentum filter with RSI
- breakout confirmation on the most recently closed candle
- hard risk controls: max daily trades, max consecutive losses, one open position at a time

## What this is
- a developer-friendly starter project
- paper/dry-run first
- built for traceability, not hype

## What this is not
- not a promise of profitability
- not financial advice
- not a high-frequency bot
- not a black-box "AI trader"

## Strategy summary
Long only when all conditions are true:
1. EMA 9 > EMA 21
2. RSI > buy threshold
3. latest candle closes bullish
4. latest close breaks previous candle high

Short only when all conditions are true:
1. EMA 9 < EMA 21
2. RSI < sell threshold
3. latest candle closes bearish
4. latest close breaks previous candle low

Default protections:
- one position at a time
- max 5 trades/day
- stop after 3 consecutive losses
- fixed SL/TP distances in pips
- dry-run mode enabled by default in sample config

## Project structure
```text
src/candlepilot/
  cli.py            # command entrypoint
  config.py         # config loading and validation
  models.py         # candle/signal/order dataclasses
  indicators.py     # EMA/RSI helpers
  strategy.py       # trading rules
  risk.py           # daily limits and position sizing
  oanda.py          # minimal OANDA REST client
  engine.py         # orchestration loop
  logging_utils.py  # log setup
config.example.yaml # starter configuration
tests/              # core unit tests
```

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your OANDA practice credentials.

## Run in dry-run mode
```bash
candlepilot run --config config.yaml --once
```

## Run continuously
```bash
candlepilot run --config config.yaml --poll-seconds 15
```

## Safety notes
- Start with an OANDA **practice** account.
- Use API tokens, not scraped web logins.
- Give the bot no withdrawal capability.
- Validate spreads, slippage, and order fills before any live deployment.
- Review logs after every session.

## Detailed design
See [PROJECT.md](PROJECT.md).
