"""Core Strategy Adapter Logic."""

from datetime import datetime
from typing import Any

from app.metaapi.data import get_candles_as_dataframe_sync
from app.strategies.adapter.models import UnifiedSignal
from app.strategies.mean_rev import (
    EnhancedMeanReversionStrategy,
    MeanReversionSignal,
)
from app.strategies.momentum import MomentumSignal, MomentumStrategy
from app.schemas import RSISignal
from app.strategies.smc import ICTSignal, SmartMoneyStrategy
from app.utils.logger import logger
from app.strategies.rsi.strategy import RSIStrategy


class StrategyAdapter:
    """Adapter to integrate strategies with MetaApi and trading bot."""

    def __init__(self, symbol: str, primary_timeframe: str = "H4"):
        """Initialize strategy adapter."""
        self.symbol = symbol
        self.primary_timeframe = primary_timeframe

        # Initialize strategies
        self.ict = SmartMoneyStrategy(
            symbol=symbol,
            timeframe=primary_timeframe,
            min_risk_reward=2.0,
            min_confidence=75.0,
        )

        self.mr_strategy = EnhancedMeanReversionStrategy(
            symbol=symbol,
            timeframe="H1",
            min_confidence=70.0,
            min_risk_reward=2.0,
        )

        self.rsi_strategy = RSIStrategy(
            symbol=symbol,
            timeframe="H1",
            min_confidence=70.0,
            min_risk_reward=2.0,
        )

        self.momentum_strategy = MomentumStrategy(
            symbol=symbol,
            timeframe="H1",
            min_confidence=70.0,
            min_risk_reward=2.0,
        )

        from app.engine.regime import MarketRegimeDetector

        self.regime_detector = MarketRegimeDetector(adx_period=14, adx_threshold=25.0)

        # Active strategies
        self.active_strategies = {
            "smart_money": True,
            "mean_reversion": True,
            "rsi": True,
            "momentum": True,
        }

    def _update_regime_filters(self, data: dict[str, Any]) -> None:
        """Dynamically toggle strategies based on the current market regime."""
        df_primary = data.get("H4") or data.get("primary")
        if df_primary is None or df_primary.empty:
            return

        regime = self.regime_detector.detect(df_primary)
        logger.debug(f"{self.symbol} Current Regime: {regime.value}")

        from app.engine.regime import MarketRegimeType

        if regime in [MarketRegimeType.TRENDING_BULL, MarketRegimeType.TRENDING_BEAR]:
            # Trending markets: Follow trend with ICT and momentum
            self.active_strategies["mean_reversion"] = False
            self.active_strategies["rsi"] = False
            self.active_strategies["smart_money"] = True
            self.active_strategies["momentum"] = True
        else:
            # Ranging or volatile markets: Mean reversion works best
            self.active_strategies["smart_money"] = False
            self.active_strategies["momentum"] = False
            self.active_strategies["mean_reversion"] = True
            self.active_strategies["rsi"] = True

    def analyze(self) -> UnifiedSignal | None:
        """Analyze market with all active strategies."""
        try:
            # Fetch data from MetaApi
            data = self._fetch_market_data()

            if not data:
                logger.warning(f"No market data available for {self.symbol}")
                return None

            self._update_regime_filters(data)

            # Try Smart Money ICT strategy
            if self.active_strategies.get("smart_money"):
                ict_signal = self._analyze_ict(data)
                if ict_signal:
                    return ict_signal

            # Try Mean Reversion strategy
            if self.active_strategies.get("mean_reversion"):
                mr_signal = self._analyze_mean_reversion(data)
                if mr_signal:
                    return mr_signal

            # Try RSI strategy
            if self.active_strategies.get("rsi"):
                rsi_signal = self._analyze_rsi(data)
                if rsi_signal:
                    return rsi_signal

            # Try Momentum strategy
            if self.active_strategies.get("momentum"):
                momentum_signal = self._analyze_momentum(data)
                if momentum_signal:
                    return momentum_signal

            return None

        except Exception as e:
            logger.error(f"Error in strategy analysis: {e}")
            return None

    def analyze_multi_strategy(self) -> dict[str, UnifiedSignal | None]:
        """Analyze with all strategies and return all signals for confluence check."""
        signals = {}

        try:
            data = self._fetch_market_data()

            if not data:
                return signals

            self._update_regime_filters(data)

            if self.active_strategies.get("smart_money"):
                signals["smart_money"] = self._analyze_ict(data)

            if self.active_strategies.get("mean_reversion"):
                signals["mean_reversion"] = self._analyze_mean_reversion(data)

            if self.active_strategies.get("rsi"):
                signals["rsi"] = self._analyze_rsi(data)

            if self.active_strategies.get("momentum"):
                signals["momentum"] = self._analyze_momentum(data)

        except Exception as e:
            logger.error(f"Error in multi-strategy analysis: {e}")

        return signals

    def check_confluence(self) -> UnifiedSignal | None:
        """Check for multi-strategy confluence (highest probability setups)."""
        signals = self.analyze_multi_strategy()

        # Filter out None signals
        active_signals = {k: v for k, v in signals.items() if v is not None}

        if len(active_signals) < 2:
            return None

        # Check if signals agree on direction
        directions = [sig.action for sig in active_signals.values()]

        if len(set(directions)) == 1:
            # All signals agree!
            # Pick the highest confidence signal and boost it
            best_signal = max(active_signals.values(), key=lambda x: x.confidence)

            # Boost confidence for confluence
            original_confidence = best_signal.confidence
            boosted_confidence = min(original_confidence * 1.15, 95.0)

            logger.success(
                f"🎯 CONFLUENCE DETECTED! {len(active_signals)} strategies agree on {best_signal.action} "
                f"(Confidence boosted from {original_confidence:.1f}% to {boosted_confidence:.1f}%)"
            )

            return UnifiedSignal(
                strategy_name=f"CONFLUENCE_{best_signal.strategy_name}",
                action=best_signal.action,
                symbol=best_signal.symbol,
                entry_price=best_signal.entry_price,
                stop_loss=best_signal.stop_loss,
                take_profit=best_signal.take_profit,
                confidence=boosted_confidence,
                risk_reward_ratio=best_signal.risk_reward_ratio,
                reason=f"CONFLUENCE ({len(active_signals)} strategies): {best_signal.reason}",
                timestamp=best_signal.timestamp,
                metadata={
                    "confluence_count": len(active_signals),
                    "strategies": list(active_signals.keys()),
                    "original_signal": best_signal.metadata,
                },
            )

        return None

    def _fetch_market_data(self) -> dict[str, Any] | None:
        """Fetch OHLC data from MetaApi."""
        try:
            # Primary timeframe
            df_primary = get_candles_as_dataframe_sync(
                self.symbol, self.primary_timeframe, limit=200
            )

            if df_primary is None or df_primary.empty:
                return None

            # Additional timeframes for MTF analysis
            df_h1 = get_candles_as_dataframe_sync(self.symbol, "1h", limit=200)
            df_h4 = get_candles_as_dataframe_sync(self.symbol, "4h", limit=200)
            df_d1 = get_candles_as_dataframe_sync(self.symbol, "1d", limit=200)

            return {
                "primary": df_primary,
                "H1": df_h1,
                "H4": df_h4,
                "D1": df_d1,
                "mtf_data": {"H1": df_h1, "H4": df_h4, "D1": df_d1},
            }

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None

    def _analyze_ict(self, data: dict) -> UnifiedSignal | None:
        """Analyze with Smart Money ICT strategy."""
        try:
            df_primary = data.get("H4") or data.get("primary")

            if df_primary is None or df_primary.empty:
                return None

            signal = self.ict.analyze(df_primary)

            if signal:
                return self._convert_ict_signal(signal)

        except Exception as e:
            logger.error(f"Error in ICT analysis: {e}")

        return None

    def _analyze_mean_reversion(self, data: dict) -> UnifiedSignal | None:
        """Analyze with Mean Reversion strategy."""
        try:
            df_primary = data.get("H1") or data.get("primary")
            mtf_data = data.get("mtf_data")

            if df_primary is None or df_primary.empty:
                return None

            signal = self.mr_strategy.analyze(df_primary, mtf_data)

            if signal:
                return self._convert_mr_signal(signal)

        except Exception as e:
            logger.error(f"Error in Mean Reversion analysis: {e}")

    def _analyze_rsi(self, data: dict) -> UnifiedSignal | None:
        """Analyze with Advanced RSI strategy."""
        try:
            df_primary = data.get("H1") or data.get("primary")
            mtf_data = data.get("mtf_data")

            if df_primary is None or df_primary.empty:
                return None

            signal = self.rsi_strategy.analyze(df_primary, mtf_data)

            if signal:
                return self._convert_rsi_signal(signal)

        except Exception as e:
            logger.error(f"Error in RSI analysis: {e}")

        return None

    def _analyze_momentum(self, data: dict) -> UnifiedSignal | None:
        """Analyze with Momentum strategy."""
        try:
            df_primary = data.get("H1") or data.get("primary")

            if df_primary is None or df_primary.empty:
                return None

            signal = self.momentum_strategy.analyze(df_primary)

            if signal:
                return self._convert_momentum_signal(signal)

        except Exception as e:
            logger.error(f"Error in Momentum analysis: {e}")

        return None

    def _convert_ict_signal(self, signal: ICTSignal) -> UnifiedSignal:
        """Convert ICT signal to unified format."""
        return UnifiedSignal(
            strategy_name="SMART_MONEY_ICT",
            action=signal.action,
            symbol=self.symbol,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            confidence=signal.confidence,
            risk_reward_ratio=signal.risk_reward_ratio,
            reason=signal.reason,
            timestamp=datetime.now(),
            metadata={
                "order_block": signal.order_block,
                "fvg": signal.fvg,
                "structure_break": signal.structure_break,
            },
        )

    def _convert_mr_signal(self, signal: MeanReversionSignal) -> UnifiedSignal:
        """Convert Mean Reversion signal to unified format."""
        return UnifiedSignal(
            strategy_name="MEAN_REVERSION",
            action=signal.action,
            symbol=self.symbol,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            confidence=signal.confidence,
            risk_reward_ratio=signal.risk_reward_ratio,
            reason=signal.reason,
            timestamp=datetime.now(),
            metadata={
                "rsi_values": signal.rsi_values,
                "bb_position": signal.bb_position,
                "volatility_state": signal.volatility_state,
            },
        )

    def _convert_rsi_signal(self, signal: RSISignal) -> UnifiedSignal:
        """Convert RSI signal to unified format."""
        return UnifiedSignal(
            strategy_name="ADVANCED_RSI",
            action=signal.action,
            symbol=self.symbol,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            confidence=signal.confidence,
            risk_reward_ratio=signal.risk_reward_ratio,
            reason=signal.reason,
            timestamp=datetime.now(),
            metadata={
                "rsi_value": signal.rsi_value,
                "regime": signal.regime,
                "pattern": signal.pattern,
            },
        )

    def _convert_momentum_signal(self, signal: MomentumSignal) -> UnifiedSignal:
        """Convert Momentum signal to unified format."""
        return UnifiedSignal(
            strategy_name="MOMENTUM",
            action=signal.action,
            symbol=self.symbol,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            confidence=signal.confidence,
            risk_reward_ratio=signal.risk_reward_ratio,
            reason=signal.reason,
            timestamp=datetime.now(),
            metadata={
                "channel_width": signal.channel_width,
                "volatility_state": signal.volatility_state,
                "volume_state": signal.volume_state,
            },
        )

    def set_strategy_active(self, strategy_name: str, active: bool):
        """Enable or disable a strategy."""
        if strategy_name in self.active_strategies:
            self.active_strategies[strategy_name] = active
            logger.info(
                f"Strategy {strategy_name} set to {'active' if active else 'inactive'}"
            )
