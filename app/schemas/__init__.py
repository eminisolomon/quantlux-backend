"""Schemas package - consolidated imports."""

from app.schemas.analytics import (
    AverageTradeStats,
    DrawdownInfo,
    PerformanceReport,
    PerformanceStats,
    Trade,
)
from app.schemas.market import TickData
from app.schemas.metaapi import (
    AccountInfo,
    OrderSendResult,
    SymbolInfo,
    TerminalInfo,
    TradeOrder,
    TradePosition,
    TradeRequest,
)
from app.schemas.news import NewsEvent
from app.schemas.signal import TradeSignal
from app.schemas.rsi import RSISignal

__all__ = [
    "AccountInfo",
    "SymbolInfo",
    "TradeRequest",
    "OrderSendResult",
    "TradePosition",
    "TradeOrder",
    "TerminalInfo",
    "Trade",
    "DrawdownInfo",
    "AverageTradeStats",
    "PerformanceStats",
    "PerformanceReport",
    "NewsEvent",
    "TickData",
    "TradeSignal",
    "RSISignal",
]
