from app.schemas import SymbolInfo
from app.utils.logger import logger


def normalize_volume(volume: float, symbol_info: SymbolInfo) -> float:
    """Normalize volume to symbol's step size and limits."""
    step = symbol_info.volume_step
    min_vol = symbol_info.volume_min
    max_vol = symbol_info.volume_max

    if step > 0:
        volume = round(volume / step) * step

    if volume < min_vol:
        logger.debug(f"Volume {volume:.2f} below minimum. Setting to {min_vol}")
        volume = min_vol

    if max_vol > 0 and volume > max_vol:
        logger.warning(f"Volume {volume:.2f} exceeds maximum. Capping at {max_vol}")
        volume = max_vol

    # Round to 2 decimal places for cleaner output
    return round(volume, 2)


def calculate_pip_value(
    symbol_info: SymbolInfo,
    lot_size: float = 1.0,
) -> float:
    """Calculate the monetary value of one pip for a given lot size."""
    tick_value = symbol_info.trade_tick_value
    tick_size = symbol_info.trade_tick_size
    point = symbol_info.point

    if tick_size == 0 or point == 0:
        logger.error("Invalid tick_size or point value")
        return 0.0

    standard_pip = 0.0001 if symbol_info.digits == 5 else 0.01
    pip_in_points = standard_pip / point

    point_value = tick_value * (point / tick_size)
    pip_value = point_value * pip_in_points * lot_size

    return pip_value


def calculate_margin_required(
    symbol_info: SymbolInfo,
    lot_size: float,
    leverage: int,
) -> float | None:
    """Estimate margin required for a position."""
    if leverage <= 0:
        logger.error(f"Invalid leverage: {leverage}")
        return None

    contract_size = symbol_info.trade_contract_size
    current_price = (symbol_info.bid + symbol_info.ask) / 2

    if contract_size == 0 or current_price == 0:
        logger.error("Invalid contract_size or price")
        return None

    margin = (lot_size * contract_size * current_price) / leverage

    return margin
