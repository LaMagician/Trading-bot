import pandas as pd


class MovingAverageStrategy:

    def __init__(self, fast_period=20, slow_period=50):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, data):

        data = data.copy()

        data["fast_ma"] = (
            data["close"]
            .rolling(self.fast_period)
            .mean()
        )

        data["slow_ma"] = (
            data["close"]
            .rolling(self.slow_period)
            .mean()
        )

        data["signal"] = 0

        data.loc[
            data["fast_ma"] > data["slow_ma"],
            "signal"
        ] = 1

        data.loc[
            data["fast_ma"] < data["slow_ma"],
            "signal"
        ] = -1

        return data