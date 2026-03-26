from __future__ import annotations

import argparse

from .config import load_config
from .engine import TradingEngine
from .logging_utils import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser(description="CandlePilot trading bot")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run the trading bot")
    run_parser.add_argument("--config", required=True, help="Path to YAML config")
    run_parser.add_argument("--once", action="store_true", help="Run exactly one evaluation cycle")
    run_parser.add_argument("--poll-seconds", type=int, default=15, help="Polling interval in seconds")

    args = parser.parse_args()
    if args.command == "run":
        config = load_config(args.config)
        setup_logging(config.runtime.log_dir)
        engine = TradingEngine(config)
        if args.once:
            engine.run_once()
        else:
            engine.run_forever(args.poll_seconds)


if __name__ == "__main__":
    main()
