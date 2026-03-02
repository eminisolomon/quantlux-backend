from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TickData(BaseModel):
    """Standardized real-time market tick data."""

    model_config = ConfigDict(populate_by_name=True)

    symbol: str
    bid: float
    ask: float
    time: datetime = Field(default_factory=datetime.now)

    @property
    def spread(self) -> float:
        """Calculate current spread in price units."""
        return round(self.ask - self.bid, 5)

    @property
    def mid(self) -> float:
        """Calculate mid price."""
        return round((self.ask + self.bid) / 2, 5)
