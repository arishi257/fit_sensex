# Fit SENSEX

Modular version of the live SENSEX option-chain dashboard.

## Architecture

- `fit_sensex.config` reads environment-driven settings.
- `fit_sensex.pricing.black_scholes` contains pure Black-Scholes and IV helpers.
- `fit_sensex.pricing.vol_curve` owns the parametric slope/volatility fit.
- `fit_sensex.market.instruments` fetches Kite instruments for the selected expiry and builds strike/token maps.
- `fit_sensex.market.kite_stream` handles Kite websocket callbacks and live quote state.
- `fit_sensex.services.analytics` turns quote snapshots into table rows, fitted params, and plot data.
- `fit_sensex.ui.app` renders the Tkinter dashboard.
- `fit_sensex.main` wires everything together.

## Setup

From `C:\Users\rishi\projects\fit_sensex`:

```powershell
..\.venv\Scripts\python.exe -m pip install -e .
```

Set your live credentials before running:

Create `credentials.ini` in this folder:

```ini
[kite]
api_key = your_api_key
access_token = your_access_token
```

Environment variables still work and take priority over `credentials.ini`:

```powershell
$env:KITE_API_KEY="your_api_key"
$env:KITE_ACCESS_TOKEN="your_access_token"
```

Run the app:

```powershell
..\.venv\Scripts\python.exe -m fit_sensex
```

The app asks for an expiry date at startup:

```text
Enter SENSEX option expiry date (YYYY-MM-DD):
```

Accepted formats are `YYYY-MM-DD`, `DD-MM-YYYY`, and `DD/MM/YYYY`.

For the same expiry, the app reads `full_days` from `hols.xlsx` in this folder:

- column A: expiry date
- column C: `full_days`

The app also reads the five initial model parameters from the `params` tab of the same workbook:

- column A: parameter name, using `a`, `bL`, `bR`, `capL`, `floorR`
- column B: starting value

You can point to another workbook with:

```powershell
$env:HOLIDAYS_FILE="C:\Users\rishi\projects\fit_sensex\hols.xlsx"
```

## Notes

The original script is left untouched at:

`C:\Users\rishi\projects\.venv\Scripts\setup_updated_fit_sensex_3.py`

The new project avoids hardcoding live Kite credentials and no longer depends on a local expiry CSV. Runtime parameters can be changed with environment variables listed in `.env.example`.
