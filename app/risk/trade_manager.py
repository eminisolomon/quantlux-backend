import asyncio
from typing import Any

from app.core import logger, settings
from app.core.protocols import BrokerProtocol
from app.schemas.metaapi import TradePosition, SymbolInfo


class ActiveTradeManager:
    """Monitors open positions for trailing stops, breakeven, and partial take profits."""

    def __init__(self, broker: BrokerProtocol):
        self.broker = broker
        self.is_running = False
        self._task = None

        # Configuration per trade or global
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
            await asyncio.sleep(60)  # Check every minute

    async def manage_open_trades(self) -> None:
        """Fetch and process all open positions."""
        positions = await self.broker.get_positions()

        for pos in positions:
            magic = getattr(pos, "magic", None) or (
                isinstance(pos, dict) and pos.get("magic")
            )
            if magic != settings.MAGIC_NUMBER:
                continue

            symbol_info = await self.broker.get_symbol_info(pos.symbol)
            if not symbol_info:
                continue

            await self._apply_trade_management(pos, symbol_info)

    async def _apply_trade_management(
        self, pos: TradePosition, symbol_info: SymbolInfo
    ) -> None:
        try:
            is_buy = pos.type == "POSITION_TYPE_BUY"

            # Convert pips to price distance
            point_value = symbol_info.point
            # Adjust mapping for different pairs like JPY
            pip_multiplier = 10 if "JPY" in symbol_info.symbol else 1
            pip_size = point_value * pip_multiplier

            current_profit_pips = 0.0
            if is_buy:
                current_profit_pips = (pos.currentPrice - pos.openPrice) / pip_size
            else:
                current_profit_pips = (pos.openPrice - pos.currentPrice) / pip_size

            # 1. Breakeven Check
            if (
                self.enable_breakeven
                and current_profit_pips >= self.breakeven_trigger_pips
            ):
                new_sl = (
                    pos.openPrice + (self.breakeven_lock_pips * pip_size)
                    if is_buy
                    else pos.openPrice - (self.breakeven_lock_pips * pip_size)
                )

                # Check if SL needs updating (only if current SL is worse than breakeven)
                needs_update = False
                if is_buy and (pos.stopLoss is None or pos.stopLoss < new_sl):
                    needs_update = True
                elif not is_buy and (
                    pos.stopLoss is None or pos.stopLoss > new_sl or pos.stopLoss == 0
                ):
                    needs_update = True

                if needs_update:
                    logger.info(
                        f"Moving SL to breakeven for {pos.symbol} (ID: {pos.id})"
                    )
                    await self.broker.modify_position(
                        pos.id, stop_loss=new_sl, take_profit=pos.takeProfit
                    )
                    return  # Skip trailing stop logic this cycle

            # 2. Trailing Stop Check
            if (
                self.enable_trailing_stop
                and current_profit_pips >= self.trailing_stop_pips
            ):
                # Calculate new trailing stop loss
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
                    logger.info(
                        f"Trailing SL for {pos.symbol} (ID: {pos.id}) to {new_sl:.5f}"
                    )
                    await self.broker.modify_position(
                        pos.id, stop_loss=new_sl, take_profit=pos.takeProfit
                    )

        except Exception as e:
            logger.error(f"Trade management error for {pos.symbol}: {e}")
