from pathlib import Path

import pandas as pd


ROOT = (
    Path(__file__).resolve().parents[2]
)

INPUT_FILE = (
    ROOT
    / "data"
    / "btc_usdt_1h.csv"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "splits"
)


def split_data():

    data = pd.read_csv(INPUT_FILE)

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        utc=True,
    )

    data = data.sort_values(
        "timestamp"
    )

    development = data[
        data["timestamp"]
        < "2024-01-01"
    ]

    validation = data[
        (
            data["timestamp"]
            >= "2024-01-01"
        )
        &
        (
            data["timestamp"]
            < "2026-01-01"
        )
    ]

    test = data[
        data["timestamp"]
        >= "2026-01-01"
    ]

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    development.to_csv(
        OUTPUT_DIR
        / "development.csv",
        index=False,
    )

    validation.to_csv(
        OUTPUT_DIR
        / "validation.csv",
        index=False,
    )

    test.to_csv(
        OUTPUT_DIR
        / "test.csv",
        index=False,
    )

    print()
    print("=" * 60)
    print("              DATASET SPLIT")
    print("=" * 60)

    print()
    print(
        f"Development: "
        f"{len(development):,} candles"
    )

    print(
        f"Validation:  "
        f"{len(validation):,} candles"
    )

    print(
        f"Test:        "
        f"{len(test):,} candles"
    )

    print()
    print("Files created:")

    print(
        OUTPUT_DIR
        / "development.csv"
    )

    print(
        OUTPUT_DIR
        / "validation.csv"
    )

    print(
        OUTPUT_DIR
        / "test.csv"
    )


if __name__ == "__main__":
    split_data()
