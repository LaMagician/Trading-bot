from dataclasses import dataclass


@dataclass
class Trade:
    entry_time: object
    exit_time: object
    entry_price: float
    exit_price: float
    quantity: float
    gross_profit: float
    fees: float
    net_profit: float
    reason: str


class BacktestEngine:

    def __init__(
        self,
        initial_capital=10_000.0,
        risk_per_trade=0.01,
        stop_loss_percent=0.02,
        take_profit_percent=0.04,
        fee_rate=0.001,
        slippage_rate=0.0005,
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital

        self.risk_per_trade = risk_per_trade

        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent

        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate

        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.quantity = 0.0

        self.stop_loss = None
        self.take_profit = None

        self.trades = []
        self.equity_curve = []

    def calculate_position_size(
        self,
        price,
        stop_price=None,
    ):

        risk_amount = (
            self.capital *
            self.risk_per_trade
        )

        if stop_price is None:

            stop_distance = (
                price *
                self.stop_loss_percent
            )

        else:

            stop_distance = (
                price -
                stop_price
            )

        if stop_distance <= 0:
            return 0.0

        quantity = (
            risk_amount /
            stop_distance
        )

        return quantity

    def open_long(
        self,
        price,
        timestamp,
        stop_price=None,
        target_price=None,
    ):

        if self.position is not None:
            return

        # Simulate buying slightly above
        # the market price.
        execution_price = (
            price *
            (1 + self.slippage_rate)
        )

        # ATR-based strategy can provide
        # explicit stop and target levels.
        if stop_price is not None:

            stop_price = min(
                stop_price,
                execution_price
            )

        if target_price is not None:

            target_price = max(
                target_price,
                execution_price
            )

        quantity = (
            self.calculate_position_size(
                execution_price,
                stop_price,
            )
        )

        if quantity <= 0:
            return

        self.position = "LONG"

        self.entry_price = (
            execution_price
        )

        self.entry_time = timestamp

        self.quantity = quantity

        # Use strategy-provided levels
        # when available.
        if stop_price is not None:

            self.stop_loss = stop_price

        else:

            self.stop_loss = (
                self.entry_price *
                (1 - self.stop_loss_percent)
            )

        if target_price is not None:

            self.take_profit = (
                target_price
            )

        else:

            self.take_profit = (
                self.entry_price *
                (1 + self.take_profit_percent)
            )

    def close_long(
        self,
        price,
        timestamp,
        reason,
    ):

        if self.position != "LONG":
            return

        # Simulate selling slightly below
        # market price.
        execution_price = (
            price *
            (1 - self.slippage_rate)
        )

        position_value_entry = (
            self.entry_price *
            self.quantity
        )

        position_value_exit = (
            execution_price *
            self.quantity
        )

        gross_profit = (
            position_value_exit -
            position_value_entry
        )

        entry_fee = (
            position_value_entry *
            self.fee_rate
        )

        exit_fee = (
            position_value_exit *
            self.fee_rate
        )

        fees = (
            entry_fee +
            exit_fee
        )

        net_profit = (
            gross_profit -
            fees
        )

        self.capital += net_profit

        trade = Trade(
            entry_time=self.entry_time,
            exit_time=timestamp,
            entry_price=self.entry_price,
            exit_price=execution_price,
            quantity=self.quantity,
            gross_profit=gross_profit,
            fees=fees,
            net_profit=net_profit,
            reason=reason,
        )

        self.trades.append(trade)

        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.quantity = 0.0
        self.stop_loss = None
        self.take_profit = None

    def update(self, candle):

        timestamp = candle["timestamp"]

        close = candle["close"]
        high = candle["high"]
        low = candle["low"]

        if self.position == "LONG":

            # Stop loss gets priority if both
            # levels are touched during the
            # same candle.
            if low <= self.stop_loss:

                self.close_long(
                    self.stop_loss,
                    timestamp,
                    "STOP_LOSS",
                )

            elif high >= self.take_profit:

                self.close_long(
                    self.take_profit,
                    timestamp,
                    "TAKE_PROFIT",
                )

        self.equity_curve.append(
            {
                "timestamp": timestamp,
                "equity": self.get_equity(
                    close
                ),
            }
        )

    def get_equity(self, current_price):

        if self.position == "LONG":

            unrealized = (
                current_price -
                self.entry_price
            ) * self.quantity

            return (
                self.capital +
                unrealized
            )

        return self.capital

    def close_position_at_end(
        self,
        price,
        timestamp,
    ):

        if self.position == "LONG":

            self.close_long(
                price,
                timestamp,
                "END_OF_BACKTEST",
            )