import time
from pathlib import Path

import ccxt
import pandas as pd


SYMBOL = "BTC/USDT"
TIMEFRAME = "1h"

START_DATE = "2020-01-01T00:00:00Z"

OUTPUT_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "btc_usdt_1h.csv"
)


def download_data():

    exchange = ccxt.binance({
        "enableRateLimit": True,
    })

    exchange.load_markets()

    since = exchange.parse8601(START_DATE)

    timeframe_ms = (
        exchange.parse_timeframe(TIMEFRAME)
        * 1000
    )

    all_candles = []

    print()
    print("================================")
    print("     BTC/USDT DATA DOWNLOAD")
    print("================================")
    print(f"Symbol:     {SYMBOL}")
    print(f"Timeframe:  {TIMEFRAME}")
    print(f"Starting:   {START_DATE}")
    print()

    while True:

        try:

            candles = exchange.fetch_ohlcv(
                SYMBOL,
                TIMEFRAME,
                since=since,
                limit=1000,
            )

            if not candles:
                break

            all_candles.extend(candles)

            first_timestamp = candles[0][0]
            last_timestamp = candles[-1][0]

            print(
                "Fetched "
                f"{len(candles):4d} candles | "
                f"{exchange.iso8601(first_timestamp)} "
                "→ "
                f"{exchange.iso8601(last_timestamp)}"
            )

            next_since = (
                last_timestamp
                + timeframe_ms
            )

            if next_since <= since:
                break

            since = next_since

            # Avoid hammering the API.
            time.sleep(
                exchange.rateLimit / 1000
            )

            if len(candles) < 1000:
                break

        except Exception as error:

            print(
                "Download error:",
                type(error).__name__,
                str(error),
            )

            time.sleep(5)

    if not all_candles:

        raise RuntimeError(
            "No market data was downloaded."
        )

    data = pd.DataFrame(
        all_candles,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ],
    )

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        unit="ms",
        utc=True,
    )

    data = data.drop_duplicates(
        subset="timestamp"
    )

    data = data.sort_values(
        "timestamp"
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("================================")
    print("          DOWNLOAD DONE")
    print("================================")

    print(
        f"Candles:    {len(data):,}"
    )

    print(
        f"First:      {data['timestamp'].iloc[0]}"
    )

    print(
        f"Last:       {data['timestamp'].iloc[-1]}"
    )

    print(
        f"Saved to:   {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    download_data()
