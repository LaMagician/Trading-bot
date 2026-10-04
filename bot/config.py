import os

from dotenv import load_dotenv


load_dotenv()

SYMBOL = "BTC/USDT"

TIMEFRAME = "1h"

INITIAL_CAPITAL = 10_000.0

RISK_PER_TRADE = 0.01

STOP_LOSS_PERCENT = 0.02

TAKE_PROFIT_PERCENT = 0.04

EXCHANGE_ID = os.getenv("EXCHANGE_ID", "binance")
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"
TIMEFRAME_SECONDS = int(os.getenv("TIMEFRAME_SECONDS", "3600"))
MAX_MARKETS = int(os.getenv("MAX_MARKETS", "50"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "0.03"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", str(RISK_PER_TRADE)))
STATE_FILE = os.getenv("STATE_FILE", "logs/live_state.json")