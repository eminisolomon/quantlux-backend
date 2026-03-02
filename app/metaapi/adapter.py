from typing import Any

from app.execution.broker import AbstractBroker
from app.execution.metaapi import MetaApiBroker
from app.metaapi.connection import MetaApiConnection
from app.metaapi.data import MetaApiData
from app.metaapi.info import MetaApiInfo
from app.metaapi.mappers import (
    map_account_info,
    map_symbol_info,
    map_trade_order,
    map_trade_position,
)
from app.models.metaapi import (
    AccountInfo,
    SymbolInfo,
    TradeOrder,
    TradePosition,
)


class MetaApiAdapter(AbstractBroker):
    """
    Unified adapter for MetaApi interaction.
    Consolidates Connection, Information, Data, and Execution.
    """

    def __init__(self):
        self.executor = MetaApiBroker()

    async def initialize(self) -> bool:
        """Initialize connection."""
        return await MetaApiConnection.initialize()

    async def shutdown(self) -> None:
        """Shutdown connection."""
        await MetaApiConnection.shutdown()

    async def ensure_connected(self) -> bool:
        """Ensure connection is active."""
        return await MetaApiConnection.ensure_connected()

    def is_connected(self) -> bool:
        """Check if connected."""
        return MetaApiConnection.is_connected()

    async def get_terminal_state(self) -> dict[str, Any]:
        """Get current terminal state."""
        return await MetaApiConnection.get_terminal_state()

    # --- Information Methods ---

    async def get_account_info(self) -> AccountInfo | None:
        """Get account information."""
        info = await MetaApiInfo.get_account_info()
        return map_account_info(info) if info else None

    async def get_positions(self, symbol: str | None = None) -> list[TradePosition]:
        """Get open positions."""
        positions = await MetaApiInfo.get_positions(symbol)
        return [map_trade_position(p) for p in positions]

    async def get_orders(self, symbol: str | None = None) -> list[TradeOrder]:
        """Get pending orders."""
        orders = await MetaApiInfo.get_orders(symbol)
        return [map_trade_order(o) for o in orders]

    async def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Get symbol specification."""
        info = await MetaApiData.get_symbol_info(symbol)
        return map_symbol_info(symbol, info) if info else None

    # --- Execution Methods ---

    async def create_market_buy_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Create market buy order."""
        return await self.executor.create_market_buy_order(
            symbol, volume, stop_loss, take_profit, comment
        )

    async def create_market_sell_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Create market sell order."""
        return await self.executor.create_market_sell_order(
            symbol, volume, stop_loss, take_profit, comment
        )

    async def close_position(
        self, position_id: str, volume: float | None = None
    ) -> dict[str, Any]:
        """Close position."""
        return await self.executor.close_position(position_id, volume)

    async def modify_position(
        self,
        position_id: str,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> dict[str, Any]:
        """Modify position."""
        return await self.executor.modify_position(position_id, stop_loss, take_profit)

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Cancel pending order."""
        return await self.executor.cancel_order(order_id)

    # --- Data Methods ---

    async def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """Subscribe/unsubscribe market data."""
        if enable:
            return await MetaApiData.subscribe_to_market_data(symbol)
        return True

    async def get_candles(
        self, symbol: str, timeframe: str = "H1", start_time=None, limit: int = 1000
    ):
        """Get historical candles."""
        return await MetaApiData.get_candles(symbol, timeframe, start_time, limit)

    async def get_candles_as_dataframe(
        self, symbol: str, timeframe: str = "H1", start_time=None, limit: int = 1000
    ):
        """Get historical candles as DataFrame."""
        return await MetaApiData.get_candles_as_dataframe(
            symbol, timeframe, start_time, limit
        )

    async def get_symbol_price(self, symbol: str) -> dict[str, Any] | None:
        """Get current market price."""
        return await MetaApiData.get_symbol_price(symbol)
