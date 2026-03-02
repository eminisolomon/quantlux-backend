"""Internal async queue processor for order execution."""

import asyncio
from asyncio import Queue
from dataclasses import dataclass

from app.core.enums import SignalAction
from app.core.protocols import BrokerProtocol
from app.utils.logger import logger


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
    future: asyncio.Future | None = None


class OrderQueue:
    """Manages coordinated asynchronous order execution."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.queue = Queue()
            cls._instance.is_running = False
            cls._instance.executor = None
            cls._instance.worker_task = None
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
        logger.info("🟢 OrderQueue processor started")

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

    async def enqueue_order(self, task: OrderTask) -> asyncio.Future:
        """Add an order to the execution queue and return a future."""
        loop = asyncio.get_running_loop()
        task.future = loop.create_future()

        if task.action == SignalAction.SELL and task.position_id:
            pass

        await self.queue.put(task)
        logger.debug(f"Queued order: {task.action} {task.symbol}")
        return task.future

    async def _process_queue(self):
        """Background task that pulls from queue and executes."""
        while self.is_running:
            try:
                task: OrderTask = await self.queue.get()
                await self._execute_task(task)
                self.queue.task_done()

                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing order queue task: {e}")

    async def _execute_task(self, task: OrderTask):
        """Execute a single order task."""
        if not self.executor:
            error_msg = "TradeExecutor not found. Cannot execute task."
            logger.error(error_msg)
            if task.future and not task.future.done():
                task.future.set_exception(RuntimeError(error_msg))
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

            if task.future and not task.future.done():
                task.future.set_result(result)
        except Exception as e:
            logger.error(f"Failed queued order execution: {e}")
            if task.future and not task.future.done():
                task.future.set_exception(e)


order_queue = OrderQueue()
