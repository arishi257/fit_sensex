from __future__ import annotations

import threading
from collections.abc import Mapping

from kiteconnect import KiteTicker

from fit_sensex.market.instruments import OptionChain, TokenMap
from fit_sensex.models import LatestQuote


class MarketDataStore:
    def __init__(self, chain: OptionChain, token_to_strike: TokenMap) -> None:
        self.chain = chain
        self.token_to_strike = token_to_strike
        self.latest_values: dict[int, LatestQuote] = {}
        self._lock = threading.Lock()

    def update_tick(self, tick: Mapping) -> None:
        token = tick["instrument_token"]
        if token not in self.token_to_strike:
            return

        strike, option_type = self.token_to_strike[token]
        depth = tick.get("depth")
        if not depth:
            return

        buy = depth.get("buy")
        sell = depth.get("sell")
        if not buy or not sell:
            return

        try:
            best_bid = buy[0]["price"]
            best_ask = sell[0]["price"]
        except (IndexError, KeyError, TypeError):
            return

        option_data = self.chain[strike].ce if option_type == "CE" else self.chain[strike].pe
        if option_data is None:
            return

        with self._lock:
            option_data.bid = best_bid
            option_data.ask = best_ask

            ce = self.chain[strike].ce
            pe = self.chain[strike].pe
            if ce is None or pe is None:
                return
            if None in (ce.bid, ce.ask, pe.bid, pe.ask):
                return

            self.latest_values[strike] = LatestQuote(
                ce_bid=float(ce.bid),
                ce_ask=float(ce.ask),
                pe_bid=float(pe.bid),
                pe_ask=float(pe.ask),
            )

    def snapshot(self) -> dict[int, LatestQuote]:
        with self._lock:
            return dict(self.latest_values)


class KiteMarketStream:
    def __init__(
        self,
        api_key: str,
        access_token: str,
        tokens: list[int],
        store: MarketDataStore,
    ) -> None:
        self.tokens = tokens
        self.store = store
        self.kws = KiteTicker(api_key, access_token)
        self.kws.on_connect = self.on_connect
        self.kws.on_ticks = self.on_ticks
        self.kws.on_error = self.on_error
        self.kws.on_close = self.on_close

    def on_connect(self, ws, response) -> None:
        print(f"Connected. Subscribing to {len(self.tokens)} tokens")
        ws.subscribe(self.tokens)
        ws.set_mode(ws.MODE_FULL, self.tokens)

    def on_ticks(self, ws, ticks) -> None:
        for tick in ticks:
            self.store.update_tick(tick)

    @staticmethod
    def on_error(ws, code, reason) -> None:
        print("WebSocket Error:", reason)

    @staticmethod
    def on_close(ws, code, reason) -> None:
        print("WebSocket Closed:", reason)

    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.kws.connect, daemon=True)
        thread.start()
        return thread
