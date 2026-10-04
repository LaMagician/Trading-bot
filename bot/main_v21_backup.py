import sys
from pathlib import Path

import pandas as pd

from bot.strategy.trend_atr_strategy import TrendATRStrategy
from bot.backtest.engine import BacktestEngine

from bot.config import (
    INITIAL_CAPITAL,
    RISK_PER_TRADE,
)


def main():

    data_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "data/splits/development.csv"
    )

    print()
    print(f"Loading market data: {data_file}")

    data = pd.read_csv(data_file)

    strategy = TrendATRStrategy(
        fast_period=20,
        slow_period=50,
        atr_period=14,
        adx_period=14,
        adx_threshold=25,
        stop_atr_multiplier=2.0,
        target_atr_multiplier=4.0,
    )

    data = strategy.generate_signals(data)

    Path("logs").mkdir(
        parents=True,
        exist_ok=True,
    )

    trade_metadata = []

    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL,
        risk_per_trade=RISK_PER_TRADE,
    )

    previous_signal = 0

    for _, row in data.iterrows():

        signal = row["signal"]

        # ----------------------------------------
        # ENTRY
        # ----------------------------------------

        if (
            signal == 1
            and previous_signal != 1
        ):

            atr = row["atr"]

            if pd.isna(atr):

                previous_signal = signal
                continue

            stop_price = (
                row["close"]
                - (
                    atr * 2.0
                )
            )

            target_price = (
                row["close"]
                + (
                    atr * 4.0
                )
            )

            engine.open_long(
                row["close"],
                row["timestamp"],
                stop_price=stop_price,
                target_price=target_price,
            )

            # Save indicator information for
            # this particular entry.
            if engine.position == "LONG":

                trade_metadata.append(
                    {
                        "entry_time": row["timestamp"],
                        "entry_price": engine.entry_price,
                        "atr": row["atr"],
                        "adx": row["adx"],
                        "fast_ema": row["fast_ema"],
                        "slow_ema": row["slow_ema"],
                        "stop_price": engine.stop_loss,
                        "target_price": engine.take_profit,
                        "trade_number": len(trade_metadata) + 1,
                    }
                )

        # ----------------------------------------
        # SIGNAL EXIT
        # ----------------------------------------

        elif (
            signal == 0
            and previous_signal == 1
        ):

            engine.close_long(
                row["close"],
                row["timestamp"],
                "SIGNAL_EXIT",
            )

        # ----------------------------------------
        # STOP LOSS / TAKE PROFIT
        # ----------------------------------------

        engine.update(row)

        previous_signal = signal

    # ----------------------------------------
    # CLOSE OPEN POSITION
    # ----------------------------------------

    if engine.position == "LONG":

        last_row = data.iloc[-1]

        engine.close_position_at_end(
            last_row["close"],
            last_row["timestamp"],
        )

    # ========================================
    # SAVE TRADE DIAGNOSTICS
    # ========================================

    trade_rows = []

    for i, trade in enumerate(engine.trades):

        metadata = (
            trade_metadata[i]
            if i < len(trade_metadata)
            else {}
        )

        entry_time = pd.to_datetime(
            trade.entry_time
        )

        exit_time = pd.to_datetime(
            trade.exit_time
        )

        holding_hours = (
            exit_time - entry_time
        ).total_seconds() / 3600

        trade_rows.append(
            {
                "trade_number": i + 1,

                "entry_time":
                    trade.entry_time,

                "exit_time":
                    trade.exit_time,

                "holding_hours":
                    holding_hours,

                "entry_price":
                    trade.entry_price,

                "exit_price":
                    trade.exit_price,

                "quantity":
                    trade.quantity,

                "gross_profit":
                    trade.gross_profit,

                "fees":
                    trade.fees,

                "net_profit":
                    trade.net_profit,

                "reason":
                    trade.reason,

                "atr":
                    metadata.get("atr"),

                "adx":
                    metadata.get("adx"),

                "fast_ema":
                    metadata.get("fast_ema"),

                "slow_ema":
                    metadata.get("slow_ema"),

                "stop_price":
                    metadata.get("stop_price"),

                "target_price":
                    metadata.get("target_price"),
            }
        )

    trade_dataframe = pd.DataFrame(
        trade_rows
    )

    trade_dataframe.to_csv(
        "logs/v21_trades.csv",
        index=False,
    )

    print()
    print("Trade diagnostics saved to:")
    print("logs/v21_trades.csv")

    # ========================================
    # PERFORMANCE CALCULATIONS
    # ========================================

    winning_trades = [
        trade
        for trade in engine.trades
        if trade.net_profit > 0
    ]

    losing_trades = [
        trade
        for trade in engine.trades
        if trade.net_profit <= 0
    ]

    gross_profit = sum(
        trade.gross_profit
        for trade in winning_trades
        if trade.gross_profit > 0
    )

    gross_loss = abs(
        sum(
            trade.gross_profit
            for trade in losing_trades
            if trade.gross_profit < 0
        )
    )

    total_fees = sum(
        trade.fees
        for trade in engine.trades
    )

    win_rate = (
        len(winning_trades)
        / len(engine.trades)
        * 100
        if engine.trades
        else 0
    )

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else float("inf")
    )

    average_trade = (
        (
            engine.capital
            - engine.initial_capital
        )
        / len(engine.trades)
        if engine.trades
        else 0
    )

    reason_counts = {}

    for trade in engine.trades:

        reason_counts[trade.reason] = (
            reason_counts.get(
                trade.reason,
                0
            ) + 1
        )

    # ========================================
    # SUMMARY
    # ========================================

    print()
    print("=" * 50)
    print("              V2 SUMMARY")
    print("=" * 50)

    print()
    print("=" * 60)
    print("                 V2 DIAGNOSTICS")
    print("=" * 60)

    print()
    print("--- ACCOUNT ---")

    print(
        f"Starting capital:   "
        f"{engine.initial_capital:,.2f}"
    )

    print(
        f"Ending capital:     "
        f"{engine.capital:,.2f}"
    )

    print(
        f"Net profit:         "
        f"{engine.capital - engine.initial_capital:,.2f}"
    )

    print(
        f"Return:             "
        f"{(
            (
                engine.capital
                - engine.initial_capital
            )
            / engine.initial_capital
            * 100
        ):.2f}%"
    )

    print()
    print("--- TRADES ---")

    print(
        f"Total trades:       "
        f"{len(engine.trades)}"
    )

    print(
        f"Winning trades:     "
        f"{len(winning_trades)}"
    )

    print(
        f"Losing trades:      "
        f"{len(losing_trades)}"
    )

    print(
        f"Win rate:           "
        f"{win_rate:.2f}%"
    )

    print(
        f"Average trade:      "
        f"{average_trade:.2f}"
    )

    print()
    print("--- PROFITABILITY ---")

    print(
        f"Gross profit:       "
        f"{gross_profit:,.2f}"
    )

    print(
        f"Gross loss:         "
        f"{gross_loss:,.2f}"
    )

    print(
        f"Total fees:         "
        f"{total_fees:,.2f}"
    )

    print(
        f"Profit factor:      "
        f"{profit_factor:.2f}"
    )

    print()
    print("--- EXIT REASONS ---")

    for reason, count in sorted(
        reason_counts.items()
    ):

        print(
            f"{reason:<20} {count}"
        )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()