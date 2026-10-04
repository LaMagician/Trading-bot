from pathlib import Path

import pandas as pd


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "btc_usdt_1h.csv"
)


def validate_data():

    print()
    print("=" * 60)
    print("             MARKET DATA VALIDATION")
    print("=" * 60)

    data = pd.read_csv(DATA_FILE)

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    print()
    print("--- BASIC INFORMATION ---")

    print(f"Rows:       {len(data):,}")
    print(f"Columns:    {len(data.columns)}")

    print(
        f"Start:      "
        f"{data['timestamp'].min()}"
    )

    print(
        f"End:        "
        f"{data['timestamp'].max()}"
    )

    print()
    print("--- MISSING VALUES ---")

    missing = data.isnull().sum()

    print(missing)

    print()
    print("--- DUPLICATES ---")

    duplicates = data["timestamp"].duplicated().sum()

    print(
        f"Duplicate timestamps: "
        f"{duplicates}"
    )

    print()
    print("--- OHLC VALIDATION ---")

    invalid_ohlc = (
        (data["high"] < data["low"])
        |
        (data["high"] < data["open"])
        |
        (data["high"] < data["close"])
        |
        (data["low"] > data["open"])
        |
        (data["low"] > data["close"])
    )

    print(
        f"Invalid OHLC rows: "
        f"{invalid_ohlc.sum()}"
    )

    print()
    print("--- NEGATIVE / ZERO VALUES ---")

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:

        invalid = (
            data[column] <= 0
        ).sum()

        print(
            f"{column:<10}: "
            f"{invalid}"
        )

    print()
    print("--- TIME GAPS ---")

    timestamps = data["timestamp"].sort_values()

    differences = timestamps.diff()

    expected_interval = pd.Timedelta(
        hours=1
    )

    gaps = differences[
        differences > expected_interval
    ]

    print(
        f"Gaps larger than 1 hour: "
        f"{len(gaps)}"
    )

    if len(gaps) > 0:

        print()
        print("Largest gaps:")

        print(
            gaps.sort_values(
                ascending=False
            ).head(10)
        )

    print()
    print("--- PRICE ---")

    print(
        f"Minimum price: "
        f"{data['low'].min():,.2f}"
    )

    print(
        f"Maximum price: "
        f"{data['high'].max():,.2f}"
    )

    print()
    print("=" * 60)


if __name__ == "__main__":
    validate_data()
