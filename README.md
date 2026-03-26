# CandlePilot

CandlePilot is a small, auditable trading bot for **OANDA practice and live accounts**.

It is intentionally built around **deterministic rules**, not marketing fluff:
- EMA 9 / EMA 21 trend filter
- RSI momentum filter
- breakout confirmation on the last closed candle
- risk controls: max daily trades, max consecutive losses, one open trade at a time
- **dry-run**, **demo/practice**, **live**, and **backtesting** workflows
- simple **web interface** for configuration and execution

## Important warning
This project is educational and operational, **not a promise of profitability**.

Before using live money:
1. validate in **dry-run**
2. validate in **OANDA practice**
3. run backtests
4. review logs and fills
5. start with very small size

---

## Features

- **Dry-run mode**: evaluates the strategy and logs hypothetical orders
- **Practice/demo mode**: runs against OANDA practice environment
- **Live mode**: runs against OANDA live environment only when explicitly enabled
- **Backtesting**: simulates historical performance on fetched candles
- **Web UI**: save config, run one cycle, run backtest, inspect last report
- **CLI**: run once, loop continuously, or backtest from terminal
- **State tracking**: JSON state file for daily trade counters
- **Logging**: persistent logs for auditability

---

## Strategy logic

### Buy when all are true
1. EMA 9 > EMA 21
2. RSI > 55
3. the latest closed candle is bullish
4. the latest close breaks the previous candle high

### Sell when all are true
1. EMA 9 < EMA 21
2. RSI < 45
3. the latest closed candle is bearish
4. the latest close breaks the previous candle low

### Risk controls
- max 5 trades per day
- stop after 3 consecutive losses
- fixed stop loss in pips
- fixed take profit in pips
- only one open trade per instrument at a time

---

## Project structure

```text
src/candlepilot/
  cli.py            # CLI entrypoint
  web.py            # Flask web UI
  engine.py         # trading engine
  oanda.py          # OANDA REST client
  backtest.py       # historical simulation
  strategy.py       # candle strategy
  indicators.py     # EMA / RSI
  risk.py           # trade limits and sizing
  config.py         # YAML config models
  models.py         # dataclasses
  logging_utils.py  # file/stdout logging
config.example.yaml
PROJECT.md
tests/
```

---

## Requirements

- Python **3.11+** recommended
- An **OANDA account**
  - practice account for demo testing
  - live account only if you truly want to trade live
- OANDA API token
- Git

---

## Step-by-step setup

### 1. Clone the repository
```bash
git clone https://github.com/Germoto/candlepilot.git
cd candlepilot
```

### 2. Create a virtual environment

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -e .[dev]
```

### 4. Create your config file
```bash
cp config.example.yaml config.yaml
```

### 5. Edit `config.yaml`

#### For dry-run
```yaml
mode: dry_run
broker:
  provider: oanda
  account_id: "YOUR_PRACTICE_ACCOUNT_ID"
  api_token: "YOUR_PRACTICE_API_TOKEN"
  environment: practice
strategy:
  instrument: EUR_USD
  granularity: M5
  candle_count: 250
  ema_fast: 9
  ema_slow: 21
  rsi_period: 14
  rsi_buy_threshold: 55
  rsi_sell_threshold: 45
risk:
  risk_per_trade_pct: 1.0
  stop_loss_pips: 10
  take_profit_pips: 15
  pip_value: 0.0001
  max_daily_trades: 5
  max_consecutive_losses: 3
  units: 1000
runtime:
  state_dir: state
  log_dir: logs
  timezone: UTC
  allow_live_orders: false
```

#### For OANDA practice/demo execution
```yaml
mode: live
broker:
  provider: oanda
  account_id: "YOUR_PRACTICE_ACCOUNT_ID"
  api_token: "YOUR_PRACTICE_API_TOKEN"
  environment: practice
runtime:
  state_dir: state
  log_dir: logs
  timezone: UTC
  allow_live_orders: true
```

#### For real money / live account
Use this **only after testing**:
```yaml
mode: live
broker:
  provider: oanda
  account_id: "YOUR_LIVE_ACCOUNT_ID"
  api_token: "YOUR_LIVE_API_TOKEN"
  environment: live
runtime:
  state_dir: state
  log_dir: logs
  timezone: UTC
  allow_live_orders: true
```

**Live orders only happen when both are true:**
- `mode: live`
- `allow_live_orders: true`

If either is not true, the bot should behave as non-live.

---

## How to run

### A. Run one dry-run cycle
```bash
candlepilot run --config config.yaml --once
```

### B. Run continuously
```bash
candlepilot run --config config.yaml --poll-seconds 15
```

### C. Run a backtest from terminal
```bash
candlepilot backtest --config config.yaml
```

### D. Run the web interface
```bash
candlepilot web --host 127.0.0.1 --port 8501
```
Then open:
```text
http://127.0.0.1:8501
```

---

## Web interface usage

The web app lets you:
- enter account ID and API token
- choose **practice** or **live** environment
- choose **dry_run** or **live** mode
- save configuration
- run one trading cycle
- run a backtest
- inspect the latest backtest report

### Recommended usage flow
1. open the web app
2. load practice credentials
3. keep `mode = dry_run`
4. click **Guardar configuración**
5. click **Ejecutar 1 ciclo**
6. review `logs/candlepilot.log`
7. click **Correr backtest**
8. review the backtest report
9. only later switch to practice+live execution
10. only much later consider live money

---

## Backtesting

Current backtesting flow:
- fetches historical candles from OANDA
- scans candle by candle
- opens trades on the next candle open after a signal
- exits on stop loss or take profit
- reports total trades, wins, losses, win rate, and net pips

### Backtesting caveats
This is a useful MVP, but it still does **not** model everything perfectly:
- slippage
- spread changes
- commissions/financing
- news spikes
- partial fills
- latency

So: treat backtests as **screening**, not proof.

---

## Logs and state

### Logs
- `logs/candlepilot.log`

### State
- `state/bot_state.json`
- `state/last_backtest.json`

---

## Tests

Run tests with:
```bash
pytest -q
```

---

## Safety checklist

Before real money:
- [ ] strategy validated in dry-run
- [ ] strategy validated in OANDA practice
- [ ] backtests reviewed
- [ ] small size selected
- [ ] logs monitored
- [ ] API token stored safely
- [ ] no withdrawal permissions exposed

---

## Roadmap

Near-term improvements:
- session/time filters
- spread filter
- ATR-based stops
- CSV import backtesting
- broker abstraction for more providers
- dashboard charts
- notifications

---

## Detailed design
See [PROJECT.md](PROJECT.md).
