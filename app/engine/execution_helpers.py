"""Shared execution helpers for order processing and notifications."""

import asyncio
from collections.abc import Callable

from app.core import logger
from app.core import messages as msg
from app.core.enums import SignalAction
from app.engine.queue import OrderTask, order_queue
from app.metaapi.orders import OrderFactory
from app.models import OrderSendResult
from app.utils.notifiers import get_trade_notifier


async def execute_order(
    action: SignalAction,
    symbol: str,
    volume: float,
    stop_loss: float | None,
    take_profit: float | None,
    comment: str,
    notification_callback: Callable[[str], None] | None = None,
) -> None:
    """Execute a single order via the order queue."""
    request = OrderFactory.create_market_order(
        symbol=symbol,
        volume=volume,
        order_type=action,
        sl=stop_loss or 0.0,
        tp=take_profit or 0.0,
        comment=comment,
    )

    task_obj = OrderTask(
        action=request.action,
        symbol=request.symbol,
        volume=request.volume,
        stop_loss=request.sl,
        take_profit=request.tp,
        magic_number=request.magic,
        comment=request.comment,
    )

    future = await order_queue.enqueue_order(task_obj)
    result = await future

    if result:
        success = (
            result.get("success") if "success" in result else ("positionId" in result)
        )
        order_result = OrderSendResult(
            success=success,
            price=result.get("price", 0.0),
            error=result.get("error"),
        )
        _handle_execution_result(
            order_result,
            symbol,
            action,
            volume,
            stop_loss,
            take_profit,
            comment,
            notification_callback,
        )


def _handle_execution_result(
    result: OrderSendResult,
    symbol: str,
    action: SignalAction,
    volume: float,
    sl: float | None = None,
    tp: float | None = None,
    comment: str = "",
    notification_callback: Callable[[str], None] | None = None,
) -> None:
    """Log and notify about execution results."""
    if result.success:
        msg_str = msg.TRADE_SUCCESS.format(
            symbol=symbol, action=action.value, volume=volume, price=result.price
        )
        logger.info(msg_str)
        # Send rich notification
        asyncio.create_task(
            _notify_rich(
                symbol=symbol,
                action=action,
                volume=volume,
                price=result.price,
                sl=sl,
                tp=tp,
                comment=comment,
            )
        )
    else:
        msg_str = msg.TRADE_EXECUTION_FAILED.format(symbol=symbol, error=result.error)
        logger.error(msg_str)

    if notification_callback:
        notification_callback(msg_str)


async def _notify_rich(
    symbol: str,
    action: SignalAction,
    volume: float,
    price: float,
    sl: float | None = None,
    tp: float | None = None,
    comment: str = "",
):
    """Send rich Telegram notification."""
    try:
        notifier = get_trade_notifier()
        await notifier.notify_trade_opened(
            symbol=symbol,
            trade_type=action,
            volume=volume,
            entry_price=price,
            stop_loss=sl,
            take_profit=tp,
            strategy=comment,
        )
    except Exception as e:
        logger.error(msg.NOTIFY_ERROR.format(error=e))
