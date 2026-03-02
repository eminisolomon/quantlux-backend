"""Split Order Manager for Partial Take Profit Execution."""

from collections.abc import Callable

from app.core import messages as msg
from app.core import settings
from app.core.enums import SignalAction
from app.engine.execution_helpers import execute_order
from app.engine.queue import OrderTask, order_queue
from app.utils.logger import logger


class SplitOrderManager:
    """Manages the execution of split orders for partial take profits."""

    def __init__(
        self,
        metaapi,
        notification_callback: Callable[[str], None] | None = None,
    ):
        self.metaapi = metaapi
        self.notification_callback = notification_callback

    async def execute(
        self,
        action: SignalAction,
        symbol: str,
        total_volume: float,
        stop_loss: float | None,
        tp_levels: list[float],
        base_comment: str,
    ) -> None:
        """
        Execute trade with split orders based on TP levels.

        If split execution is disabled in settings, executes a single order
        targeting the first TP level.
        """
        if not settings.ALLOW_SPLIT_EXECUTION:
            logger.info(msg.SPLITTER_DISABLED.format(symbol=symbol))
            take_profit = tp_levels[0] if tp_levels else None
            await execute_order(
                action=action,
                symbol=symbol,
                volume=total_volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=base_comment,
                notification_callback=self.notification_callback,
            )
            return

        # Execution Logic
        num_orders = len(tp_levels)
        base_vol = round(total_volume / num_orders, 2)

        # Adjust last order to match total volume exactly (handle rounding)
        volumes = [base_vol] * num_orders
        remainder = round(total_volume - sum(volumes), 2)
        if remainder != 0:
            volumes[-1] = round(volumes[-1] + remainder, 2)

        logger.info(
            msg.SPLITTER_START.format(symbol=symbol, volumes=volumes, levels=tp_levels)
        )

        executed_count = 0
        for i, (vol, tp) in enumerate(zip(volumes, tp_levels)):
            if vol <= 0:
                continue

            comment = f"{base_comment} (TP{i + 1})"

            task_obj = OrderTask(
                action=action,
                symbol=symbol,
                volume=vol,
                stop_loss=stop_loss,
                take_profit=tp,
                comment=comment,
            )
            future = await order_queue.enqueue_order(task_obj)
            result = await future

            if result and (result.get("success") or "positionId" in result):
                executed_count += 1
                if self.notification_callback:
                    self.notification_callback(
                        msg.SPLIT_TRADE_SUCCESS.format(
                            symbol=symbol,
                            index=i + 1,
                            total=num_orders,
                            volume=vol,
                            tp=tp,
                        )
                    )
            else:
                error = result.get("error") if result else "Unknown error"
                if self.notification_callback:
                    self.notification_callback(
                        msg.SPLIT_TRADE_FAILED.format(
                            symbol=symbol, index=i + 1, total=num_orders, error=error
                        )
                    )

        if executed_count == num_orders:
            logger.info(msg.ALL_SPLIT_SUCCESS.format(symbol=symbol))
