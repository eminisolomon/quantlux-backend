from app.core.enums import SignalAction
from app.core.settings import settings
from app.schemas import TradeRequest


class OrderFactory:
    """Factory for creating TradeRequest objects."""

    @staticmethod
    def create_market_order(
        symbol: str,
        volume: float,
        order_type: SignalAction,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 0,
        comment: str = "",
    ) -> TradeRequest:
        """Create a market order request (Buy/Sell)."""
        if magic == 0:
            magic = settings.MAGIC_NUMBER

        return TradeRequest(
            action=order_type,
            symbol=symbol,
            volume=volume,
            type=order_type,
            price=price,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
        )

    @staticmethod
    def create_market_buy(
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 0,
        comment: str = "",
    ) -> TradeRequest:
        """Helper for Market Buy."""
        return OrderFactory.create_market_order(
            symbol, volume, SignalAction.BUY, 0.0, sl, tp, magic, comment
        )

    @staticmethod
    def create_market_sell(
        symbol: str,
        volume: float,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int = 0,
        comment: str = "",
    ) -> TradeRequest:
        """Helper for Market Sell."""
        return OrderFactory.create_market_order(
            symbol, volume, SignalAction.SELL, 0.0, sl, tp, magic, comment
        )
