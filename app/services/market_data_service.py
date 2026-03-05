"""Unified Market Data Service handling both historical and real-time feeds."""

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from app.core import messages as msg
from app.core.settings import settings
from app.metaapi.adapter import MetaApiAdapter
from app.metaapi.connection import (
    get_latency_monitor,
    get_rate_limiter,
    retry_on_error,
)
from app.schemas.market import TickData
from app.utils.logger import logger


class MarketDataService:
    """Manages historical data retrieval and real-time market polling."""

    TIMEFRAMES = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "M30": "30m",
        "H1": "1h",
        "H4": "4h",
        "D1": "1d",
        "W1": "1w",
        "MN1": "1M",
    }

    def __init__(self, symbols: list[str], metaapi: MetaApiAdapter) -> None:
        self.symbols: set[str] = set(symbols)
        self.metaapi = metaapi
        self._running: bool = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._callbacks: list[Callable[[str, TickData], None]] = []

    def register_callback(self, callback: Callable[[str, TickData], None]) -> None:
        self._callbacks.append(callback)

    async def start_feed(self) -> None:
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

    async def stop_feed(self) -> None:
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DataFeed stopped.")

    async def add_symbol_to_feed(self, symbol: str) -> None:
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

    @staticmethod
    def _calculate_start_time(
        start_time: datetime | None, limit: int, timeframe: str
    ) -> datetime:
        """Calculate start time for historical data request."""
        if start_time:
            return start_time

        timeframe_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }

        minutes = timeframe_minutes.get(timeframe, 60)
        return datetime.now(timezone.utc) - timedelta(minutes=minutes * limit)

    @retry_on_error(max_retries=3, initial_delay=1.0)
    async def get_candles(
        self,
        symbol: str,
        timeframe: str = "H1",
        start_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[dict] | None:
        """Get historical candles."""
        rate_limiter = get_rate_limiter()
        latency_monitor = get_latency_monitor()

        await rate_limiter.await_if_needed()

        try:
            if timeframe in self.TIMEFRAMES:
                timeframe = self.TIMEFRAMES[timeframe]

            calculated_start = self._calculate_start_time(start_time, limit, timeframe)

            logger.debug(
                f"Fetching candles: {symbol} {timeframe} from {calculated_start}"
            )

            with latency_monitor.measure("get_candles"):
                candles = await self.metaapi.read_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=calculated_start,
                    limit=limit,
                )

            logger.info(
                f"Retrieved {len(candles) if candles else 0} candles for {symbol}"
            )
            return candles

        except Exception as e:
            logger.error(f"Failed to get candles for {symbol}: {e}")
            return None

    @staticmethod
    def _convert_candles_to_dataframe(candles: list[dict]) -> pd.DataFrame:
        """Convert candles list to DataFrame."""
        df = pd.DataFrame(candles)

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)

        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not in candles data")

        df.sort_index(inplace=True)
        return df

    async def get_candles_as_dataframe(
        self,
        symbol: str,
        timeframe: str = "H1",
        start_time: datetime | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame | None:
        """Get historical candles as DataFrame."""
        candles = await self.get_candles(symbol, timeframe, start_time, limit)

        if not candles:
            return None

        try:
            df = self._convert_candles_to_dataframe(candles)
            logger.debug(f"Converted {len(df)} candles to DataFrame for {symbol}")
            return df
        except Exception as e:
            logger.error(f"Failed to convert candles to DataFrame: {e}")
            return None

    @retry_on_error(max_retries=2, initial_delay=0.5)
    async def get_ticks(
        self, symbol: str, start_time: datetime | None = None, limit: int = 1000
    ) -> list[dict] | None:
        """Get historical ticks."""
        rate_limiter = get_rate_limiter()
        latency_monitor = get_latency_monitor()

        await rate_limiter.await_if_needed()

        try:
            if not start_time:
                start_time = datetime.now(timezone.utc) - timedelta(hours=1)

            logger.debug(f"Fetching ticks: {symbol} from {start_time}")

            with latency_monitor.measure("get_ticks"):
                ticks = await self.metaapi.read_ticks(
                    symbol=symbol, start_time=start_time, limit=limit
                )

            logger.info(f"Retrieved {len(ticks) if ticks else 0} ticks for {symbol}")
            return ticks

        except Exception as e:
            logger.error(f"Failed to get ticks for {symbol}: {e}")
            return None
