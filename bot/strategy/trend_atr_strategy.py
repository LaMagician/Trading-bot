import pandas as pd


class TrendATRStrategy:

    def __init__(
        self,
        fast_period=20,
        slow_period=50,
        atr_period=14,
        adx_period=14,
        adx_threshold=25,
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold

    def calculate_atr(self, data):

        high_low = data["high"] - data["low"]

        high_close = (
            data["high"] - data["close"].shift(1)
        ).abs()

        low_close = (
            data["low"] - data["close"].shift(1)
        ).abs()

        true_range = pd.concat(
            [
                high_low,
                high_close,
                low_close,
            ],
            axis=1,
        ).max(axis=1)

        return true_range.rolling(
            self.atr_period
        ).mean()

    def calculate_adx(self, data):

        high = data["high"]
        low = data["low"]
        close = data["close"]

        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = up_move.where(
            (up_move > down_move) &
            (up_move > 0),
            0.0,
        )

        minus_dm = down_move.where(
            (down_move > up_move) &
            (down_move > 0),
            0.0,
        )

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()

        true_range = pd.concat(
            [tr1, tr2, tr3],
            axis=1,
        ).max(axis=1)

        atr = true_range.rolling(
            self.adx_period
        ).mean()

        plus_di = (
            100
            * plus_dm.rolling(
                self.adx_period
            ).mean()
            / atr
        )

        minus_di = (
            100
            * minus_dm.rolling(
                self.adx_period
            ).mean()
            / atr
        )

        dx = (
            100
            * (plus_di - minus_di).abs()
            / (plus_di + minus_di)
        )

        adx = dx.rolling(
            self.adx_period
        ).mean()

        return adx

    def generate_signals(self, data):

        data = data.copy()

        # --------------------------------
        # EMA TREND
        # --------------------------------

        data["fast_ema"] = (
            data["close"]
            .ewm(
                span=self.fast_period,
                adjust=False,
            )
            .mean()
        )

        data["slow_ema"] = (
            data["close"]
            .ewm(
                span=self.slow_period,
                adjust=False,
            )
            .mean()
        )

        # --------------------------------
        # ATR
        # --------------------------------

        data["atr"] = self.calculate_atr(
            data
        )

        # --------------------------------
        # ADX
        # --------------------------------

        data["adx"] = self.calculate_adx(
            data
        )

        # --------------------------------
        # SIGNAL
        # --------------------------------

        data["signal"] = 0

        long_condition = (
            (data["fast_ema"] > data["slow_ema"])
            &
            (data["close"] > data["fast_ema"])
            &
            (data["adx"] >= self.adx_threshold)
        )

        data.loc[
            long_condition,
            "signal"
        ] = 1

        return data