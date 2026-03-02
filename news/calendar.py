from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict
import httpx
from bs4 import BeautifulSoup

from app.core.enums import Impact
from app.core import messages as msg
from app.core.settings import settings
from app.utils.logger import logger


from app.models import NewsEvent


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
            date = datetime.now()

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

        events = []
        if not table:
            return events

        year = date.year

        rows = table.find_all("tr", class_=["calendar__row", "calendar_row"])

        current_time_str = "00:00"

        for row in rows:
            try:
                if "calendar__row--new-day" in row.get("class", []):
                    continue

                currency_cell = row.find("td", class_="calendar__currency")
                if not currency_cell:
                    continue
                currency = currency_cell.text.strip()

                impact_cell = row.find("td", class_="calendar__impact")
                impact_span = impact_cell.find("span") if impact_cell else None
                impact_classes = (
                    str(impact_span.get("class", [])) if impact_span else ""
                )

                if "impact-red" in impact_classes:
                    impact = Impact.HIGH
                elif "impact-orange" in impact_classes:
                    impact = Impact.MEDIUM
                elif "impact-yellow" in impact_classes:
                    impact = Impact.LOW
                else:
                    impact = Impact.NONE

                title_cell = row.find("td", class_="calendar__event")
                title = title_cell.text.strip() if title_cell else "Unknown"

                time_cell = row.find("td", class_="calendar__time")
                if time_cell and time_cell.text.strip():
                    current_time_str = time_cell.text.strip()

                event_time = self._parse_time(current_time_str, date)

                actual = row.find("td", class_="calendar__actual").text.strip()
                forecast = row.find("td", class_="calendar__forecast").text.strip()
                previous = row.find("td", class_="calendar__previous").text.strip()

                event = NewsEvent(
                    id=row.get("data-event-id", ""),
                    title=title,
                    country=currency[:2] if len(currency) >= 2 else "Global",
                    currency=currency,
                    impact=impact,
                    time=event_time,
                    forecast=forecast,
                    previous=previous,
                    actual=actual,
                )
                events.append(event)

            except Exception:
                continue

        return events

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
        now = datetime.now()
        events_today = await self.get_calendar(now)
        events_tomorrow = await self.get_calendar(now + timedelta(days=1))
        events = events_today + events_tomorrow

        high_impact = [
            e
            for e in events
            if e.impact == Impact.HIGH and now < e.time < now + timedelta(hours=hours)
        ]
        return high_impact
