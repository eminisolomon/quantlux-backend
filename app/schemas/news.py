from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import Impact


class NewsEvent(BaseModel):
    """Economic news event model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    country: str
    currency: str
    impact: Impact  # High, Medium, Low
    time: datetime
    forecast: str
    previous: str
    actual: str = ""
