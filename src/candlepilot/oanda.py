from __future__ import annotations

import logging
from typing import Any

import requests

from .config import BrokerConfig
from .models import Candle, OrderRequest

log = logging.getLogger(__name__)


class OandaClient:
    def __init__(self, broker: BrokerConfig):
        self.broker = broker
        base = "https://api-fxpractice.oanda.com" if broker.environment == "practice" else "https://api-fxtrade.oanda.com"
        self.base_url = f"{base}/v3"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {broker.api_token.get_secret_value()}",
                "Content-Type": "application/json",
            }
        )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(f"{self.base_url}{path}", json=payload, timeout=20)
        response.raise_for_status()
        return response.json()

    def fetch_candles(self, instrument: str, granularity: str, count: int = 250) -> list[Candle]:
        data = self._get(
            f"/instruments/{instrument}/candles",
            params={"granularity": granularity, "count": count, "price": "M"},
        )
        candles = []
        for item in data.get("candles", []):
            mid = item.get("mid", {})
            candles.append(
                Candle(
                    time=item["time"],
                    open=float(mid["o"]),
                    high=float(mid["h"]),
                    low=float(mid["l"]),
                    close=float(mid["c"]),
                    volume=int(item.get("volume", 0)),
                    complete=bool(item.get("complete", False)),
                )
            )
        return candles

    def list_open_trades(self) -> list[dict[str, Any]]:
        data = self._get(f"/accounts/{self.broker.account_id}/openTrades")
        return data.get("trades", [])

    def has_open_trade_for(self, instrument: str) -> bool:
        return any(t.get("instrument") == instrument for t in self.list_open_trades())

    def get_pricing(self, instrument: str) -> dict[str, Any]:
        data = self._get(f"/accounts/{self.broker.account_id}/pricing", params={"instruments": instrument})
        prices = data.get("prices", [])
        return prices[0] if prices else {}

    def current_spread_pips(self, instrument: str, pip_value: float) -> float | None:
        pricing = self.get_pricing(instrument)
        bids = pricing.get("bids", [])
        asks = pricing.get("asks", [])
        if not bids or not asks:
            return None
        bid = float(bids[0]["price"])
        ask = float(asks[0]["price"])
        return (ask - bid) / pip_value

    def place_market_order(self, order: OrderRequest) -> dict[str, Any]:
        payload = {
            "order": {
                "type": "MARKET",
                "instrument": order.instrument,
                "units": str(order.units),
                "timeInForce": "FOK",
                "positionFill": "DEFAULT",
                "stopLossOnFill": {"price": f"{order.stop_loss_price:.5f}"},
                "takeProfitOnFill": {"price": f"{order.take_profit_price:.5f}"},
            }
        }
        log.info("Submitting market order", extra={"instrument": order.instrument, "units": order.units})
        return self._post(f"/accounts/{self.broker.account_id}/orders", payload)
