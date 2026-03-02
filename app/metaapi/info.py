"""MetaApi Information and Query operations."""

import asyncio

from app.metaapi.connection import MetaApiConnection
from app.utils.logger import logger


class MetaApiInfo:
    """Manages MetaApi information retrieval and monitoring."""

    @staticmethod
    async def get_positions(symbol: str | None = None) -> list[dict]:
        """Get open positions."""
        latency_monitor = MetaApiConnection.get_latency_monitor()

        try:
            connection = MetaApiConnection.get_connection()
            terminal_state = connection.terminal_state

            with latency_monitor.measure("get_positions"):
                positions = terminal_state.positions

            if symbol:
                positions = [p for p in positions if p["symbol"] == symbol]

            logger.debug(f"Retrieved {len(positions)} positions")
            return positions

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    @staticmethod
    async def get_orders(symbol: str | None = None) -> list[dict]:
        """Get pending orders."""
        latency_monitor = MetaApiConnection.get_latency_monitor()

        try:
            connection = MetaApiConnection.get_connection()
            terminal_state = connection.terminal_state

            with latency_monitor.measure("get_orders"):
                orders = terminal_state.orders

            if symbol:
                orders = [o for o in orders if o["symbol"] == symbol]

            logger.debug(f"Retrieved {len(orders)} orders")
            return orders

        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    @staticmethod
    async def get_account_info() -> dict | None:
        """Get account information and update metrics."""
        latency_monitor = MetaApiConnection.get_latency_monitor()

        try:
            connection = MetaApiConnection.get_connection()
            terminal_state = connection.terminal_state

            with latency_monitor.measure("get_account_info"):
                account_info = terminal_state.account_information

            if account_info:
                logger.debug(
                    f"Account: Balance={account_info.get('balance')}, "
                    f"Equity={account_info.get('equity')}, "
                    f"Margin={account_info.get('margin')}"
                )

            return account_info

        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None


def get_positions_sync(*args, **kwargs) -> list[dict]:
    """Synchronous wrapper for get_positions."""
    return asyncio.run(MetaApiInfo.get_positions(*args, **kwargs))


def get_account_info_sync() -> dict | None:
    """Synchronous wrapper for get_account_info."""
    return asyncio.run(MetaApiInfo.get_account_info())


__all__ = ["MetaApiInfo"]
