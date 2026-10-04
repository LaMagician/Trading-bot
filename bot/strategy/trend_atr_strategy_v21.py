import pandas as pd

from ta.trend import EMAIndicator, ADXIndicator
from ta.volatility import AverageTrueRange


class TrendATRStrategy:

    def __init__(
        self,
        fast_period=20,
        slow_period=50,
        atr_period=14,
        adx_period=14,
        adx_threshold=25,
        stop_atr_multiplier=2.0,
        target_atr_multiplier=4.0,
    ):

        self.fast_period = fast_period
        self.slow_period = slow_period

        self.atr_period = atr_period
        self.adx_period = adx_period

        self.adx_threshold = adx_threshold

        self.stop_atr_multiplier = (
            stop_atr_multiplier
        )

        self.target_atr_multiplier = (
            target_atr_multiplier
        )

    def generate_signals(self, data):

        data = data.copy()

        # -----------------------------
        # EMA TREND
        # -----------------------------

        data["fast_ema"] = (
            EMAIndicator(
                close=data["close"],
                window=self.fast_period,
            )
            .ema_indicator()
        )

        data["slow_ema"] = (
            EMAIndicator(
                close=data["close"],
                window=self.slow_period,
            )
            .ema_indicator()
        )

        # -----------------------------
        # ATR
        # -----------------------------

        data["atr"] = (
            AverageTrueRange(
                high=data["high"],
                low=data["low"],
                close=data["close"],
                window=self.atr_period,
            )
            .average_true_range()
        )

        # -----------------------------
        # ADX
        # -----------------------------

        data["adx"] = (
            ADXIndicator(
                high=data["high"],
                low=data["low"],
                close=data["close"],
                window=self.adx_period,
            )
            .adx()
        )

        # -----------------------------
        # ENTRY
        #
        # Actual EMA crossover.
        # -----------------------------

        bullish_cross = (
            (data["fast_ema"] > data["slow_ema"])
            &
            (
                data["fast_ema"].shift(1)
                <=
                data["slow_ema"].shift(1)
            )
        )

        strong_trend = (
            data["adx"] >
            self.adx_threshold
        )

        price_above_trend = (
            data["close"] >
            data["slow_ema"]
        )

        data["entry_signal"] = (
            bullish_cross
            &
            strong_trend
            &
            price_above_trend
        )

        # -----------------------------
        # EXIT
        #
        # Only exit when EMA trend
        # actually reverses.
        # -----------------------------

        bearish_cross = (
            (data["fast_ema"] < data["slow_ema"])
            &
            (
                data["fast_ema"].shift(1)
                >=
                data["slow_ema"].shift(1)
            )
        )

        data["exit_signal"] = bearish_cross

        # Compatibility signal
        data["signal"] = 0

        data.loc[
            data["entry_signal"],
            "signal"
        ] = 1

        data.loc[
            data["exit_signal"],
            "signal"
        ] = -1

        return data