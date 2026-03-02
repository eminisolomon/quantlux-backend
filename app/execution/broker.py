from abc import ABC, abstractmethod


class AbstractBroker(ABC):
    """Abstract base class for all trading brokers (MetaApi, Binance, etc)."""

    @abstractmethod
    async def create_market_buy_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict:
        """Create a market buy order."""
        pass

    @abstractmethod
    async def create_market_sell_order(
        self,
        symbol: str,
        volume: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        comment: str | None = None,
    ) -> dict:
        """Create a market sell order."""
        pass

    @abstractmethod
    async def modify_position(
        self,
        position_id: str,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ) -> dict:
        """Modify stop loss or take profit of an existing position."""
        pass

    @abstractmethod
    async def close_position(
        self, position_id: str, volume: float | None = None
    ) -> dict:
        """Close a position partially or fully."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> dict:
        """Cancel a pending order."""
        pass
