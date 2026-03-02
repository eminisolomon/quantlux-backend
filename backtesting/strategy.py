"""Backtrader Strategy Wrapper."""

import backtrader as bt

from app.utils.logger import logger


class QuantLuxStrategy(bt.Strategy):
    """Backtrader-compatible wrapper for QuantLux RSI strategy."""

    params = (
        ("rsi_period", 14),
        ("rsi_oversold", 30),
        ("rsi_overbought", 70),
        ("stop_loss_pct", 2.0),
        ("take_profit_pct", 4.0),
        ("position_size", 0.01),  # Lot size
    )

    def __init__(self):
        """Initialize strategy with indicators."""
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)

        self.order = None
        self.buy_price = None
        self.buy_comm = None

    def notify_order(self, order):
        """Handle order notifications."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            self._handle_completed_order(order)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            logger.warning(f"Order {order.status}")

        self.order = None

    def _handle_completed_order(self, order):
        """Handle logic for completed orders."""
        if order.isbuy():
            self.buy_price = order.executed.price
            self.buy_comm = order.executed.comm

            logger.debug(
                f"BUY EXECUTED: Price={order.executed.price:.5f}, "
                f"Cost={order.executed.value:.2f}, "
                f"Comm={order.executed.comm:.2f}"
            )

        elif order.issell():
            profit = order.executed.value - (self.buy_price * order.executed.size)

            logger.debug(
                f"SELL EXECUTED: Price={order.executed.price:.5f}, "
                f"Profit={profit:.2f}"
            )

    def notify_trade(self, trade):
        """Handle trade notifications."""
        if not trade.isclosed:
            return

        logger.debug(f"TRADE PROFIT: Gross={trade.pnl:.2f}, Net={trade.pnlcomm:.2f}")

    def next(self):
        """Execute strategy logic on each bar."""
        if self.order:
            return

        current_rsi = self.rsi[0]
        current_price = self.data.close[0]

        if not self.position:
            self._handle_entry(current_rsi, current_price)
        else:
            self._handle_exit(current_rsi, current_price)

    def _handle_entry(self, rsi_value: float, price: float):
        """Handle entry logic for new positions."""
        if rsi_value < self.params.rsi_oversold:
            cash = self.broker.get_cash()
            size = (cash * self.params.position_size) / price

            self.order = self.buy(size=size)
            logger.debug(f"BUY SIGNAL: RSI={rsi_value:.2f}, Price={price:.5f}")

    def _handle_exit(self, rsi_value: float, price: float):
        """Handle exit logic for open positions."""
        # Check for Strategy Exit Signal
        if rsi_value > self.params.rsi_overbought:
            self.order = self.sell(size=self.position.size)
            logger.debug(f"SELL SIGNAL: RSI={rsi_value:.2f}")
            return

        if not self.buy_price:
            return

        # Check for Risk Management Exits
        if self._is_stop_loss_hit(price):
            self.order = self.sell(size=self.position.size)
            loss_pct = ((self.buy_price - price) / self.buy_price) * 100
            logger.debug(f"STOP LOSS HIT: Loss={loss_pct:.2f}%")

        elif self._is_take_profit_hit(price):
            self.order = self.sell(size=self.position.size)
            profit_pct = ((price - self.buy_price) / self.buy_price) * 100
            logger.debug(f"TAKE PROFIT HIT: Profit={profit_pct:.2f}%")

    def _is_stop_loss_hit(self, price: float) -> bool:
        """Check if stop loss condition is met."""
        loss_pct = ((self.buy_price - price) / self.buy_price) * 100
        return loss_pct >= self.params.stop_loss_pct

    def _is_take_profit_hit(self, price: float) -> bool:
        """Check if take profit condition is met."""
        profit_pct = ((price - self.buy_price) / self.buy_price) * 100
        return profit_pct >= self.params.take_profit_pct
