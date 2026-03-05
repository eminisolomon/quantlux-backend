import asyncio
from datetime import datetime, timedelta, timezone
import httpx
from bs4 import BeautifulSoup

from app.core.decorators import retry_on_error
from app.core.enums import Impact
from app.core import messages as msg
from app.core.settings import settings
from app.utils.logger import logger
from app.schemas import NewsEvent


class EconomicCalendar:
    """Fetches economic calendar data from ForexFactory."""

    BASE_URL = settings.FOREXFACTORY_BASE_URL

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def get_calendar(self, date: datetime | None = None) -> list[NewsEvent]:
        """Fetch economic calendar events."""
        logger.info(msg.NEWS_FETCHING)
        if date is None:
            date = datetime.now(timezone.utc)

        date_str = date.strftime("%b%d.%Y").lower()
        url = self.BASE_URL.format(date_str)

        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    logger.error(
                        msg.NEWS_FETCH_FAILED.format(status_code=response.status_code)
                    )
                    return []

                return self._parse_html(response.text, date)

        except Exception as e:
            logger.error(msg.NEWS_ERROR.format(error=e))
            return []

    def _parse_html(self, html: str, date: datetime) -> list[NewsEvent]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="calendar__table")
        if not table:
            return []

        rows = table.find_all("tr", class_=["calendar__row", "calendar_row"])
        events = []
        current_time_str = "00:00"

        for row in rows:
            try:
                if "calendar__row--new-day" in row.get("class", []):
                    continue

                currency_cell = row.find("td", class_="calendar__currency")
                if not currency_cell:
                    continue

                time_cell = row.find("td", class_="calendar__time")
                if time_cell and time_cell.text.strip():
                    current_time_str = time_cell.text.strip()

                event = self._build_event(row, date, current_time_str)
                if event:
                    events.append(event)
            except Exception:
                continue

        return events

    def _build_event(self, row, date: datetime, time_str: str) -> NewsEvent | None:
        """Build a NewsEvent from a calendar table row."""
        try:
            currency = row.find("td", class_="calendar__currency").text.strip()
            title_cell = row.find("td", class_="calendar__event")
            title = title_cell.text.strip() if title_cell else "Unknown"

            return NewsEvent(
                id=row.get("data-event-id", ""),
                title=title,
                country=currency[:2] if len(currency) >= 2 else "Global",
                currency=currency,
                impact=self._extract_impact(row),
                time=self._extract_event_time(time_str, date),
                forecast=row.find("td", class_="calendar__forecast").text.strip(),
                previous=row.find("td", class_="calendar__previous").text.strip(),
                actual=row.find("td", class_="calendar__actual").text.strip(),
            )
        except Exception:
            return None

    def _extract_impact(self, row) -> Impact:
        """Determine the impact level from a row's impact span classes."""
        impact_cell = row.find("td", class_="calendar__impact")
        impact_span = impact_cell.find("span") if impact_cell else None
        classes = str(impact_span.get("class", [])) if impact_span else ""

        if "impact-red" in classes:
            return Impact.HIGH
        if "impact-orange" in classes:
            return Impact.MEDIUM
        if "impact-yellow" in classes:
            return Impact.LOW
        return Impact.NONE

    def _extract_event_time(self, time_str: str, date: datetime) -> datetime:
        """Parse a calendar time string into a full datetime."""
        return self._parse_time(time_str, date)

    def _parse_time(self, time_str: str, date: datetime) -> datetime:
        """Parses a time string into a datetime object."""
        try:
            if "Day" in time_str or "Tentative" in time_str:
                return date.replace(hour=0, minute=0)

            t = datetime.strptime(time_str, "%I:%M%p")
            return date.replace(hour=t.hour, minute=t.minute)
        except:
            return date

    async def get_upcoming_high_impact(self, hours: int = 24) -> list[NewsEvent]:
        """Fetches high impact news for the upcoming hours."""
        now = datetime.now(timezone.utc)
        events_today = await self.get_calendar(now)
        events_tomorrow = await self.get_calendar(now + timedelta(days=1))
        events = events_today + events_tomorrow

        high_impact = [
            e
            for e in events
            if e.impact == Impact.HIGH and now < e.time < now + timedelta(hours=hours)
        ]
        return high_impact


class NewsService:
    """Service that manages economic news events and determines trading availability based on the calendar."""

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
            today = datetime.now(timezone.utc)
            events_today = await self.calendar.get_calendar(today)
            events_tomorrow = await self.calendar.get_calendar(
                today + timedelta(days=1)
            )

            all_events = events_today + events_tomorrow
            allowed_impacts = [Impact(i) for i in settings.NEWS_IMPACT_FILTER]

            self.events = [e for e in all_events if e.impact in allowed_impacts]
            self.last_update = datetime.now(timezone.utc)

            logger.info(msg.NEWS_UPDATED.format(count=len(self.events)))

    def should_trade(self, symbol: str) -> bool:
        """Check if trading is allowed based on news window."""
        if not settings.ENABLE_NEWS_FILTER:
            return True

        currencies = self._get_relevant_currencies(symbol)

        now = datetime.now(timezone.utc)

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
