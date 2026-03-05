from app.schemas import AccountInfo, SymbolInfo
from app.risk.sizing.core import normalize_volume
from app.utils.logger import logger


def calculate_risk_lot(
    account: AccountInfo,
    symbol_info: SymbolInfo,
    risk_pct: float,
    sl_pips: float,
) -> float:
    """Calculate lot size based on percentage risk and Stop Loss distance."""
    if risk_pct <= 0 or sl_pips <= 0:
        logger.error(f"Invalid risk parameters: risk={risk_pct}%, sl={sl_pips}")
        return 0.0

    if account.equity <= 0:
        logger.error("Account equity is zero or negative.")
        return 0.0

    risk_amount = account.equity * (risk_pct / 100.0)

    tick_value = symbol_info.trade_tick_value
    if tick_value == 0:
        tick_value = symbol_info.trade_tick_value_profit

        if tick_value == 0:
            logger.warning(
                f"Trade tick value is 0 for {symbol_info.name}. Falling back to minimum lot size."
            )
            return symbol_info.volume_min

    tick_size = symbol_info.trade_tick_size
    point = symbol_info.point

    if tick_size == 0 or point == 0:
        logger.error(
            f"Invalid tick_size ({tick_size}) or point ({point}) for {symbol_info.name}"
        )
        return symbol_info.volume_min

    point_value = tick_value * (point / tick_size)

    loss_per_lot = sl_pips * point_value

    if loss_per_lot == 0:
        logger.warning("Loss per lot is 0. Using minimum lot size.")
        return symbol_info.volume_min

    raw_lot = risk_amount / loss_per_lot

    lot = normalize_volume(raw_lot, symbol_info)

    logger.info(
        f"Position Size Calculation for {symbol_info.name}:\n"
        f"  Risk Amount: {risk_amount:.2f} {account.currency}\n"
        f"  SL Distance: {sl_pips} points\n"
        f"  Point Value: {point_value:.5f}\n"
        f"  Loss Per Lot: {loss_per_lot:.2f}\n"
        f"  Raw Lot: {raw_lot:.4f}\n"
        f"  Normalized Lot: {lot:.2f}"
    )

    return lot


def calculate_fixed_lot(
    symbol_info: SymbolInfo,
    fixed_lot: float,
) -> float:
    """Calculate position size using a fixed lot size."""
    if fixed_lot <= 0:
        logger.error(f"Invalid fixed lot size: {fixed_lot}")
        return symbol_info.volume_min

    lot = normalize_volume(fixed_lot, symbol_info)
    logger.info(f"Fixed Lot: {lot}")

    return lot


def calculate_percent_equity_lot(
    account: AccountInfo,
    symbol_info: SymbolInfo,
    equity_pct: float,
) -> float:
    """Calculate lot size as a percentage of equity."""
    if equity_pct <= 0 or equity_pct > 100:
        logger.error(f"Invalid equity percentage: {equity_pct}%")
        return 0.0

    if account.equity <= 0:
        logger.error("Account equity is zero or negative.")
        return 0.0

    allocation = account.equity * (equity_pct / 100.0)

    contract_size = symbol_info.trade_contract_size
    current_price = (symbol_info.bid + symbol_info.ask) / 2

    if contract_size == 0 or current_price == 0:
        logger.error(
            f"Invalid contract_size ({contract_size}) or price ({current_price})"
        )
        return symbol_info.volume_min

    raw_lot = allocation / (contract_size * current_price)

    lot = normalize_volume(raw_lot, symbol_info)

    logger.info(
        f"Percent Equity Sizing for {symbol_info.name}:\n"
        f"  Equity: {account.equity:.2f}\n"
        f"  Allocation: {allocation:.2f} ({equity_pct}%)\n"
        f"  Calculated Lot: {lot:.2f}"
    )

    return lot


def calculate_kelly_lot(
    account: AccountInfo,
    symbol_info: SymbolInfo,
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    sl_pips: float,
    kelly_fraction: float = 0.25,
) -> float:
    """Calculate lot size using the Kelly Criterion."""
    if not (0 <= win_rate <= 1):
        logger.error(f"Invalid win rate: {win_rate}. Must be between 0 and 1.")
        return 0.0

    if avg_win <= 0 or avg_loss <= 0:
        logger.error(f"Invalid avg_win ({avg_win}) or avg_loss ({avg_loss})")
        return 0.0

    if account.equity <= 0:
        logger.error("Account equity is zero or negative.")
        return 0.0

    win_loss_ratio = avg_win / avg_loss

    kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)

    kelly_pct *= kelly_fraction

    if kelly_pct <= 0:
        logger.warning(f"Kelly Criterion suggests no trade (Kelly %: {kelly_pct:.2%})")
        return 0.0

    max_kelly = 0.25
    if kelly_pct > max_kelly:
        logger.warning(
            f"Kelly % ({kelly_pct:.2%}) exceeds maximum ({max_kelly:.2%}). "
            f"Capping at {max_kelly:.2%}."
        )
        kelly_pct = max_kelly

    lot = calculate_risk_lot(account, symbol_info, kelly_pct * 100, sl_pips)

    logger.info(
        f"Kelly Criterion Sizing:\n"
        f"  Win Rate: {win_rate:.2%}\n"
        f"  Win/Loss Ratio: {win_loss_ratio:.2f}\n"
        f"  Kelly %: {kelly_pct:.2%}\n"
        f"  Calculated Lot: {lot:.2f}"
    )

    return lot
