from app.schemas import AccountInfo, SymbolInfo
from app.risk.sizing.core import normalize_volume
from app.risk.sizing.strategies import calculate_risk_lot
from app.utils.logger import logger


def calculate_atr_lot(
    account: AccountInfo,
    symbol_info: SymbolInfo,
    risk_pct: float,
    atr_value: float,
    atr_multiplier: float = 2.0,
) -> float:
    """Calculate lot size using ATR for stop loss."""
    if atr_value <= 0:
        logger.error(f"Invalid ATR value: {atr_value}")
        return 0.0

    sl_distance_price = atr_value * atr_multiplier
    sl_pips = sl_distance_price / symbol_info.point

    logger.info(
        f"ATR-Based Sizing:\n"
        f"  ATR Value: {atr_value:.5f}\n"
        f"  ATR Multiplier: {atr_multiplier}\n"
        f"  SL Distance: {sl_pips:.1f} points"
    )

    return calculate_risk_lot(account, symbol_info, risk_pct, sl_pips)


def calculate_volatility_adjusted_lot(
    account: AccountInfo,
    symbol_info: SymbolInfo,
    base_lot: float,
    symbol_name: str | None = None,
    target_volatility: float = 0.02,
) -> float:
    """Calculate volatility-adjusted position size."""

    final_lot = normalize_volume(base_lot, symbol_info)

    logger.debug(
        f"Volatility adjustment disabled. Normalized lot: {base_lot:.2f} -> {final_lot:.2f}"
    )

    return final_lot
