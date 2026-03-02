from typing import Any, Protocol, runtime_checkable

from app.models.metaapi import AccountInfo, SymbolInfo, TradeOrder, TradePosition


@runtime_checkable
class BrokerProtocol(Protocol):
    """Interface for trading broker interactions."""

    async def get_account_info(self) -> AccountInfo | None: ...
    async def get_positions(self, symbol: str | None = None) -> list[TradePosition]: ...
    async def get_orders(self, symbol: str | None = None) -> list[TradeOrder]: ...
    async def get_symbol_info(self, symbol: str) -> SymbolInfo | None: ...
    async def ensure_connected(self) -> bool: ...
    def is_connected(self) -> bool: ...

    async def create_market_buy_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]: ...

    async def create_market_sell_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict[str, Any]: ...

    async def close_position(
        self, position_id: str, volume: float | None = None
    ) -> dict[str, Any]: ...

    async def cancel_order(self, order_id: str) -> dict[str, Any]: ...


@runtime_checkable
class AccountServiceProvider(Protocol):
    """Interface for the Account Service."""

    async def get_account_summary(self) -> dict[str, Any]: ...
    async def get_detailed_positions(self) -> list[TradePosition]: ...
    async def get_detailed_orders(self) -> list[TradeOrder]: ...
    def is_connected(self) -> bool: ...
    async def ensure_connected(self) -> bool: ...
