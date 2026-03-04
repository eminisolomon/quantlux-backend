"""Trading Bot orchestration module."""

from app.core import logger, settings
from app.core import messages as msg
from app.core.symbols import SymbolManager
from app.engine.executor import SignalExecutor
from app.engine.feed import DataFeed
from app.engine.strategy_manager import StrategyManager
from app.engine.watchdog import MarketWatchdog
from app.metaapi.adapter import MetaApiAdapter
from app.schemas.market import TickData
from app.risk import RiskManager
from app.risk.trade_manager import ActiveTradeManager
from news.manager import NewsManager


class TradingBot:
    """Central coordinator of the QuantLux-FX trading engine."""

    def __init__(
        self,
        risk_manager: RiskManager,
        symbol_manager: SymbolManager,
        news_manager: NewsManager,
        trade_executor: MetaApiAdapter,
        executor: SignalExecutor,
        watchdog: MarketWatchdog,
        strategy_manager: StrategyManager,
        active_trade_manager: ActiveTradeManager,
        gemini=None,
    ):
        self.is_running = False
        self.data_feed: DataFeed | None = None
        self.risk_manager = risk_manager
        self.symbol_manager = symbol_manager
        self.news_manager = news_manager
        self.trade_executor = trade_executor
        self.executor = executor
        self.watchdog = watchdog
        self.gemini = gemini
        self.strategies = strategy_manager
        self.active_trade_manager = active_trade_manager

    async def start(self) -> None:
        """Start all background services and the data feed."""
        logger.info(msg.BOT_START)

        self._initialize_strategies()
        await self.active_trade_manager.start()
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
        """Register strategies for all enabled symbols."""
        symbols = self.symbol_manager.get_enabled_symbols()
        for symbol in symbols:
            self.strategies.add_high_accuracy_strategies(symbol)
            logger.debug(
                msg.STRATEGY_REG_DEBUG.format(
                    strategy="MasterStrategyAdapter", symbol=symbol
                )
            )

    async def stop(self) -> None:
        """Gracefully shut down all bot services."""
        logger.info(msg.BOT_STOPPING)
        self.is_running = False

        if self.data_feed:
            await self.data_feed.stop()

        await self.active_trade_manager.stop()
        await self.news_manager.stop()
        await self.watchdog.stop()
        logger.success(msg.BOT_STOP_COMPLETE)

    async def _emergency_close_all(self) -> None:
        """Close all bot-managed positions (kill switch)."""
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
        """Process incoming price tick: watchdog → news → strategy → execution."""
        if not self.is_running:
            return

        try:
            if not await self.watchdog.check_tick(symbol, tick):
                return

            if not self.news_manager.should_trade(symbol):
                return

            unified_signal = self.strategies.analyze_high_accuracy(symbol)

            if unified_signal:
                from app.schemas.signal import TradeSignal

                signal = TradeSignal(
                    action=unified_signal.action,
                    symbol=symbol,
                    price=unified_signal.entry_price,
                    stop_loss=unified_signal.stop_loss,
                    take_profit=unified_signal.take_profit,
                    confidence=unified_signal.confidence,
                    reason=unified_signal.reason,
                    comment=unified_signal.strategy_name,
                    metadata=unified_signal.metadata,
                )
                await self.executor.process_signal(signal, strategy=None)

        except Exception as e:
            logger.error(msg.BOT_TICK_ERROR.format(symbol=symbol, error=e))
