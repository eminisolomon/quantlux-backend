import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Numeric, DateTime
from app.db.base import Base


class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC),
        index=True,
    )
    equity: Mapped[float] = mapped_column(Numeric(12, 2))
    balance: Mapped[float] = mapped_column(Numeric(12, 2))
    margin_used: Mapped[float] = mapped_column(Numeric(12, 2))
    free_margin: Mapped[float] = mapped_column(Numeric(12, 2))
