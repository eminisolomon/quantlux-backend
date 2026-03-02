"""MetaApi Cloud SDK data retrieval with resilience and monitoring."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from app.metaapi.connection import (
    MetaApiConnection,
    get_latency_monitor,
    get_rate_limiter,
    retry_on_error,
)
from app.utils.logger import logger


class MetaApiData:
    """Manages MetaApi data retrieval with retry and latency monitoring."""

    # Timeframe mappings
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

    @staticmethod
    @retry_on_error(max_retries=2, initial_delay=0.5)
    async def get_symbol_info(symbol: str) -> dict | None:
        """Get symbol specification."""
        rate_limiter = get_rate_limiter()
        latency_monitor = get_latency_monitor()

        await rate_limiter.await_if_needed()

        try:
            connection = MetaApiConnection.get_connection()

            with latency_monitor.measure("get_symbol_info"):
                symbol_spec = await connection.get_symbol_specification(symbol)

            logger.debug(f"Retrieved symbol info for {symbol}")
            return symbol_spec

        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None

    @staticmethod
    async def get_symbol_price(symbol: str) -> dict[str, Any] | None:
        """Get current price for a symbol."""
        latency_monitor = get_latency_monitor()

        try:
            connection = MetaApiConnection.get_connection()

            with latency_monitor.measure("get_symbol_price"):
                price = await connection.get_symbol_price(symbol)

            return price

        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    @staticmethod
    def _calculate_start_time(
        start_time: datetime | None, limit: int, timeframe: str
    ) -> datetime:
        """Calculate start time for historical data request."""
        if start_time:
            return start_time

        # Calculate default start time based on limit and timeframe
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
        return datetime.now() - timedelta(minutes=minutes * limit)

    @staticmethod
    @retry_on_error(max_retries=3, initial_delay=1.0)
    async def get_candles(
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
            connection = MetaApiConnection.get_connection()

            # Convert timeframe if needed
            if timeframe in MetaApiData.TIMEFRAMES:
                timeframe = MetaApiData.TIMEFRAMES[timeframe]

            # Calculate start time
            calculated_start = MetaApiData._calculate_start_time(
                start_time, limit, timeframe
            )

            logger.debug(
                f"Fetching candles: {symbol} {timeframe} from {calculated_start}"
            )

            with latency_monitor.measure("get_candles"):
                candles = await connection.get_candles(
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

        # Ensure OHLCV columns exist
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"Column '{col}' not in candles data")

        df.sort_index(inplace=True)
        return df

    @staticmethod
    async def get_candles_as_dataframe(
        symbol: str,
        timeframe: str = "H1",
        start_time: datetime | None = None,
        limit: int = 1000,
    ) -> pd.DataFrame | None:
        """Get historical candles as DataFrame."""
        candles = await MetaApiData.get_candles(symbol, timeframe, start_time, limit)

        if not candles:
            return None

        try:
            df = MetaApiData._convert_candles_to_dataframe(candles)
            logger.debug(f"Converted {len(df)} candles to DataFrame for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to convert candles to DataFrame: {e}")
            return None

    @staticmethod
    @retry_on_error(max_retries=2, initial_delay=0.5)
    async def get_ticks(
        symbol: str, start_time: datetime | None = None, limit: int = 1000
    ) -> list[dict] | None:
        """Get historical ticks."""
        rate_limiter = get_rate_limiter()
        latency_monitor = get_latency_monitor()

        await rate_limiter.await_if_needed()

        try:
            connection = MetaApiConnection.get_connection()

            if not start_time:
                start_time = datetime.now() - timedelta(hours=1)

            logger.debug(f"Fetching ticks: {symbol} from {start_time}")

            with latency_monitor.measure("get_ticks"):
                ticks = await connection.get_ticks(
                    symbol=symbol, start_time=start_time, limit=limit
                )

            logger.info(f"Retrieved {len(ticks) if ticks else 0} ticks for {symbol}")
            return ticks

        except Exception as e:
            logger.error(f"Failed to get ticks for {symbol}: {e}")
            return None

    @staticmethod
    async def subscribe_to_market_data(symbol: str) -> bool:
        """Subscribe to real-time market data for a symbol."""
        latency_monitor = get_latency_monitor()

        try:
            connection = MetaApiConnection.get_connection()

            with latency_monitor.measure("subscribe_market_data"):
                await connection.subscribe_to_market_data(symbol)

            logger.info(f"Subscribed to market data for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe to market data for {symbol}: {e}")
            return False


# Synchronous wrappers
def get_symbol_info_sync(symbol: str) -> dict | None:
    """Synchronous wrapper for get_symbol_info."""
    return asyncio.run(MetaApiData.get_symbol_info(symbol))


def get_symbol_price_sync(symbol: str) -> dict | None:
    """Synchronous wrapper for get_symbol_price."""
    return asyncio.run(MetaApiData.get_symbol_price(symbol))


def get_candles_sync(
    symbol: str, timeframe: str = "H1", start_time=None, limit: int = 1000
) -> list[dict] | None:
    """Synchronous wrapper for get_candles."""
    return asyncio.run(MetaApiData.get_candles(symbol, timeframe, start_time, limit))


def get_candles_as_dataframe_sync(
    symbol: str, timeframe: str = "H1", start_time=None, limit: int = 1000
) -> pd.DataFrame | None:
    """Synchronous wrapper for get_candles_as_dataframe."""
    return asyncio.run(
        MetaApiData.get_candles_as_dataframe(symbol, timeframe, start_time, limit)
    )
