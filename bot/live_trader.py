import argparse
import json
import logging
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from bot.config import (
    API_KEY,
    API_SECRET,
    EXCHANGE_ID,
    INITIAL_CAPITAL,
    LIVE_TRADING,
    MAX_DAILY_LOSS,
    MAX_MARKETS,
    MAX_OPEN_POSITIONS,
    RISK_PER_TRADE,
    STATE_FILE,
    TIMEFRAME,
    TIMEFRAME_SECONDS,
)
from bot.execution.executor import BrokerExecutor
from bot.strategy.trend_atr_strategy import TrendATRStrategy


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("trading-bot")


@dataclass
class Position:
    symbol: str
    amount: float
    entry_price: float
    stop_price: float
    target_price: float

    def as_dict(self):
        return {
            "symbol": self.symbol,
            "amount": self.amount,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "target_price": self.target_price,
        }


class LiveTrader:
    def __init__(self):
        if LIVE_TRADING and (not API_KEY or not API_SECRET):
            raise RuntimeError("LIVE_TRADING=true requires API_KEY and API_SECRET")

        self.broker = BrokerExecutor(
            EXCHANGE_ID,
            API_KEY,
            API_SECRET,
            live=LIVE_TRADING,
        )
        self.strategy = TrendATRStrategy(
            fast_period=20,
            slow_period=50,
            atr_period=14,
            adx_period=14,
            adx_threshold=25,
            min_atr_percent=0.003,
        )
        self.positions = {}
        self.session_date = date.today()
        self.starting_balance = None
        self.state_path = Path(STATE_FILE)
        self.load_state()

    def load_state(self):
        if not self.state_path.exists():
            return
        with self.state_path.open() as state_file:
            state = json.load(state_file)
        saved_mode = state.get("mode")
        saved_exchange = state.get("exchange")
        current_mode = "live" if LIVE_TRADING else "paper"
        if LIVE_TRADING and not saved_mode:
            logger.warning("Ignoring legacy state file while starting live mode")
            return
        if saved_mode and saved_mode != current_mode:
            logger.warning(
                "Ignoring %s-mode state while running in %s mode",
                saved_mode,
                current_mode,
            )
            return
        if saved_exchange and saved_exchange != EXCHANGE_ID:
            logger.warning("Ignoring state created for exchange %s", saved_exchange)
            return
        self.positions = {
            symbol: Position(**position)
            for symbol, position in state.get("positions", {}).items()
        }
        self.starting_balance = state.get("starting_balance")
        logger.info("Restored %d position(s) from %s", len(self.positions), self.state_path)

    def save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.state_path.with_suffix(".tmp")
        with temporary_path.open("w") as state_file:
            json.dump(
                {
                    "mode": "live" if LIVE_TRADING else "paper",
                    "exchange": EXCHANGE_ID,
                    "positions": {
                        symbol: position.as_dict()
                        for symbol, position in self.positions.items()
                    },
                    "starting_balance": self.starting_balance,
                },
                state_file,
                indent=2,
            )
        temporary_path.replace(self.state_path)

    def preflight(self):
        market_count = self.broker.preflight(TIMEFRAME)
        logger.info(
            "Preflight passed: %s exchange, %d markets, %s mode",
            EXCHANGE_ID,
            market_count,
            "LIVE" if LIVE_TRADING else "PAPER",
        )

    def market_symbols(self):
        markets = self.broker.load_markets()
        symbols = [
            symbol
            for symbol, market in markets.items()
            if market.get("active", True)
            and market.get("spot", True)
            and market.get("quote") == "USDT"
        ]
        return sorted(symbols)[:MAX_MARKETS]

    def candles(self, symbol):
        rows = self.broker.fetch_ohlcv(symbol, TIMEFRAME, limit=200)
        data = pd.DataFrame(
            rows,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        return self.strategy.generate_signals(data)

    def daily_loss_hit(self):
        if not LIVE_TRADING:
            return False
        if self.starting_balance is None:
            self.starting_balance = self.broker.fetch_quote_balance("USDT")
            self.save_state()
        current_balance = self.broker.fetch_quote_balance("USDT")
        loss = (self.starting_balance - current_balance) / self.starting_balance
        return loss >= MAX_DAILY_LOSS if self.starting_balance else False

    def open_position(self, symbol, row):
        if len(self.positions) >= MAX_OPEN_POSITIONS:
            return
        atr = float(row["atr"])
        price = float(row["close"])
        stop_price = price - 2.0 * atr
        target_price = price + 4.0 * atr
        if atr <= 0 or stop_price <= 0:
            return

        quote_balance = (
            self.broker.fetch_quote_balance("USDT")
            if LIVE_TRADING
            else INITIAL_CAPITAL
        )
        risk_amount = quote_balance * RISK_PER_TRADE
        amount = risk_amount / (price - stop_price)
        order = self.broker.market_buy(symbol, amount, price)
        self.positions[symbol] = Position(
            symbol, order.amount, order.price, stop_price, target_price,
        )
        self.save_state()
        logger.info("%s %s %.8f at %.4f", "LIVE BUY" if LIVE_TRADING else "PAPER BUY", symbol, order.amount, order.price)

    def manage_position(self, symbol, row):
        position = self.positions[symbol]
        high = float(row["high"])
        low = float(row["low"])
        price = position.stop_price if low <= position.stop_price else None
        reason = "STOP_LOSS" if price else None
        if price is None and high >= position.target_price:
            price = position.target_price
            reason = "TAKE_PROFIT"
        if price is None:
            return
        self.broker.market_sell(symbol, position.amount, price)
        del self.positions[symbol]
        self.save_state()
        logger.info("%s %s at %.4f (%s)", "LIVE SELL" if LIVE_TRADING else "PAPER SELL", symbol, price, reason)

    def run_once(self):
        if date.today() != self.session_date:
            self.session_date = date.today()
            self.starting_balance = None
            self.save_state()
        if self.daily_loss_hit():
            logger.warning("Daily loss limit reached; no new trades will be opened")
            return

        for symbol in self.market_symbols():
            try:
                data = self.candles(symbol)
                if len(data) < 3:
                    continue
                row = data.iloc[-2]
                if symbol in self.positions:
                    self.manage_position(symbol, row)
                elif int(row["signal"]) == 1:
                    self.open_position(symbol, row)
            except Exception:
                logger.exception("Failed while processing %s", symbol)

    def run_forever(self):
        self.preflight()
        logger.info("Starting %s mode on %s, scanning up to %d USDT markets", "LIVE" if LIVE_TRADING else "PAPER", EXCHANGE_ID, MAX_MARKETS)
        while True:
            try:
                self.run_once()
            except Exception:
                logger.exception("Scanner cycle failed; retrying")
            time.sleep(TIMEFRAME_SECONDS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the multi-market trading service")
    parser.add_argument("--check", action="store_true", help="Validate exchange configuration and exit")
    parser.add_argument("--once", action="store_true", help="Run one scan cycle and exit")
    arguments = parser.parse_args()
    trader = LiveTrader()
    trader.preflight()
    if arguments.check:
        raise SystemExit(0)
    if arguments.once:
        trader.run_once()
    else:
        trader.run_forever()