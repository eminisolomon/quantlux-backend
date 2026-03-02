import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, DateTime, Boolean
from app.db.base import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticket: Mapped[str] = mapped_column(String, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String, index=True)
    side: Mapped[str] = mapped_column(String)  # BUY or SELL
    volume: Mapped[float] = mapped_column(Numeric(10, 4))
    open_price: Mapped[float] = mapped_column(Numeric(10, 5))
    close_price: Mapped[float | None] = mapped_column(Numeric(10, 5), nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Numeric(10, 5), nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Numeric(10, 5), nullable=True)
    profit: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    open_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    close_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    strategy_id: Mapped[str | None] = mapped_column(String, nullable=True)
