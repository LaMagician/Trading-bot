# Trading Bot

## Run the backtest

From the project directory:

```bash
.venv/bin/python -m bot.main_v2
```

To use another CSV file:

```bash
.venv/bin/python -m bot.main_v2 data/splits/validation.csv
```

Install dependencies into a new environment with:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Results are written to `logs/v22_trades.csv`.

## Run the market scanner

Copy `.env.example` to `.env`, set `EXCHANGE_ID`, and leave `LIVE_TRADING=false` while testing:

```bash
cp .env.example .env
.venv/bin/python -m bot.live_trader
```

Check the exchange connection without scanning or trading:

```bash
.venv/bin/python -m bot.live_trader --check
```

Run exactly one scan cycle:

```bash
.venv/bin/python -m bot.live_trader --once
```

For live orders, create an exchange API key restricted to trading only, set `API_KEY` and `API_SECRET`, and change `LIVE_TRADING=true`. Never enable withdrawals on the key. The scanner uses closed candles, limits open positions, sizes trades by risk, and stops opening trades after the configured daily loss limit. It cannot guarantee profit.
