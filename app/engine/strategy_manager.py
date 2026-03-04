"""Enhanced Strategy Manager."""

from typing import Any

from app.core import messages as msg
from app.core.enums import Timeframe
from app.metaapi.adapter import MetaApiAdapter
from app.strategies.adapter import StrategyAdapter, UnifiedSignal
from app.strategies.base import BaseStrategy
from app.utils.logger import logger


class StrategyManager:
    """Strategy Manager supporting legacy and high-accuracy strategies."""

    def __init__(self, metaapi: MetaApiAdapter):
        self.metaapi = metaapi
        self.strategies: dict[str, list[BaseStrategy]] = {}
        self.strategy_adapters: dict[str, StrategyAdapter] = {}

    def add_strategy(self, symbol: str, strategy: BaseStrategy) -> None:
        """Add core strategy."""
        if symbol not in self.strategies:
            self.strategies[symbol] = []
        self.strategies[symbol].append(strategy)
        logger.info(msg.STRATEGY_ADDED.format(symbol=symbol))

    def add_high_accuracy_strategies(
        self, symbol: str, primary_timeframe: str = "H4"
    ) -> None:
        """Add ICT + Mean Reversion strategies."""
        if symbol not in self.strategy_adapters:
            adapter = StrategyAdapter(
                symbol=symbol, primary_timeframe=primary_timeframe
            )
            self.strategy_adapters[symbol] = adapter
            logger.info(msg.STRATEGY_ACC_ADDED.format(symbol=symbol))

    async def process_tick(
        self, symbol: str, tick: dict[str, Any]
    ) -> list[tuple[Any, BaseStrategy]]:
        """Process tick for legacy strategies."""
        signals = []

        if symbol in self.strategies:
            for strategy in self.strategies[symbol]:
                try:
                    if not strategy.check_risk():
                        continue

                    signal = await strategy.process_tick(tick)
                    if signal:
                        signals.append((signal, strategy))
                except Exception as e:
                    logger.error(
                        msg.STRATEGY_ERROR.format(
                            name=strategy.__class__.__name__, error=e
                        )
                    )

        return signals

    async def analyze_high_accuracy(self, symbol: str) -> UnifiedSignal | None:
        """Analyze with high-accuracy strategies."""
        if symbol not in self.strategy_adapters:
            return None

        adapter = self.strategy_adapters[symbol]
        confluence_signal = await adapter.check_confluence()

        if confluence_signal:
            return confluence_signal
        return await adapter.analyze()

    async def get_all_signals(self, symbol: str) -> dict[str, Any]:
        """Get all signals from all strategies for a symbol."""
        all_signals = {"legacy": [], "high_accuracy": None, "confluence": False}

        await self._get_legacy_signals(symbol, all_signals)
        await self._get_high_accuracy_signals(symbol, all_signals)

        return all_signals

    async def _get_legacy_signals(
        self, symbol: str, all_signals: dict[str, Any]
    ) -> None:
        """Fetch and process signals for legacy strategies."""
        if symbol not in self.strategies:
            return

        try:
            df = await self.metaapi.get_candles_as_dataframe(
                symbol, timeframe=Timeframe.H1.value, limit=100
            )

            if df is not None and not df.empty:
                for strategy in self.strategies[symbol]:
                    try:
                        self._process_single_legacy_strategy(strategy, df, all_signals)
                    except Exception as e:
                        logger.error(
                            msg.STRATEGY_CALC_ERROR.format(
                                name=strategy.__class__.__name__, error=e
                            )
                        )
        except Exception as e:
            logger.error(msg.STRATEGY_FETCH_ERROR.format(error=e))

    def _process_single_legacy_strategy(
        self, strategy: BaseStrategy, df: Any, all_signals: dict[str, Any]
    ) -> None:
        """Process a single legacy strategy."""
        df_analyzed = strategy.calculate_signals(df.copy())
        last_row = df_analyzed.iloc[-1]
        signal_val = last_row.get("signal") or last_row.get("position")

        if signal_val:
            all_signals["legacy"].append(
                {
                    "strategy": strategy.__class__.__name__,
                    "signal": signal_val,
                    "params": strategy.params,
                }
            )

    async def _get_high_accuracy_signals(
        self, symbol: str, all_signals: dict[str, Any]
    ) -> None:
        """Process signals for high-accuracy strategies."""
        if symbol not in self.strategy_adapters:
            return

        adapter = self.strategy_adapters[symbol]
        confluence_signal = await adapter.check_confluence()

        if confluence_signal:
            all_signals["high_accuracy"] = confluence_signal
            all_signals["confluence"] = True
        else:
            all_signals["high_accuracy"] = await adapter.analyze()

    def set_strategy_active(self, symbol: str, strategy_name: str, active: bool):
        """Enable/disable a specific strategy."""
        if symbol in self.strategy_adapters:
            self.strategy_adapters[symbol].set_strategy_active(strategy_name, active)
