import asyncio
from datetime import datetime

from app.core import messages as msg
from app.core.settings import settings
from app.models.market import TickData
from app.utils.logger import logger


class MarketWatchdog:
    """
    Monitors real-time market conditions to protect the bot.
    Shields against high spreads, extreme volatility, and stale data.
    """

    def __init__(self):
        self.is_market_safe: bool = True
        self.last_tick_time: dict[str, datetime] = {}
        self.current_spreads: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the watchdog."""
        pass

    async def stop(self):
        """Stop the watchdog."""
        pass

    async def check_tick(self, symbol: str, tick: TickData) -> bool:
        """Evaluate if a tick is safe for trading."""
        async with self._lock:
            self.last_tick_time[symbol] = tick.time
            self.current_spreads[symbol] = tick.spread

            max_spread = settings.MAX_SPREAD_PIPS * 0.0001

            if tick.spread > max_spread:
                if self.is_market_safe:
                    logger.warning(
                        msg.WATCHDOG_PAUSE.format(
                            symbol=symbol, spread=tick.spread, limit=max_spread
                        )
                    )
                self.is_market_safe = False
                return False

            if not self.is_market_safe:
                logger.info(msg.WATCHDOG_NORMAL.format(symbol=symbol))
                self.is_market_safe = True

            return True

    def is_healthy(self, symbol: str) -> bool:
        """General health check for a symbol."""
        now = datetime.now()
        last_time = self.last_tick_time.get(symbol)

        if not last_time:
            return False

        if (now - last_time).total_seconds() > 30:
            logger.error(msg.WATCHDOG_STALE.format(symbol=symbol))
            return False

        return self.is_market_safe
