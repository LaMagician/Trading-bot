from dataclasses import dataclass

import ccxt


@dataclass
class OrderResult:
	symbol: str
	side: str
	amount: float
	price: float
	order_id: str | None
	live: bool


class BrokerExecutor:
	"""Small CCXT adapter shared by paper and live trading modes."""

	def __init__(self, exchange_id, api_key="", api_secret="", live=False):
		exchange_class = getattr(ccxt, exchange_id, None)
		if exchange_class is None:
			raise ValueError(f"Unsupported CCXT exchange: {exchange_id}")

		self.live = live
		self.exchange = exchange_class(
			{
				"apiKey": api_key,
				"secret": api_secret,
				"enableRateLimit": True,
				"options": {"defaultType": "spot"},
			}
		)

	def load_markets(self):
		return self.exchange.load_markets()

	def preflight(self, timeframe):
		markets = self.load_markets()
		if timeframe not in self.exchange.timeframes:
			raise RuntimeError(
				f"{self.exchange.id} does not support timeframe {timeframe}"
			)
		if self.live:
			self.exchange.check_required_credentials()
			self.exchange.fetch_balance()
		return len(markets)

	def fetch_ohlcv(self, symbol, timeframe, limit=200):
		return self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

	def fetch_quote_balance(self, quote):
		balance = self.exchange.fetch_balance()
		return float(balance.get(quote, {}).get("free", 0.0))

	def amount_for_symbol(self, symbol, amount):
		market = self.exchange.market(symbol)
		minimum = (market.get("limits", {}).get("amount", {}) or {}).get("min")
		amount = float(self.exchange.amount_to_precision(symbol, amount))
		if minimum is not None and amount < minimum:
			raise ValueError(
				f"Calculated amount {amount} is below {symbol} minimum {minimum}"
			)
		return amount

	def market_buy(self, symbol, amount, reference_price):
		amount = self.amount_for_symbol(symbol, amount)
		if amount <= 0:
			raise ValueError(f"Calculated buy amount is too small for {symbol}")
		if not self.live:
			return OrderResult(symbol, "buy", amount, reference_price, None, False)
		order = self.exchange.create_market_buy_order(symbol, amount)
		return OrderResult(
			symbol, "buy", amount, float(order.get("average") or reference_price),
			order.get("id"), True,
		)

	def market_sell(self, symbol, amount, reference_price):
		amount = self.amount_for_symbol(symbol, amount)
		if amount <= 0:
			raise ValueError(f"Calculated sell amount is too small for {symbol}")
		if not self.live:
			return OrderResult(symbol, "sell", amount, reference_price, None, False)
		order = self.exchange.create_market_sell_order(symbol, amount)
		return OrderResult(
			symbol, "sell", amount, float(order.get("average") or reference_price),
			order.get("id"), True,
		)
