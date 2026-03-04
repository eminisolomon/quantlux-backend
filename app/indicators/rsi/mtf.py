"""Multi-Timeframe RSI Analysis."""

from app.core.enums import SignalAction
from app.indicators.rsi.calculator import ModernRSI
from app.indicators.rsi.config import RSIConfig

from app.utils.logger import logger


class MultiTimeframeRSI:
    """Calculate RSI across multiple timeframes for confirmation."""

    def __init__(self, config: RSIConfig | None = None):
        self.rsi_calculator = ModernRSI(config)

    async def analyze_timeframes(
        self, symbol: str, timeframes: list[str]
    ) -> dict[str, dict]:
        """Analyze RSI across multiple timeframes."""

        from app.core.di import container
        from app.services.market_data_service import MarketDataService

        data_service = container.resolve(MarketDataService)
        results = {}

        for tf in timeframes:
            try:
                # Get candles for this timeframe
                df = await data_service.get_candles_as_dataframe(symbol, tf, limit=100)

                if df is None or df.empty:
                    logger.warning(f"No data for {symbol} {tf}")
                    continue

                # Calculate RSI
                rsi_series = self.rsi_calculator.calculate(df["close"])
                current_rsi = rsi_series.iloc[-1] if not rsi_series.empty else None

                if current_rsi is not None:
                    results[tf] = {
                        "rsi": float(current_rsi),
                        "signal": self.rsi_calculator.get_signal(current_rsi),
                        "prev_rsi": (
                            float(rsi_series.iloc[-2]) if len(rsi_series) > 1 else None
                        ),
                    }

            except Exception as e:
                logger.error(f"Error calculating RSI for {symbol} {tf}: {e}")

        return results

    def get_consensus_signal(self, mtf_results: dict[str, dict]) -> SignalAction:
        """Get consensus signal from multiple timeframes."""
        if not mtf_results:
            return SignalAction.HOLD

        signals = [result["signal"] for result in mtf_results.values()]

        buy_count = signals.count(SignalAction.BUY)
        sell_count = signals.count(SignalAction.SELL)

        # Require majority (>50%) agreement
        threshold = len(signals) / 2

        if buy_count > threshold:
            return SignalAction.BUY
        elif sell_count > threshold:
            return SignalAction.SELL

        return SignalAction.HOLD
