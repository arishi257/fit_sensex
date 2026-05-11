from __future__ import annotations

from dataclasses import replace
import tkinter as tk

from fit_sensex.config import AppConfig
from fit_sensex.market.instruments import load_option_chain_for_expiry, parse_expiry_date
from fit_sensex.market.kite_stream import KiteMarketStream, MarketDataStore
from fit_sensex.services.analytics import AnalyticsEngine
from fit_sensex.services.expiry_calendar import (
    load_full_days_for_expiry,
    load_model_params,
)
from fit_sensex.ui.app import FitSensexApp


def ask_expiry_date():
    while True:
        raw_value = input("Enter SENSEX option expiry date (YYYY-MM-DD): ")
        try:
            return parse_expiry_date(raw_value)
        except ValueError as exc:
            print(exc)


def main() -> None:
    config = AppConfig()
    config.api.validate()
    expiry = ask_expiry_date()
    full_days = load_full_days_for_expiry(config.market.holidays_file, expiry)
    model_params = load_model_params(config.market.holidays_file)
    config = replace(config, market=replace(config.market, full_days=full_days))
    config = replace(
        config,
        model=replace(
            config.model,
            initial_a=model_params["a"],
            initial_bl=model_params["bL"],
            initial_br=model_params["bR"],
            initial_capl=model_params["capL"],
            initial_floorr=model_params["floorR"],
        ),
    )
    print(f"Using full_days={full_days} from {config.market.holidays_file.name}")
    print(
        "Using initial params from params tab: "
        f"a={config.model.initial_a}, "
        f"bL={config.model.initial_bl}, "
        f"bR={config.model.initial_br}, "
        f"capL={config.model.initial_capl}, "
        f"floorR={config.model.initial_floorr}"
    )

    chain, token_to_strike, tokens = load_option_chain_for_expiry(
        config.api,
        config.market,
        config.strikes,
        expiry,
    )
    print(
        f"Loaded {len(chain)} {config.market.symbol_name} strikes "
        f"and {len(tokens)} option tokens for {expiry}"
    )

    store = MarketDataStore(chain, token_to_strike)
    stream = KiteMarketStream(
        config.api.api_key,
        config.api.access_token,
        tokens,
        store,
    )
    stream.start()

    root = tk.Tk()
    analytics = AnalyticsEngine(config.market, config.model)
    app = FitSensexApp(root, config, chain, store, analytics)
    app.start()


if __name__ == "__main__":
    main()
