from typing import Any, TypeVar

from app.engine.watchdog import MarketWatchdog
from app.metaapi.adapter import MetaApiAdapter
from app.services.account import AccountService

T = TypeVar("T")


class DIContainer:
    """Lightweight Dependency Injection container."""

    def __init__(self):
        self._services: dict[type, Any] = {}

    def register(self, service_type: type[T], instance: T) -> None:
        """Register a service instance."""
        self._services[service_type] = instance

    def resolve(self, service_type: type[T]) -> T:
        """Resolve a service instance."""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type} not registered")
        return self._services[service_type]


container = DIContainer()


def init_container(metaapi_adapter: MetaApiAdapter) -> None:
    """Initialize the global container with core services."""
    from app.core.settings import settings
    from app.engine.executor import SignalExecutor
    from app.risk import RiskManager
    from app.risk.correlation import CorrelationManager
    from app.risk.drawdown import DrawdownManager

    container.register(MetaApiAdapter, metaapi_adapter)

    account_service = AccountService(metaapi_adapter)
    container.register(AccountService, account_service)

    drawdown_manager = DrawdownManager(
        max_daily_dd_pct=settings.MAX_DAILY_DRAWDOWN_PCT,
        max_total_dd_pct=settings.MAX_TOTAL_DRAWDOWN_PCT,
    )
    correlation_manager = CorrelationManager()

    risk_manager = RiskManager(
        drawdown_manager=drawdown_manager,
        correlation_manager=correlation_manager,
        broker=metaapi_adapter,
        account_service=account_service,
    )
    container.register(RiskManager, risk_manager)

    executor = SignalExecutor(risk_manager=risk_manager, broker=metaapi_adapter)
    container.register(SignalExecutor, executor)

    from app.engine.strategy_manager import StrategyManager
    from app.risk.trade_manager import ActiveTradeManager

    strategy_manager = StrategyManager(metaapi=metaapi_adapter)
    container.register(StrategyManager, strategy_manager)

    active_trade_manager = ActiveTradeManager(broker=metaapi_adapter)
    container.register(ActiveTradeManager, active_trade_manager)

    container.register(MarketWatchdog, MarketWatchdog())
    return container
