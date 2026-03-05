import asyncio
from typing import Any

from app.core import logger, settings
from app.core.protocols import BrokerProtocol
from app.schemas.metaapi import TradePosition, SymbolInfo


def _pip_size(symbol_info: SymbolInfo) -> float:
    """Return pip size in price units for the given symbol."""
    return symbol_info.point * (10 if "JPY" in symbol_info.symbol else 1)


def _profit_pips(pos: TradePosition, is_buy: bool, pip_size: float) -> float:
    """Calculate current floating profit in pips for an open position."""
    if is_buy:
        return (pos.currentPrice - pos.openPrice) / pip_size
    return (pos.openPrice - pos.currentPrice) / pip_size


class ActiveTradeManager:
    """Monitors open positions for trailing stops, breakeven, and partial take profits."""

    def __init__(self, broker: BrokerProtocol):
        self.broker = broker
        self.is_running = False
        self._task = None

        self.enable_trailing_stop = True
        self.trailing_stop_pips = 20.0

        self.enable_breakeven = True
        self.breakeven_trigger_pips = 15.0
        self.breakeven_lock_pips = 2.0

    async def start(self) -> None:
        """Start the monitoring background task."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("ActiveTradeManager monitoring started.")

    async def stop(self) -> None:
        """Stop the monitoring background task."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ActiveTradeManager stopped.")

    async def _monitor_loop(self) -> None:
        while self.is_running:
            try:
                await self.manage_open_trades()
            except Exception as e:
                logger.error(f"Error in ActiveTradeManager loop: {e}")
            await asyncio.sleep(60)

    async def manage_open_trades(self) -> None:
        """Fetch and process all bot-managed open positions."""
        positions = await self._get_managed_positions()
        for pos in positions:
            await self._process_position(pos)

    async def _get_managed_positions(self) -> list:
        """Return only positions belonging to this bot (by magic number)."""
        all_positions = await self.broker.get_positions()
        return [
            pos
            for pos in all_positions
            if (
                getattr(pos, "magic", None) == settings.MAGIC_NUMBER
                or (isinstance(pos, dict) and pos.get("magic") == settings.MAGIC_NUMBER)
            )
        ]

    async def _process_position(self, pos: TradePosition) -> None:
        """Fetch symbol info and apply trade management for a single position."""
        symbol_info = await self.broker.get_symbol_info(pos.symbol)
        if symbol_info:
            await self._apply_trade_management(pos, symbol_info)

    async def _apply_trade_management(
        self, pos: TradePosition, symbol_info: SymbolInfo
    ) -> None:
        try:
            is_buy = pos.type == "POSITION_TYPE_BUY"
            pip_size = _pip_size(symbol_info)
            profit_pips = _profit_pips(pos, is_buy, pip_size)

            breakeven_triggered = await self._handle_breakeven(
                pos, is_buy, pip_size, profit_pips
            )
            if not breakeven_triggered:
                await self._handle_trailing_stop(pos, is_buy, pip_size, profit_pips)

        except Exception as e:
            logger.error(f"Trade management error for {pos.symbol}: {e}")

    async def _handle_breakeven(
        self,
        pos: TradePosition,
        is_buy: bool,
        pip_size: float,
        current_profit_pips: float,
    ) -> bool:
        """Apply breakeven stop loss if trigger conditions are met."""
        if not (
            self.enable_breakeven and current_profit_pips >= self.breakeven_trigger_pips
        ):
            return False

        lock_dist = self.breakeven_lock_pips * pip_size
        new_sl = pos.openPrice + lock_dist if is_buy else pos.openPrice - lock_dist

        needs_update = False
        if is_buy and (pos.stopLoss is None or pos.stopLoss < new_sl):
            needs_update = True
        elif not is_buy and (
            pos.stopLoss is None or pos.stopLoss > new_sl or pos.stopLoss == 0
        ):
            needs_update = True

        if needs_update:
            logger.info(f"Moving SL to breakeven for {pos.symbol} (ID: {pos.id})")
            await self.broker.modify_position(
                pos.id, stop_loss=new_sl, take_profit=pos.takeProfit
            )
            return True

        return False

    async def _handle_trailing_stop(
        self,
        pos: TradePosition,
        is_buy: bool,
        pip_size: float,
        current_profit_pips: float,
    ) -> None:
        """Apply trailing stop loss if trigger conditions are met."""
        if not (
            self.enable_trailing_stop and current_profit_pips >= self.trailing_stop_pips
        ):
            return

        trail_distance = self.trailing_stop_pips * pip_size
        new_sl = (
            pos.currentPrice - trail_distance
            if is_buy
            else pos.currentPrice + trail_distance
        )

        needs_update = False
        if is_buy and (pos.stopLoss is None or new_sl > pos.stopLoss):
            needs_update = True
        elif not is_buy and (
            pos.stopLoss is None or new_sl < pos.stopLoss or pos.stopLoss == 0
        ):
            needs_update = True

        if needs_update:
            logger.info(f"Trailing SL for {pos.symbol} (ID: {pos.id}) to {new_sl:.5f}")
            await self.broker.modify_position(
                pos.id, stop_loss=new_sl, take_profit=pos.takeProfit
            )
