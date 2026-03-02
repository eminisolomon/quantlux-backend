"""Schemas package - consolidated imports."""

from app.models.analytics import (
    AverageTradeStats,
    DrawdownInfo,
    PerformanceReport,
    PerformanceStats,
    Trade,
)
from app.models.market import TickData
from app.models.metaapi import (
    AccountInfo,
    OrderSendResult,
    SymbolInfo,
    TerminalInfo,
    TradeOrder,
    TradePosition,
    TradeRequest,
)
from app.models.news import NewsEvent
from app.models.signal import TradeSignal
from app.models.rsi import RSISignal

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
