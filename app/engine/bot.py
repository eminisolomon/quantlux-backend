"""
Trading Bot Orchestration Module

This module contains the TradingBot class, which acts as the central hub of the
QuantLux-FX system. it coordinates market data feeds, strategy analysis,
risk management, and execution across all managed symbols.
"""

from collections.abc import Callable

from app.core import logger, settings
from app.core import messages as msg
from app.core.symbols import SymbolManager
from app.engine.executor import SignalExecutor
from app.engine.feed import DataFeed
from app.engine.strategy_manager import StrategyManager
from app.engine.watchdog import MarketWatchdog
from app.metaapi.adapter import MetaApiAdapter
from app.models.market import TickData
from app.risk import RiskManager
from app.strategies.rsi.strategy import RSIStrategy
from news.manager import NewsManager


class TradingBot:
    """
    The central coordinator of the QuantLux-FX trading engine.

    The TradingBot orchestrates the lifecycle of market data ingestion,
    strategy signal generation, risk-controlled trade execution, and
    automated notifications. It acts as the bridge between infrastructural
    adapters (MetaApi) and high-level logic (Strategies/Risk).
    """

    def __init__(
        self,
        risk_manager: RiskManager,
        symbol_manager: SymbolManager,
        news_manager: NewsManager,
        trade_executor: MetaApiAdapter,
        executor: SignalExecutor,
        watchdog: MarketWatchdog,
        gemini=None,
    ):
        """
        Initialize the system orchestration engine.

        Args:
            risk_manager: Handles drawdown monitoring and global risk limits.
            symbol_manager: Manages the list of active/enabled trading symbols.
            news_manager: Monitors economic events to restrict trading during high volatility.
            trade_executor: High-level broker adapter for account interactions.
            executor: Handles the actual signal processing and trade placement.
            watchdog: Monitors data feed health and symbol-specific constraints.
            gemini: Optional AI client for advanced market sentiment analysis.
        """
        self.is_running = False
        self.data_feed: DataFeed | None = None
        self.risk_manager = risk_manager
        self.symbol_manager = symbol_manager
        self.news_manager = news_manager
        self.trade_executor = trade_executor
        self.executor = executor
        self.watchdog = watchdog
        self.gemini = gemini

        self.strategies = StrategyManager(self.trade_executor)
        self.notification_callback: Callable[[str], None] | None = None

    def register_notification_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a global callback mechanism for system notifications (e.g., Telegram).

        Args:
            callback: A function that accepts a message string.
        """
        self.notification_callback = callback
        self.executor.notification_callback = callback

    async def start(self) -> None:
        """
        Activate the bot and start all its background service components.

        This includes initializing strategies, starting news/watchdog services,
        and launching the real-time market data feed.
        """
        logger.info(msg.BOT_START)

        self._initialize_strategies()
        await self.news_manager.start()
        await self.watchdog.start()

        symbols = list(self.strategies.strategies.keys())
        if not symbols:
            logger.warning(msg.BOT_IDLE)

        self.data_feed = DataFeed(symbols, self.trade_executor)
        self.data_feed.register_callback(self.on_tick)
        await self.data_feed.start()

        self.is_running = True
        logger.success(msg.BOT_ACTIVE.format(count=len(symbols)))

    def _initialize_strategies(self) -> None:
        """
        Register and configure trading strategies based on account settings.

        This private method scans enabled symbols and attaches the globally
        configured strategy (e.g., RSIStrategy) to each.
        """
        symbols = self.symbol_manager.get_enabled_symbols()
        for symbol in symbols:
            if settings.USE_RSI_STRATEGY:
                strategy = RSIStrategy(
                    symbol, {"rsi_period": 14, "oversold": 30, "overbought": 70}
                )
                self.strategies.add_strategy(symbol, strategy)
                logger.debug(
                    msg.STRATEGY_REG_DEBUG.format(strategy="RSIStrategy", symbol=symbol)
                )

    async def stop(self) -> None:
        """
        Perform a graceful shutdown of all bot services.

        This shuts down the data feed, news monitor, and market watchdog.
        """
        logger.info(msg.BOT_STOPPING)
        self.is_running = False

        if self.data_feed:
            await self.data_feed.stop()

        await self.news_manager.stop()
        await self.watchdog.stop()
        logger.success(msg.BOT_STOP_COMPLETE)

    async def _emergency_close_all(self) -> None:
        """
        Identify and close all open positions managed by this bot instance.

        This is typically used during a 'Kill Switch' activation. It filters
        positions by the configured MAGIC_NUMBER to avoid interfering with
        manual trades or other bots.
        """
        logger.info(msg.BOT_CLEAR_POSITIONS)
        try:
            positions = await self.trade_executor.get_positions()
            count = 0
            for pos in positions:
                magic = getattr(pos, "magic", None) or (
                    isinstance(pos, dict) and pos.get("magic")
                )
                if magic == settings.MAGIC_NUMBER:
                    pos_id = getattr(pos, "id", None) or (
                        isinstance(pos, dict) and pos.get("id")
                    )
                    if pos_id:
                        await self.trade_executor.close_position(pos_id)
                        count += 1

            logger.info(msg.EMERGENCY_CLOSE_COMPLETE.format(count=count))
        except Exception as e:
            logger.error(msg.EMERGENCY_CLOSE_ERROR.format(error=e))

    async def on_tick(self, symbol: str, tick: TickData) -> None:
        """
        The primary real-time processing entry point for every incoming price update.

        This pipeline performs the following steps:
        1.  Health check (Watchdog)
        2.  Economic constraint check (News)
        3.  Signal generation (Strategy)
        4.  Risk-aware execution (Executor)

        Args:
            symbol: The financial instrument that emitted the tick.
            tick: The raw price and volume data.
        """
        if not self.is_running:
            return

        try:
            # Step 1: Feed Health & Symbol Constraints
            if not await self.watchdog.check_tick(symbol, tick):
                return

            # Step 2: Global Economic News Restrictions
            if not self.news_manager.should_trade(symbol):
                return

            # Step 3: Core Signal Generation
            tick_dict = tick.model_dump()
            signals = await self.strategies.process_tick(symbol, tick_dict)

            # Step 4: Execution Pipeline
            from app.models.signal import TradeSignal

            for signal_data, strategy in signals:
                if isinstance(signal_data, dict):
                    signal = TradeSignal(symbol=symbol, **signal_data)
                else:
                    signal = signal_data
                await self.executor.process_signal(signal, strategy)

        except Exception as e:
            logger.error(msg.BOT_TICK_ERROR.format(symbol=symbol, error=e))
