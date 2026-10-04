import numpy as np
import pandas as pd

np.random.seed(42)

rows = 1000

returns = np.random.normal(
    loc=0.0002,
    scale=0.02,
    size=rows
)

price = 50000 * np.exp(
    np.cumsum(returns)
)

data = pd.DataFrame({
    "timestamp": pd.date_range(
        start="2024-01-01",
        periods=rows,
        freq="h"
    ),
    "open": price,
    "high": price * 1.01,
    "low": price * 0.99,
    "close": price,
    "volume": np.random.randint(
        100,
        1000,
        rows
    )
})

data.to_csv(
    "data/test_data.csv",
    index=False
)

print("Generated", len(data), "candles.")