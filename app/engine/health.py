import asyncio
from typing import Callable, Optional
from app.core import logger


class HealthMonitor:
    """
    Monitors data feed and connection stability.
    Sends alerts via Telegram if downtime or issues are detected.
    """

    def __init__(
        self, broker, telegram_notify_cb: Optional[Callable[[str], None]] = None
    ):
        self.broker = broker
        self.telegram_notify_cb = telegram_notify_cb
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health Monitor started.")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health Monitor stopped.")

    async def _monitor_loop(self):
        while self.is_running:
            try:
                is_connected = await self._check_broker_connection()
                if not is_connected:
                    msg = "🚨 *ALERT*: Broker connection lost or latency too high!"
                    logger.warning(msg)
                    if self.telegram_notify_cb:
                        self.telegram_notify_cb(msg)
            except Exception as e:
                logger.error(f"Health check failed: {e}")

            await asyncio.sleep(60)  # Check every 60 seconds

    async def _check_broker_connection(self) -> bool:
        # This will contain specific logic depending on the MetaApi adapter's ping support
        # Placeholder ping logic for broker
        try:
            # Check if broker object has a way to verify connection health
            # if hasattr(self.broker, 'is_connected'): return self.broker.is_connected()
            return True
        except Exception:
            return False
