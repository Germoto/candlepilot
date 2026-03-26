from __future__ import annotations

import argparse
import json

from .backtest import Backtester
from .config import load_config
from .engine import TradingEngine
from .logging_utils import setup_logging
from .oanda import OandaClient
from .web import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="CandlePilot trading bot")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run the trading bot")
    run_parser.add_argument("--config", required=True, help="Path to YAML config")
    run_parser.add_argument("--once", action="store_true", help="Run exactly one evaluation cycle")
    run_parser.add_argument("--poll-seconds", type=int, default=15, help="Polling interval in seconds")

    backtest_parser = sub.add_parser("backtest", help="Run a backtest using broker candle data")
    backtest_parser.add_argument("--config", required=True, help="Path to YAML config")

    web_parser = sub.add_parser("web", help="Run the web interface")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8501)
    web_parser.add_argument("--config-store", default="web_config.json")

    args = parser.parse_args()

    if args.command == "run":
        config = load_config(args.config)
        setup_logging(config.runtime.log_dir)
        engine = TradingEngine(config)
        if args.once:
            engine.run_once()
        else:
            engine.run_forever(args.poll_seconds)
    elif args.command == "backtest":
        config = load_config(args.config)
        setup_logging(config.runtime.log_dir)
        client = OandaClient(config.broker)
        candles = client.fetch_candles(
            config.strategy.instrument,
            config.strategy.granularity,
            config.strategy.candle_count,
        )
        report = Backtester(config).run(candles)
        print(json.dumps(report.to_dict(), indent=2))
    elif args.command == "web":
        app = create_app(args.config_store)
        app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
