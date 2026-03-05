"""Internal async queue processor for order execution."""

import asyncio
import json
from dataclasses import dataclass, asdict

from app.core.enums import SignalAction
from app.core.protocols import BrokerProtocol
from app.utils.logger import logger
from app.core.redis_client import redis_client
from app.core import messages as msg


@dataclass
class OrderTask:
    """Represents an order task in the queue."""

    action: SignalAction
    symbol: str
    volume: float
    stop_loss: float | None = None
    take_profit: float | None = None
    magic_number: int | None = None
    position_id: str | None = None
    comment: str = ""

    def to_dict(self):
        d = asdict(self)
        d["action"] = self.action.value
        return d

    @classmethod
    def from_dict(cls, d: dict):
        d["action"] = SignalAction(d["action"])
        d.pop("future", None)
        return cls(**d)


class OrderQueue:
    """Manages coordinated asynchronous order execution."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.is_running = False
            cls._instance.executor = None
            cls._instance.worker_task = None
            cls._instance.queue_key = "quantlux:execution_queue"
        return cls._instance

    def initialize(self, executor: BrokerProtocol):
        """Initialize the queue processor with a trade executor."""
        self.executor = executor

    async def start(self):
        """Start the queue worker."""
        if not self.executor:
            raise ValueError("OrderQueue not initialized with a TradeExecutor.")

        if self.is_running:
            return

        self.is_running = True
        self.worker_task = asyncio.create_task(self._process_queue())
        logger.info("🟢 OrderQueue processor started (Redis)")

    async def stop(self):
        """Stop the queue worker and process remaining tasks."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("🔴 OrderQueue processor stopped")

    async def enqueue_order(self, task: OrderTask) -> None:
        """Add an order to the execution queue via Redis."""
        redis = redis_client.redis
        task_data = json.dumps(task.to_dict())

        if task.action == SignalAction.SELL and task.position_id:
            pass

        await redis.rpush(self.queue_key, task_data)
        logger.debug(f"Queued order: {task.action} {task.symbol}")

    async def _process_queue(self):
        """Background task that pulls from queue and executes."""
        redis = redis_client.redis
        while self.is_running:
            try:
                result = await redis.blpop(self.queue_key, timeout=1)
                if result:
                    _, task_data = result
                    task_dict = json.loads(task_data)
                    task = OrderTask.from_dict(task_dict)
                    await self._execute_task(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing order queue task: {e}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: OrderTask):
        """Execute a single order task."""
        if not self.executor:
            logger.error("TradeExecutor not found. Cannot execute task.")
            return

        try:
            result = None
            if task.action == SignalAction.BUY:
                logger.info(f"Executing queued BUY for {task.symbol}")
                result = await self.executor.create_market_buy_order(
                    symbol=task.symbol,
                    volume=task.volume,
                    stop_loss=task.stop_loss,
                    take_profit=task.take_profit,
                    comment=task.comment,
                )
            elif task.action == SignalAction.SELL and not task.position_id:
                logger.info(f"Executing queued SELL for {task.symbol}")
                result = await self.executor.create_market_sell_order(
                    symbol=task.symbol,
                    volume=task.volume,
                    stop_loss=task.stop_loss,
                    take_profit=task.take_profit,
                    comment=task.comment,
                )
            elif task.action == SignalAction.SELL and task.position_id:
                logger.info(f"Executing queued CLOSE for position {task.position_id}")
                result = await self.executor.close_position(
                    position_id=task.position_id
                )

            success = result and (result.get("success") or "positionId" in result)
            if success:
                price = result.get("price", 0.0) if result else 0.0
                logger.info(
                    msg.TRADE_SUCCESS.format(
                        symbol=task.symbol,
                        action=task.action.value,
                        volume=task.volume,
                        price=price,
                    )
                )
            else:
                error = result.get("error") if result else "Unknown error"
                logger.error(
                    msg.TRADE_EXECUTION_FAILED.format(symbol=task.symbol, error=error)
                )

        except Exception as e:
            logger.error(f"Failed queued order execution: {e}")


order_queue = OrderQueue()
