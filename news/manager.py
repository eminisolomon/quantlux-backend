import asyncio
from datetime import datetime, timedelta

from app.core.decorators import retry_on_error
from app.core.enums import Impact
from app.core import messages as msg
from app.core.settings import settings
from app.utils.logger import logger
from app.schemas import NewsEvent
from news.calendar import EconomicCalendar


class NewsManager:
    """Manages economic news events and trading availability."""

    def __init__(self):
        self.calendar = EconomicCalendar()
        self.events: list[NewsEvent] = []
        self.last_update: datetime | None = None
        self._update_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start background update tasks."""
        if not settings.ENABLE_NEWS_FILTER:
            logger.info(msg.NEWS_FILTER_DISABLED)
            return

        logger.info(msg.NEWS_START)
        await self._update_calendar()
        self._update_task = asyncio.create_task(self._periodic_update())

    async def stop(self):
        """Stop background tasks."""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None

    async def _periodic_update(self):
        """Periodically refresh calendar (every 6h)."""
        while True:
            try:
                await asyncio.sleep(6 * 60 * 60)
                await self._update_calendar()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(msg.NEWS_UPDATE_ERROR.format(error=e))
                await asyncio.sleep(60)

    @retry_on_error(max_retries=3, initial_delay=300)
    async def _update_calendar(self):
        """Refresh internal events cache."""
        async with self._lock:
            today = datetime.now()
            events_today = await self.calendar.get_calendar(today)
            events_tomorrow = await self.calendar.get_calendar(
                today + timedelta(days=1)
            )

            all_events = events_today + events_tomorrow
            allowed_impacts = [Impact(i) for i in settings.NEWS_IMPACT_FILTER]

            self.events = [e for e in all_events if e.impact in allowed_impacts]
            self.last_update = datetime.now()

            logger.info(msg.NEWS_UPDATED.format(count=len(self.events)))

    def should_trade(self, symbol: str) -> bool:
        """Check if trading is allowed based on news window."""
        if not settings.ENABLE_NEWS_FILTER:
            return True

        currencies = self._get_relevant_currencies(symbol)

        now = datetime.now()

        for event in self.events:
            if event.currency not in currencies and event.currency != "All":
                continue
            start_pause = event.time - timedelta(
                minutes=settings.NEWS_PAUSE_MINUTES_BEFORE
            )
            end_pause = event.time + timedelta(
                minutes=settings.NEWS_PAUSE_MINUTES_AFTER
            )

            if start_pause <= now <= end_pause:
                logger.warning(
                    msg.TRADING_PAUSED_NEWS.format(
                        symbol=symbol,
                        impact=event.impact,
                        currency=event.currency,
                        title=event.title,
                        time=event.time.strftime("%H:%M"),
                    )
                )
                return False

        return True

    def _get_relevant_currencies(self, symbol: str) -> list[str]:
        """Extract relevant currencies from a symbol."""
        symbol = symbol.upper()

        if len(symbol) == 6:
            return [symbol[:3], symbol[3:]]

        if "BTC" in symbol:
            return ["USD"]
        if "ETH" in symbol:
            return ["USD"]
        if "XAU" in symbol:
            return ["USD", "EUR"]

        return ["USD", "EUR", "GBP", "JPY"]
