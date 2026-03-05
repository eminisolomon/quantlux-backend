"""Application lifecycle: initialization and state sync."""

from app.services.analytics_service import AnalyticsService
from app.core import messages as msg
from app.core.di import container, init_container
from app.core.settings import settings
from app.core.symbols import SymbolManager
from app.engine.bot import TradingBot
from app.engine.executor import SignalExecutor
from app.engine.watchdog import MarketWatchdog
from app.execution.broker import AbstractBroker
from app.metaapi.adapter import MetaApiAdapter
from app.risk.correlation import CorrelationManager
from app.risk.drawdown import DrawdownManager
from app.risk.manager import RiskManager
from app.services.news_service import NewsService
from app.utils.logger import logger


async def init_engine_services() -> (
    tuple[SymbolManager, CorrelationManager, NewsService, MetaApiAdapter]
):
    """Initialize brokers, managers, and data feed handlers."""
    logger.info(msg.APP_START)
    symbol_manager = SymbolManager()
    correlation_manager = CorrelationManager()
    news_manager = NewsService()
    broker = MetaApiAdapter()
    init_container(broker)
    return symbol_manager, correlation_manager, news_manager, broker


async def init_trading_logic(
    symbol_manager: SymbolManager,
    correlation_manager: CorrelationManager,
    news_manager: NewsService,
    broker: AbstractBroker,
) -> tuple[DrawdownManager, AnalyticsService, RiskManager, TradingBot]:
    """Initialize trading logic, risk management, and the core bot."""
    risk_manager = container.resolve(RiskManager)
    drawdown_manager = risk_manager.drawdown_manager
    executor = container.resolve(SignalExecutor)
    watchdog = container.resolve(MarketWatchdog)

    from app.engine.strategy_manager import StrategyManager
    from app.risk.trade_manager import ActiveTradeManager

    strategy_manager = container.resolve(StrategyManager)
    active_trade_manager = container.resolve(ActiveTradeManager)

    tracker = AnalyticsService(initial_balance=settings.DEFAULT_INITIAL_BALANCE)

    trading_bot = TradingBot(
        risk_manager=risk_manager,
        symbol_manager=symbol_manager,
        news_manager=news_manager,
        trade_executor=broker,
        executor=executor,
        watchdog=watchdog,
        strategy_manager=strategy_manager,
        active_trade_manager=active_trade_manager,
    )

    return drawdown_manager, tracker, risk_manager, trading_bot


async def synchronize_state(
    metaapi: MetaApiAdapter, drawdown: DrawdownManager, tracker: AnalyticsService
) -> None:
    """Sync local state with live account equity."""
    try:
        await metaapi.initialize()
        initial_equity = await _fetch_equity(metaapi)
        await _sync_drawdown(drawdown, initial_equity)
        await _sync_tracker(tracker, initial_equity)
        logger.success(msg.SERVICE_SYNC.format(equity=initial_equity))
    except Exception as e:
        logger.warning(msg.SYNC_ERROR.format(error=e))
        await _sync_drawdown(drawdown, settings.DEFAULT_INITIAL_BALANCE)


async def _fetch_equity(metaapi: MetaApiAdapter) -> float:
    """Fetch live equity from broker, falling back to default on failure."""
    account_info = await metaapi.get_account_info()
    if not account_info:
        logger.warning(msg.SYNC_FAILED)
        return settings.DEFAULT_INITIAL_BALANCE
    equity = account_info.equity
    return equity if equity > 0 else settings.DEFAULT_INITIAL_BALANCE


async def _sync_drawdown(drawdown: DrawdownManager, equity: float) -> None:
    """Initialize the drawdown manager with the given equity."""
    await drawdown.initialize(equity)


async def _sync_tracker(tracker: AnalyticsService, equity: float) -> None:
    """Seed the analytics service equity curve with the live starting equity."""
    await tracker.initialize()
    tracker.current_equity = equity
    tracker.initial_balance = equity
    if not tracker.equity_curve:
        tracker.equity_curve = [equity]
    else:
        if tracker.equity_curve[-1] != equity:
            tracker.equity_curve.append(equity)
