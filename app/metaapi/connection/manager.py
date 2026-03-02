"""WebSocket connection manager with auto-reconnect for MetaApi."""

import asyncio
from collections.abc import Callable

from app.core.settings import settings
from app.utils.logger import logger


class ConnectionManager:
    """Manages WebSocket connection with auto-reconnect capability."""

    def __init__(
        self,
        connection,
        reconnect_delay: float = None,
        max_reconnect_attempts: int = None,
    ):
        """Initialize connection manager with auto-reconnect settings."""
        self.connection = connection
        self.reconnect_delay = (
            reconnect_delay
            if reconnect_delay is not None
            else settings.WS_RECONNECT_DELAY
        )
        self.max_reconnect_attempts = (
            max_reconnect_attempts
            if max_reconnect_attempts is not None
            else settings.WS_MAX_RECONNECT_ATTEMPTS
        )
        self.is_connected = False
        self.reconnect_task: asyncio.Task | None = None
        self.on_reconnect_callbacks: list[Callable] = []

    async def ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if needed."""
        if not self.is_connected:
            await self.reconnect()
        return self.is_connected

    async def reconnect(self) -> bool:
        """Attempt to reconnect WebSocket."""
        attempt = 0
        while not self.is_connected and (
            self.max_reconnect_attempts == 0 or attempt < self.max_reconnect_attempts
        ):
            attempt += 1
            try:
                logger.info(
                    f"Attempting MetaApi WebSocket reconnection (attempt {attempt})..."
                )

                # Connect and wait for synchronization
                if not self.connection.is_connected():
                    await self.connection.connect()

                # Wait for terminal state to synchronize
                await self.connection.wait_synchronized()

                self.is_connected = True
                logger.info("✅ MetaApi WebSocket reconnected successfully")

                # Call reconnection callbacks
                await self._trigger_reconnect_callbacks()

                return True

            except Exception as e:
                logger.error(
                    f"Reconnection attempt {attempt} failed: {e}. "
                    f"Retrying in {self.reconnect_delay}s..."
                )
                await asyncio.sleep(self.reconnect_delay)

        if not self.is_connected:
            logger.error(
                f"Failed to reconnect after {attempt} attempts. Connection may be permanently lost."
            )

        return self.is_connected

    def on_disconnect(self):
        """Called when connection drops. Starts auto-reconnect."""
        if self.is_connected:
            self.is_connected = False
            logger.warning("⚠️  MetaApi WebSocket disconnected")

            # Start reconnection task if not already running
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self.reconnect())

    def register_reconnect_callback(self, callback: Callable):
        """Register a callback to run after successful reconnection."""
        self.on_reconnect_callbacks.append(callback)

    async def _trigger_reconnect_callbacks(self):
        """Trigger all registered reconnect callbacks."""
        for callback in self.on_reconnect_callbacks:
            try:
                await callback()
            except Exception as e:
                logger.error(f"Error in reconnect callback: {e}")

    async def close(self):
        """Close the connection gracefully."""
        try:
            self.is_connected = False
            if self.reconnect_task and not self.reconnect_task.done():
                self.reconnect_task.cancel()

            if self.connection:
                await self.connection.close()

            logger.info("Connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
