"""MetaApi schemas for type-safe data structures."""

from pydantic import BaseModel, ConfigDict, Field


class AccountInfo(BaseModel):
    """MetaApi account information."""

    model_config = ConfigDict(extra="allow")

    currency: str = Field(..., description="Account currency")
    balance: float = Field(..., description="Account balance")
    equity: float = Field(..., description="Account equity")
    margin: float = Field(..., description="Used margin")
    freeMargin: float = Field(..., description="Free margin")
    marginLevel: float | None = Field(None, description="Margin level percentage")
    leverage: int = Field(..., description="Account leverage")
    name: str | None = Field(None, description="Account name")
    server: str | None = Field(None, description="Broker server name")
    investorMode: bool | None = Field(None, description="Is account in investor mode")
    credit: float | None = Field(None, description="Credit amount")

    @property
    def pnl(self) -> float:
        """Calculate current profit/loss."""
        return self.equity - self.balance

    @property
    def pnl_pct(self) -> float:
        """Calculate P&L percentage."""
        return (self.pnl / self.balance * 100) if self.balance > 0 else 0.0


class SymbolInfo(BaseModel):
    """Trading symbol specification."""

    model_config = ConfigDict(extra="allow")

    symbol: str = Field(..., description="Symbol name")
    path: str = Field(..., description="Symbol path in market watch")
    description: str = Field(..., description="Symbol description")
    contractSize: float = Field(..., description="Contract size")
    digits: int = Field(..., description="Number of decimal places")
    point: float = Field(..., description="Point value")
    tickSize: float = Field(..., description="Minimum price change")
    tickValue: float = Field(..., description="Tick value in deposit currency")
    pippingBlock: float = Field(..., description="Pipping block")
    stopsLevel: float | None = Field(None, description="Stops level in points")
    minVolume: float = Field(..., description="Minimum transaction volume")
    maxVolume: float = Field(..., description="Maximum transaction volume")
    volumeStep: float = Field(..., description="Volume step")
    tradeMode: str = Field(..., description="Trade mode (e.g., 'TRADE_FULL')")
    marginMode: str | None = Field(None, description="Margin calculation mode")
    initialMargin: float | None = Field(None, description="Initial margin")
    maintenanceMargin: float | None = Field(None, description="Maintenance margin")


class TradeRequest(BaseModel):
    """Request to open a new trade."""

    model_config = ConfigDict(extra="allow")

    actionType: str = Field(..., description="ORDER_TYPE_BUY or ORDER_TYPE_SELL")
    symbol: str = Field(..., description="Trading symbol")
    volume: float = Field(..., description="Trade volume/lots")
    price: float | None = Field(None, description="Order price (for pending orders)")
    stopLoss: float | None = Field(None, description="Stop loss price")
    takeProfit: float | None = Field(None, description="Take profit price")
    comment: str | None = Field(None, description="Order comment")
    clientId: str | None = Field(None, description="Client-defined specific identifier")
    magic: int | None = Field(None, description="Expert Advisor ID")
    slippage: int | None = Field(None, description="Maximum allowed slippage")


class OrderSendResult(BaseModel):
    """Result of a trading operation."""

    model_config = ConfigDict(extra="allow")

    numericCode: int = Field(..., description="MetaTrader return code")
    stringCode: str = Field(..., description="String code of the error")
    message: str = Field(..., description="Error message")
    orderId: str | None = Field(None, description="ID of the placed order")
    positionId: str | None = Field(None, description="ID of the opened position")


class TradePosition(BaseModel):
    """Active trade position."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Position ID")
    type: str = Field(..., description="POSITION_TYPE_BUY or POSITION_TYPE_SELL")
    symbol: str = Field(..., description="Trading symbol")
    magic: int | None = Field(None, description="Expert Advisor ID")
    time: str = Field(..., description="Position open time")
    updateTime: str = Field(..., description="Position update time")
    openPrice: float = Field(..., description="Open price")
    currentPrice: float = Field(..., description="Current price")
    volume: float = Field(..., description="Position volume")
    swap: float = Field(..., description="Accumulated swap")
    profit: float = Field(..., description="Current profit")
    comment: str | None = Field(None, description="Position comment")
    clientId: str | None = Field(None, description="Client ID")
    stopLoss: float | None = Field(None, description="Stop loss level")
    takeProfit: float | None = Field(None, description="Take profit level")


class TradeOrder(BaseModel):
    """Pending trade order."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(..., description="Order ID")
    type: str = Field(..., description="Order type (e.g., ORDER_TYPE_BUY_LIMIT)")
    state: str = Field(..., description="Order state (e.g., ORDER_STATE_PLACED)")
    symbol: str = Field(..., description="Trading symbol")
    magic: int | None = Field(None, description="Expert Advisor ID")
    timeSetup: str = Field(..., description="Order setup time")
    openPrice: float = Field(..., description="Order price")
    currentPrice: float = Field(None, description="Current price")
    volumeInitial: float = Field(..., description="Initial volume")
    volumeCurrent: float = Field(..., description="Remaining volume")
    comment: str | None = Field(None, description="Order comment")
    clientId: str | None = Field(None, description="Client ID")
    stopLoss: float | None = Field(None, description="Stop loss level")
    takeProfit: float | None = Field(None, description="Take profit level")


class TerminalInfo(BaseModel):
    """MetaTrader terminal information."""

    model_config = ConfigDict(extra="allow")

    build: int = Field(..., description="Terminal build number")
    company: str = Field(..., description="Broker company name")
    name: str = Field(..., description="Terminal name")
    language: str = Field(..., description="Terminal language")
    connected: bool = Field(..., description="Is terminal connected to broker")
    platform: str = Field(..., description="MT4 or MT5")
    trade_allowed: bool = Field(..., description="Is trading allowed")


# Export
__all__ = [
    "AccountInfo",
    "SymbolInfo",
    "TradeRequest",
    "OrderSendResult",
    "TradePosition",
    "TradeOrder",
    "TerminalInfo",
]
