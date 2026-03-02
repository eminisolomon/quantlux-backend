"""All custom exceptions for the QuantLux trading system."""


class QuantLuxError(Exception):
    """Base exception for all QuantLux-related errors."""

    def __init__(
        self,
        message: str | None = None,
        message_key: str | None = None,
        params: dict | None = None,
    ):
        self.raw_message = message
        self.message_key = message_key
        self.params = params or {}
        super().__init__(self.raw_message or f"QuantLux Error: {self.message_key}")

    def get_user_message(self) -> str:
        """Get formatted user-facing message."""
        if self.message_key:
            from app.core import messages

            msg_template = getattr(messages, self.message_key, None)
            if msg_template:
                return msg_template.format(**self.params)
        return self.raw_message or "An unexpected error occurred."


class TradingError(QuantLuxError):
    """Base exception for trading-related errors."""

    def __init__(self, message: str | None = None, **kwargs):
        super().__init__(message=message, **kwargs)


class InsufficientMarginError(TradingError):
    """Raised when account has insufficient margin for trade."""

    pass


class InvalidVolumeError(TradingError):
    """Raised when trade volume is invalid for symbol."""

    pass


class MaxPositionsError(TradingError):
    """Raised when maximum position limit is reached."""

    pass


class SpreadTooWideError(TradingError):
    """Raised when spread exceeds maximum allowed."""

    pass


class TradingNotAllowedError(TradingError):
    """Raised when trading is not allowed (account restrictions, session, etc)."""

    pass


class RiskError(QuantLuxError):
    """Base exception for risk management errors."""

    pass


class RiskLimitExceededError(RiskError):
    """Raised when a risk limit is exceeded."""

    pass


class CorrelationLimitError(RiskError):
    """Raised when correlation limit between symbols is exceeded."""

    pass


class DrawdownLimitError(RiskError):
    """Raised when maximum drawdown limit is exceeded."""

    pass


class DataError(QuantLuxError):
    """Base exception for data-related errors."""

    pass


class InvalidSymbolError(DataError):
    """Raised when symbol is invalid or not supported."""

    pass


class InvalidTimeframeError(DataError):
    """Raised when timeframe is invalid."""

    pass


class InsufficientDataError(DataError):
    """Raised when insufficient historical data is available."""

    pass


class ConfigurationError(QuantLuxError):
    """Raised when configuration is invalid or missing."""

    pass
