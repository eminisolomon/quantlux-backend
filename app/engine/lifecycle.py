"""Application lifecycle: component initialization and state synchronization."""

from app.ai.gemini_client import GeminiClient
from app.analytics.tracker import PerformanceTracker
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
from app.services.account import AccountService
from app.telegram.bot import TelegramBot
from app.telegram.controllers.ai_chat import AIChatController
from app.telegram.controllers.analytics import AnalyticsController
from app.telegram.controllers.callbacks import CallbacksController
from app.telegram.controllers.info import InfoController
from app.utils.logger import logger
from news.manager import NewsManager


async def init_engine_services() -> (
    tuple[SymbolManager, CorrelationManager, NewsManager, MetaApiAdapter]
):
    """Initialize core engine services."""
    logger.info(msg.APP_START)
    logger.info("Initializing MetaAPI Adapter...")
    symbol_manager = SymbolManager()
    correlation_manager = CorrelationManager()
    news_manager = NewsManager()
    broker = MetaApiAdapter()

    # Initialize DI Container
    init_container(broker)

    return symbol_manager, correlation_manager, news_manager, broker


def init_ai_services() -> GeminiClient:
    """Initialize AI services (Gemini client)."""
    gemini = GeminiClient()
    if gemini.is_available:
        logger.success(msg.AI_ENABLED)
    else:
        logger.info(msg.AI_DISABLED_KEY)
    return gemini


async def init_trading_logic(
    symbol_manager: SymbolManager,
    correlation_manager: CorrelationManager,
    news_manager: NewsManager,
    broker: AbstractBroker,
    gemini: GeminiClient = None,
) -> tuple[DrawdownManager, PerformanceTracker, RiskManager, TradingBot]:
    """Initialize trading logic, risk management, and the core bot using DI."""
    # Resolve from DI
    risk_manager = container.resolve(RiskManager)
    drawdown_manager = risk_manager.drawdown_manager
    executor = container.resolve(SignalExecutor)
    watchdog = container.resolve(MarketWatchdog)

    # Inject gemini if available
    if gemini:
        executor.gemini = gemini

    tracker = PerformanceTracker(initial_balance=settings.DEFAULT_INITIAL_BALANCE)

    trading_bot = TradingBot(
        risk_manager=risk_manager,
        symbol_manager=symbol_manager,
        news_manager=news_manager,
        trade_executor=broker,
        executor=executor,
        watchdog=watchdog,
        gemini=gemini,
    )

    return drawdown_manager, tracker, risk_manager, trading_bot


async def init_telegram_interface(
    trading_bot: TradingBot,
    tracker: PerformanceTracker,
    drawdown: DrawdownManager,
    broker: AbstractBroker,
    gemini: GeminiClient = None,
) -> TelegramBot:
    """Initialize Telegram bot and register controllers."""

    account_service = container.resolve(AccountService)

    analytics_controller = AnalyticsController(
        performance_tracker=tracker,
        drawdown=drawdown,
        account_service=account_service,
    )

    callbacks_controller = CallbacksController(
        tracker=tracker, account_service=account_service
    )

    info_controller = InfoController(account_service=account_service)

    # AI Chat Controller (optional)
    ai_chat_controller = None
    if gemini and gemini.is_available and settings.ENABLE_AI_FEATURES:
        ai_chat_controller = AIChatController(
            gemini=gemini, account_service=account_service, tracker=tracker
        )

    telegram_bot = TelegramBot(
        analytics_controller=analytics_controller,
        callbacks_controller=callbacks_controller,
        info_controller=info_controller,
        ai_chat_controller=ai_chat_controller,
    )
    telegram_bot.trading_bot = trading_bot
    return telegram_bot


async def synchronize_state(
    metaapi: "MetaApiAdapter", drawdown: DrawdownManager, tracker: PerformanceTracker
) -> None:
    """Synchronize local state with live account equity and trade history."""
    try:
        await metaapi.initialize()
        account_info = await metaapi.get_account_info()

        if account_info:
            initial_equity = account_info.equity
            if initial_equity <= 0:
                initial_equity = settings.DEFAULT_INITIAL_BALANCE

            drawdown.initialize(initial_equity)
            tracker.current_equity = initial_equity
            tracker.initial_balance = initial_equity

            if not tracker.equity_curve:
                tracker.equity_curve = [initial_equity]
            else:
                tracker.equity_curve.append(initial_equity)

            logger.success(msg.SERVICE_SYNC.format(equity=initial_equity))
        else:
            logger.warning(msg.SYNC_FAILED)
            drawdown.initialize(settings.DEFAULT_INITIAL_BALANCE)

    except Exception as e:
        logger.warning(msg.SYNC_ERROR.format(error=e))
        drawdown.initialize(settings.DEFAULT_INITIAL_BALANCE)
