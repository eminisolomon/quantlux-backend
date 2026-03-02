from typing import Any

from app.metaapi.adapter import MetaApiAdapter
from app.schemas.metaapi import TradeOrder, TradePosition


class AccountService:
    """Service for account, position, and order management."""

    def __init__(self, metaapi: MetaApiAdapter):
        self.metaapi = metaapi

    async def get_account_summary(self) -> dict[str, Any]:
        """Get an aggregated account summary."""
        acc = await self.metaapi.get_account_info()
        positions = await self.metaapi.get_positions()
        orders = await self.metaapi.get_orders()

        if not acc:
            return {}

        return {
            "account": acc,
            "positions_count": len(positions),
            "orders_count": len(orders),
            "total_profit": sum(p.profit for p in positions),
            "equity": acc.equity,
            "balance": acc.balance,
            "margin_level": acc.marginLevel,
        }

    async def get_detailed_positions(self) -> list[TradePosition]:
        """Fetch all active positions."""
        return await self.metaapi.get_positions()

    async def get_detailed_orders(self) -> list[TradeOrder]:
        """Fetch all pending orders."""
        return await self.metaapi.get_orders()

    async def ensure_connected(self) -> bool:
        """Proxies connectivity check."""
        return await self.metaapi.ensure_connected()

    def is_connected(self) -> bool:
        """Sync connectivity check."""
        return self.metaapi.is_connected()
