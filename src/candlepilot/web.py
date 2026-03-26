from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, redirect, render_template_string, request, url_for

from .backtest import Backtester
from .config import AppConfig, BrokerConfig, RiskConfig, RuntimeConfig, StrategyConfig
from .engine import TradingEngine
from .logging_utils import setup_logging
from .oanda import OandaClient

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\">
  <title>CandlePilot</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; max-width: 1100px; }
    form { display:grid; grid-template-columns: repeat(2, minmax(280px, 1fr)); gap: 12px; }
    label { display:flex; flex-direction:column; font-size: 14px; }
    input, select { padding: 8px; }
    .full { grid-column: 1 / -1; }
    .card { border:1px solid #ddd; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; }
    .muted { color:#666; }
    table { border-collapse: collapse; width:100%; }
    th, td { border:1px solid #ddd; padding: 8px; font-size: 13px; }
    .actions { display:flex; gap:12px; flex-wrap: wrap; margin-top: 1rem; }
    button { padding:10px 14px; }
    pre { white-space: pre-wrap; word-break: break-word; }
  </style>
</head>
<body>
  <h1>CandlePilot Web</h1>
  <p class=\"muted\">Configura el bot para demo, real o backtesting. Revisa siempre demo antes de live.</p>
  <div class=\"card\">
    <form method=\"post\" action=\"{{ url_for('save_config') }}\">
      {% for field in fields %}
      <label class=\"{{ 'full' if field.full else '' }}\">{{ field.label }}
        {% if field.type == 'select' %}
          <select name=\"{{ field.name }}\">
            {% for value in field.options %}
              <option value=\"{{ value }}\" {% if form_data.get(field.name) == value %}selected{% endif %}>{{ value }}</option>
            {% endfor %}
          </select>
        {% else %}
          <input type=\"{{ field.type }}\" name=\"{{ field.name }}\" value=\"{{ form_data.get(field.name, '') }}\">
        {% endif %}
      </label>
      {% endfor %}
      <div class=\"full actions\">
        <button type=\"submit\">Guardar configuración</button>
      </div>
    </form>
  </div>

  <div class=\"card\">
    <div class=\"actions\">
      <form method=\"post\" action=\"{{ url_for('run_once') }}\"><button type=\"submit\">Ejecutar 1 ciclo</button></form>
      <form method=\"post\" action=\"{{ url_for('run_backtest') }}\"><button type=\"submit\">Correr backtest</button></form>
    </div>
    {% if message %}<p><strong>{{ message }}</strong></p>{% endif %}
    {% if result %}<pre>{{ result }}</pre>{% endif %}
  </div>

  {% if backtest %}
  <div class=\"card\">
    <h2>Backtest</h2>
    <p>Total trades: {{ backtest.total_trades }} | Wins: {{ backtest.wins }} | Losses: {{ backtest.losses }} | Win rate: {{ '%.2f'|format(backtest.win_rate) }}% | Net pips: {{ '%.2f'|format(backtest.net_pips) }}</p>
    <table>
      <tr><th>Entry</th><th>Exit</th><th>Side</th><th>Entry Price</th><th>Exit Price</th><th>Pips</th><th>Reason</th></tr>
      {% for trade in backtest.trades[:20] %}
      <tr>
        <td>{{ trade.entry_time }}</td><td>{{ trade.exit_time }}</td><td>{{ trade.side }}</td><td>{{ trade.entry_price }}</td><td>{{ trade.exit_price }}</td><td>{{ '%.2f'|format(trade.result_pips) }}</td><td>{{ trade.reason }}</td>
      </tr>
      {% endfor %}
    </table>
  </div>
  {% endif %}
</body>
</html>
"""

FIELDS = [
    {"name": "mode", "label": "Mode", "type": "select", "options": ["dry_run", "live"], "full": False},
    {"name": "environment", "label": "Environment", "type": "select", "options": ["practice", "live"], "full": False},
    {"name": "allow_live_orders", "label": "Allow live orders (true/false)", "type": "text", "full": False},
    {"name": "account_id", "label": "OANDA Account ID", "type": "text", "full": False},
    {"name": "api_token", "label": "OANDA API Token", "type": "password", "full": True},
    {"name": "instrument", "label": "Instrument", "type": "text", "full": False},
    {"name": "granularity", "label": "Granularity", "type": "select", "options": ["M1", "M5", "M15", "H1"], "full": False},
    {"name": "units", "label": "Units", "type": "number", "full": False},
    {"name": "stop_loss_pips", "label": "Stop loss (pips)", "type": "number", "full": False},
    {"name": "take_profit_pips", "label": "Take profit (pips)", "type": "number", "full": False},
    {"name": "max_daily_trades", "label": "Max daily trades", "type": "number", "full": False},
    {"name": "max_consecutive_losses", "label": "Max consecutive losses", "type": "number", "full": False},
    {"name": "candle_count", "label": "Candle count", "type": "number", "full": False},
]


def _build_config(data: dict[str, str]) -> AppConfig:
    return AppConfig(
        mode=data.get("mode", "dry_run"),
        broker=BrokerConfig(
            account_id=data.get("account_id", ""),
            api_token=data.get("api_token", ""),
            environment=data.get("environment", "practice"),
        ),
        strategy=StrategyConfig(
            instrument=data.get("instrument", "EUR_USD"),
            granularity=data.get("granularity", "M5"),
            candle_count=int(data.get("candle_count", 250)),
        ),
        risk=RiskConfig(
            units=int(data.get("units", 1000)),
            stop_loss_pips=float(data.get("stop_loss_pips", 10)),
            take_profit_pips=float(data.get("take_profit_pips", 15)),
            max_daily_trades=int(data.get("max_daily_trades", 5)),
            max_consecutive_losses=int(data.get("max_consecutive_losses", 3)),
        ),
        runtime=RuntimeConfig(allow_live_orders=str(data.get("allow_live_orders", "false")).lower() == "true"),
    )


def create_app(config_path: str = "web_config.json") -> Flask:
    app = Flask(__name__)
    path = Path(config_path)
    setup_logging("logs")

    def load_form_data() -> dict[str, Any]:
        if path.exists():
            return json.loads(path.read_text())
        return {
            "mode": "dry_run",
            "environment": "practice",
            "allow_live_orders": "false",
            "instrument": "EUR_USD",
            "granularity": "M5",
            "units": "1000",
            "stop_loss_pips": "10",
            "take_profit_pips": "15",
            "max_daily_trades": "5",
            "max_consecutive_losses": "3",
            "candle_count": "250",
            "account_id": "",
            "api_token": "",
        }

    @app.get("/")
    def index():
        backtest = None
        backtest_file = Path("state/last_backtest.json")
        if backtest_file.exists():
            backtest = json.loads(backtest_file.read_text())
        return render_template_string(TEMPLATE, fields=FIELDS, form_data=load_form_data(), message=request.args.get("message"), result=request.args.get("result"), backtest=backtest)

    @app.post("/save-config")
    def save_config():
        data = {k: v for k, v in request.form.items()}
        path.write_text(json.dumps(data, indent=2))
        return redirect(url_for("index", message="Configuración guardada"))

    @app.post("/run-once")
    def run_once():
        data = load_form_data()
        cfg = _build_config(data)
        engine = TradingEngine(cfg)
        engine.run_once()
        return redirect(url_for("index", message="Ciclo ejecutado. Revisa logs/candlepilot.log"))

    @app.post("/run-backtest")
    def run_backtest():
        data = load_form_data()
        cfg = _build_config(data)
        client = OandaClient(cfg.broker)
        candles = client.fetch_candles(cfg.strategy.instrument, cfg.strategy.granularity, cfg.strategy.candle_count)
        report = Backtester(cfg).run(candles)
        Path("state").mkdir(exist_ok=True)
        Path("state/last_backtest.json").write_text(json.dumps(report.to_dict(), indent=2))
        return redirect(url_for("index", message="Backtest completado"))

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=8501, debug=False)
