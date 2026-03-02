import asyncio
from collections.abc import Callable

from app.core import messages as msg
from app.core.settings import settings
from app.metaapi.adapter import MetaApiAdapter
from app.schemas.market import TickData
from app.utils.logger import logger


class DataFeed:
    """Real-time data feed manager using asyncio."""

    def __init__(self, symbols: list[str], metaapi: MetaApiAdapter) -> None:
        self.symbols: set[str] = set(symbols)
        self.metaapi = metaapi
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._callbacks: list[Callable[[str, TickData], None]] = []

    def register_callback(self, callback: Callable[[str, TickData], None]) -> None:
        self._callbacks.append(callback)

    async def start(self) -> None:
        """Start polling market data."""
        if self._running:
            return

        for symbol in self.symbols:
            if await self.metaapi.symbol_select(symbol, True):
                logger.debug(f"Subscribed to {symbol}")
            else:
                logger.error(f"Failed to subscribe to {symbol}")

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(msg.FEED_START.format(symbols=", ".join(self.symbols)))

    async def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DataFeed stopped.")

    async def add_symbol(self, symbol: str) -> None:
        """Add a symbol to the feed dynamically."""
        async with self._lock:
            if await self.metaapi.symbol_select(symbol, True):
                self.symbols.add(symbol)
                logger.info(f"Added symbol {symbol} to DataFeed")

    async def _poll_loop(self) -> None:
        """Internal async polling loop."""
        while self._running:
            try:
                if not self.metaapi.is_connected():
                    await asyncio.sleep(settings.MT5_RECONNECT_INTERVAL)
                    continue

                async with self._lock:
                    current_symbols = list(self.symbols)

                for symbol in current_symbols:
                    tick_dict = await self.metaapi.get_symbol_price(symbol)
                    if tick_dict:
                        tick_data = TickData(symbol=symbol, **tick_dict)
                        for cb in self._callbacks:
                            try:
                                if asyncio.iscoroutinefunction(cb):
                                    await cb(symbol, tick_data)
                                else:
                                    cb(symbol, tick_data)
                            except Exception as e:
                                logger.error(f"Error in DataFeed callback: {e}")

                await asyncio.sleep(settings.FEED_POLL_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(msg.FEED_ERROR.format(error=e))
                await asyncio.sleep(settings.FEED_ERROR_INTERVAL)
