import sys
import pandas as pd
import matplotlib.pyplot as plt

from bot.strategy.strategy import MovingAverageStrategy
from bot.backtest.engine import BacktestEngine
from bot.config import (
    INITIAL_CAPITAL,
    RISK_PER_TRADE,
    STOP_LOSS_PERCENT,
    TAKE_PROFIT_PERCENT,
)


def calculate_drawdown(equity):

    equity = pd.Series(equity)

    running_peak = equity.cummax()

    drawdown = (
        equity - running_peak
    ) / running_peak

    return drawdown * 100


def calculate_max_drawdown(equity):

    drawdown = calculate_drawdown(equity)

    return drawdown.min()


def calculate_max_drawdown_duration(equity):

    equity = pd.Series(equity)

    running_peak = equity.cummax()

    underwater = equity < running_peak

    max_duration = 0
    current_duration = 0

    for value in underwater:

        if value:
            current_duration += 1
            max_duration = max(
                max_duration,
                current_duration
            )
        else:
            current_duration = 0

    return max_duration


def calculate_sharpe_ratio(equity):

    equity = pd.Series(equity)

    returns = equity.pct_change().dropna()

    if len(returns) < 2:
        return 0.0

    volatility = returns.std()

    if volatility == 0:
        return 0.0

    periods_per_year = 24 * 365

    return (
        returns.mean()
        / volatility
        * (periods_per_year ** 0.5)
    )


def calculate_streaks(trades):

    max_wins = 0
    max_losses = 0

    current_wins = 0
    current_losses = 0

    for trade in trades:

        if trade.net_profit > 0:

            current_wins += 1
            current_losses = 0

            max_wins = max(
                max_wins,
                current_wins
            )

        else:

            current_losses += 1
            current_wins = 0

            max_losses = max(
                max_losses,
                current_losses
            )

    return max_wins, max_losses


def print_performance_report(engine):

    starting_capital = engine.initial_capital
    ending_capital = engine.capital

    trades = engine.trades

    if not trades:

        print("No completed trades.")
        return

    total_return = (
        (ending_capital - starting_capital)
        / starting_capital
        * 100
    )

    winning_trades = [
        trade
        for trade in trades
        if trade.net_profit > 0
    ]

    losing_trades = [
        trade
        for trade in trades
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
        for trade in trades
    )

    net_profit = sum(
        trade.net_profit
        for trade in trades
    )

    win_rate = (
        len(winning_trades)
        / len(trades)
        * 100
    )

    average_win = (
        sum(
            trade.net_profit
            for trade in winning_trades
        )
        / len(winning_trades)
        if winning_trades
        else 0
    )

    average_loss = (
        abs(
            sum(
                trade.net_profit
                for trade in losing_trades
            )
        )
        / len(losing_trades)
        if losing_trades
        else 0
    )

    average_trade = (
        net_profit / len(trades)
    )

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else float("inf")
    )

    expectancy = (
        (win_rate / 100) * average_win
        -
        ((100 - win_rate) / 100)
        * average_loss
    )

    equity = [
        point["equity"]
        for point in engine.equity_curve
    ]

    max_drawdown = calculate_max_drawdown(
        equity
    )

    drawdown_duration = (
        calculate_max_drawdown_duration(
            equity
        )
    )

    sharpe = calculate_sharpe_ratio(
        equity
    )

    peak_equity = max(equity)

    largest_winner = max(
        trade.net_profit
        for trade in trades
    )

    largest_loser = min(
        trade.net_profit
        for trade in trades
    )

    max_wins, max_losses = calculate_streaks(
        trades
    )

    print()
    print("=" * 50)
    print("              PERFORMANCE REPORT")
    print("=" * 50)

    print()
    print("--- ACCOUNT ---")

    print(
        f"Starting capital:     "
        f"{starting_capital:,.2f}"
    )

    print(
        f"Ending capital:       "
        f"{ending_capital:,.2f}"
    )

    print(
        f"Net profit:           "
        f"{net_profit:,.2f}"
    )

    print(
        f"Total return:         "
        f"{total_return:.2f}%"
    )

    print(
        f"Peak equity:          "
        f"{peak_equity:,.2f}"
    )

    print()
    print("--- TRADES ---")

    print(
        f"Total trades:         "
        f"{len(trades)}"
    )

    print(
        f"Winning trades:       "
        f"{len(winning_trades)}"
    )

    print(
        f"Losing trades:        "
        f"{len(losing_trades)}"
    )

    print(
        f"Win rate:             "
        f"{win_rate:.2f}%"
    )

    print(
        f"Average trade:        "
        f"{average_trade:.2f}"
    )

    print(
        f"Average winner:       "
        f"{average_win:.2f}"
    )

    print(
        f"Average loser:        "
        f"{average_loss:.2f}"
    )

    print(
        f"Largest winner:       "
        f"{largest_winner:.2f}"
    )

    print(
        f"Largest loser:        "
        f"{largest_loser:.2f}"
    )

    print(
        f"Max winning streak:   "
        f"{max_wins}"
    )

    print(
        f"Max losing streak:    "
        f"{max_losses}"
    )

    print()
    print("--- PROFITABILITY ---")

    print(
        f"Gross profit:         "
        f"{gross_profit:.2f}"
    )

    print(
        f"Gross loss:           "
        f"{gross_loss:.2f}"
    )

    print(
        f"Total fees:           "
        f"{total_fees:.2f}"
    )

    print(
        f"Profit factor:        "
        f"{profit_factor:.2f}"
    )

    print(
        f"Expectancy/trade:     "
        f"{expectancy:.2f}"
    )

    print()
    print("--- RISK ---")

    print(
        f"Maximum drawdown:     "
        f"{max_drawdown:.2f}%"
    )

    print(
        f"Max drawdown duration:"
        f" {drawdown_duration} periods"
    )

    print(
        f"Sharpe ratio:         "
        f"{sharpe:.2f}"
    )

    print()
    print("=" * 50)


def plot_equity_curve(engine):

    equity_data = pd.DataFrame(
        engine.equity_curve
    )

    if equity_data.empty:
        return

    equity_data["timestamp"] = pd.to_datetime(
        equity_data["timestamp"]
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        equity_data["timestamp"],
        equity_data["equity"],
        label="Equity",
    )

    plt.axhline(
        engine.initial_capital,
        linestyle="--",
        label="Starting Capital",
    )

    plt.title(
        "Trading Strategy Equity Curve"
    )

    plt.xlabel("Time")
    plt.ylabel("Account Equity")

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        "logs/equity_curve.png",
        dpi=150,
    )

    plt.show()


def plot_drawdown(engine):

    equity_data = pd.DataFrame(
        engine.equity_curve
    )

    if equity_data.empty:
        return

    equity_data["timestamp"] = pd.to_datetime(
        equity_data["timestamp"]
    )

    equity_data["drawdown"] = calculate_drawdown(
        equity_data["equity"]
    )

    plt.figure(figsize=(12, 5))

    plt.plot(
        equity_data["timestamp"],
        equity_data["drawdown"],
        label="Drawdown",
    )

    plt.axhline(
        0,
        linestyle="--",
    )

    plt.title(
        "Strategy Drawdown"
    )

    plt.xlabel("Time")
    plt.ylabel("Drawdown (%)")

    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        "logs/drawdown.png",
        dpi=150,
    )

    plt.show()


def main():

    data_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "data/test_data.csv"
    )

    print()
    print(f"Loading market data: {data_file}")

    data = pd.read_csv(data_file)

    strategy = MovingAverageStrategy(
        fast_period=20,
        slow_period=50,
    )

    data = strategy.generate_signals(
        data
    )

    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL,
        risk_per_trade=RISK_PER_TRADE,
        stop_loss_percent=STOP_LOSS_PERCENT,
        take_profit_percent=TAKE_PROFIT_PERCENT,
    )

    previous_signal = 0

    for _, row in data.iterrows():

        signal = row["signal"]

        if (
            signal == 1
            and previous_signal != 1
        ):

            engine.open_long(
                row["close"],
                row["timestamp"],
            )

        elif (
            signal == -1
            and previous_signal != -1
        ):

            engine.close_long(
                row["close"],
                row["timestamp"],
                "SIGNAL",
            )

        engine.update(row)

        previous_signal = signal

    if engine.position == "LONG":

        last_row = data.iloc[-1]

        engine.close_position_at_end(
            last_row["close"],
            last_row["timestamp"],
        )

    print_performance_report(engine)

    plot_equity_curve(engine)

    plot_drawdown(engine)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()