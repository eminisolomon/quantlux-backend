"""MetaApi Execution operations."""

from datetime import datetime

from app.execution.broker import AbstractBroker
from app.metaapi.connection import (
    MetaApiConnection,
    get_latency_monitor,
    get_rate_limiter,
    retry_on_error,
)
from app.utils.logger import logger


class MetaApiBroker(AbstractBroker):
    """MetaApi implementation of the AbstractBroker."""

    @staticmethod
    def _build_order_options(comment: str, symbol: str, order_type: str) -> dict:
        return {
            "comment": comment or f"{order_type} {symbol}",
            "clientId": f"{order_type.lower()}_{symbol}_{datetime.now().timestamp()}",
        }

    async def _execute_safe(
        self, operation_name: str, coro, log_msg: str, success_msg: str
    ) -> dict:
        """Helper to execute MetaApi operations with rate limiting, latency monitoring, and error handling."""
        rate_limiter = get_rate_limiter()
        latency_monitor = get_latency_monitor()

        await rate_limiter.await_if_needed()

        try:
            logger.info(log_msg)
            with latency_monitor.measure(operation_name):
                result = await coro

            logger.info(f"✅ {success_msg}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute {operation_name}: {e}")
            return {"error": str(e), "success": False}

    @retry_on_error(max_retries=3, initial_delay=1.0)
    async def create_market_buy_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict:
        connection = MetaApiConnection.get_connection()
        return await self._execute_safe(
            operation_name="create_market_buy_order",
            coro=connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                options=self._build_order_options(comment, symbol, "Buy"),
            ),
            log_msg=f"Creating BUY order: {symbol} {volume} lots",
            success_msg="Buy order executed",
        )

    @retry_on_error(max_retries=3, initial_delay=1.0)
    async def create_market_sell_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict:
        connection = MetaApiConnection.get_connection()
        return await self._execute_safe(
            operation_name="create_market_sell_order",
            coro=connection.create_market_sell_order(
                symbol=symbol,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                options=self._build_order_options(comment, symbol, "Sell"),
            ),
            log_msg=f"Creating SELL order: {symbol} {volume} lots",
            success_msg="Sell order executed",
        )

    @retry_on_error(max_retries=2, initial_delay=0.5)
    async def modify_position(
        self,
        position_id: str,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> dict:
        connection = MetaApiConnection.get_connection()
        return await self._execute_safe(
            operation_name="modify_position",
            coro=connection.modify_position(
                position_id=position_id,
                stop_loss=stop_loss,
                take_profit=take_profit,
            ),
            log_msg=f"Modifying position {position_id}",
            success_msg="Position modified",
        )

    @retry_on_error(max_retries=3, initial_delay=1.0)
    async def close_position(
        self, position_id: str, volume: float | None = None
    ) -> dict:
        """Close a position (full or partial)."""
        connection = MetaApiConnection.get_connection()
        coro = (
            connection.close_position_partially(position_id=position_id, volume=volume)
            if volume
            else connection.close_position(position_id=position_id)
        )
        return await self._execute_safe(
            operation_name="close_position",
            coro=coro,
            log_msg=f"Closing position {position_id}",
            success_msg="Position closed",
        )

    @retry_on_error(max_retries=2, initial_delay=0.5)
    async def cancel_order(self, order_id: str) -> dict:
        connection = MetaApiConnection.get_connection()
        return await self._execute_safe(
            operation_name="cancel_order",
            coro=connection.cancel_order(order_id=order_id),
            log_msg=f"Cancelling order {order_id}",
            success_msg="Order cancelled",
        )
