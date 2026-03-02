"""Mappers for translating raw MetaApi data into domain models."""

from typing import Any

from app.core.enums import AccountType, SignalAction
from app.models.metaapi import (
    AccountInfo,
    SymbolInfo,
    TradeOrder,
    TradePosition,
)


def map_account_type(v: Any) -> AccountType | None:
    """Map MetaApi account type strings to AccountType Enum."""
    if v is None:
        return None
    if isinstance(v, AccountType):
        return v
    if not isinstance(v, str):
        return None

    v_lower = v.lower()
    if "demo" in v_lower:
        return AccountType.DEMO
    if "real" in v_lower:
        return AccountType.REAL
    return None


def map_signal_action(v: Any) -> SignalAction:
    """Map MetaApi position/order type strings to SignalAction Enum."""
    if isinstance(v, SignalAction):
        return v
    if not isinstance(v, str):
        return SignalAction.HOLD

    v_upper = v.upper()
    if "BUY" in v_upper:
        return SignalAction.BUY
    if "SELL" in v_upper:
        return SignalAction.SELL
    return SignalAction.HOLD


def map_account_info(data: dict[str, Any]) -> AccountInfo:
    """
    Map raw MetaApi account information to the AccountInfo domain model.
    """
    # Create a copy to avoid mutating the original
    mapped = data.copy()

    # Handle Enum translation
    mapped["type"] = map_account_type(data.get("type"))

    # Ensure trade_allowed exists (from research: tradeAllowed in raw API)
    if "tradeAllowed" in mapped and "trade_allowed" not in mapped:
        mapped["trade_allowed"] = mapped["tradeAllowed"]

    return AccountInfo(**mapped)


def map_symbol_info(symbol: str, info: dict[str, Any]) -> SymbolInfo:
    """
    Map raw MetaApi symbol specifications to the SymbolInfo domain model.
    """
    return SymbolInfo(
        symbol=symbol,
        description=info.get("description"),
        digits=info.get("digits", 5),
        point=info.get("point", 0.00001),
        contract_size=info.get("contractSize"),
        volume_min=info.get("volumeMin", 0.01),
        volume_max=info.get("volumeMax", 100.0),
        volume_step=info.get("volumeStep", 0.01),
        trade_mode=info.get("tradeMode"),
        currency_base=info.get("baseCurrency"),
        currency_profit=info.get("profitCurrency"),
        currency_margin=info.get("marginCurrency"),
        bid=info.get("bid"),
        ask=info.get("ask"),
        spread=info.get("spread"),
    )


def map_trade_position(data: dict[str, Any]) -> TradePosition:
    """
    Map raw MetaApi position data to the TradePosition domain model.
    """
    mapped = data.copy()

    # Handle type mapping
    if "type" in mapped:
        mapped["type"] = map_signal_action(mapped["type"])

    return TradePosition(**mapped)


def map_trade_order(data: dict[str, Any]) -> TradeOrder:
    """
    Map raw MetaApi order data to the TradeOrder domain model.
    """
    mapped = data.copy()

    # Handle type mapping
    if "type" in mapped:
        mapped["type"] = map_signal_action(mapped["type"])

    return TradeOrder(**mapped)
