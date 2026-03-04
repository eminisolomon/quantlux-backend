"""Order execution helpers."""

from app.core import logger
from app.core import messages as msg
from app.core.enums import SignalAction
from app.engine.queue import OrderTask, order_queue
from app.metaapi.orders import OrderFactory
from app.schemas import OrderSendResult


async def execute_order(
    action: SignalAction,
    symbol: str,
    volume: float,
    stop_loss: float | None,
    take_profit: float | None,
    comment: str,
) -> None:
    """Build and enqueue a market order, then log the result."""
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
        if order_result.success:
            logger.info(
                msg.TRADE_SUCCESS.format(
                    symbol=symbol,
                    action=action.value,
                    volume=volume,
                    price=order_result.price,
                )
            )
        else:
            logger.error(
                msg.TRADE_EXECUTION_FAILED.format(
                    symbol=symbol, error=order_result.error
                )
            )
