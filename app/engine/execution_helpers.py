"""Order execution helpers."""

from app.core.enums import SignalAction
from app.engine.queue import OrderTask, order_queue
from app.metaapi.orders import OrderFactory


async def execute_order(
    action: SignalAction,
    symbol: str,
    volume: float,
    stop_loss: float | None,
    take_profit: float | None,
    comment: str,
) -> None:
    """Build and enqueue a market order."""
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

    await order_queue.enqueue_order(task_obj)
