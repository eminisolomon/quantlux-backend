from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import LogLevel, TradingEnvironment


class SymbolConfig(BaseModel):
    symbol: str
    enabled: bool = True
    max_positions: int = 1


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    TRADING_ENV: TradingEnvironment = TradingEnvironment.DEVELOPMENT
    LOG_LEVEL: LogLevel = LogLevel.INFO

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    ERROR_LOG_PATH: str = "logs/error.log"
    TRADE_LOG_PATH: str = "logs/trade_history.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "1 week"

    METAAPI_TOKEN: str | None = None
    METAAPI_ACCOUNT_ID: str | None = None
    METAAPI_REGION: str = "new-york"

    MAX_DAILY_DRAWDOWN_PCT: float = 5.0
    MAX_TOTAL_DRAWDOWN_PCT: float = 15.0
    PER_TRADE_RISK_PCT: float = 1.0
    DEFAULT_LOT_SIZE: float = 0.01
    MAX_OPEN_TRADES: int = 5
    DEFAULT_SL_PIPS: int = 20
    MAX_SLIPPAGE: float = 3.0
    MAX_SPREAD_PIPS: float = 5.0
    MIN_MARGIN_LEVEL: float = 100.0
    MAX_POSITIONS_PER_SYMBOL: int = 1
    MAGIC_NUMBER: int = 123456

    ENABLE_AUTO_TRADING: bool = False
    ENABLE_NEWS_FILTER: bool = True
    ALLOW_SPLIT_EXECUTION: bool = False
    EMERGENCY_CLOSE_ON_SHUTDOWN: bool = True

    DEFAULT_INITIAL_BALANCE: float = 10000.0
    RISK_FREE_RATE: float = 0.02

    USE_RSI_STRATEGY: bool = True

    FOREXFACTORY_BASE_URL: str = "https://www.forexfactory.com/calendar?day={}"
    NEWS_IMPACT_FILTER: list[str] = ["High", "Medium"]
    NEWS_PAUSE_MINUTES_BEFORE: int = 30
    NEWS_PAUSE_MINUTES_AFTER: int = 30

    FEED_POLL_INTERVAL: int = 1
    FEED_ERROR_INTERVAL: int = 5
    MT5_RECONNECT_INTERVAL: int = 10
    WS_HEALTH_CHECK_INTERVAL: int = 30
    WS_HEALTH_TIMEOUT: int = 10
    WS_MAX_RECONNECT_ATTEMPTS: int = 5
    WS_RECONNECT_DELAY: int = 5

    REDIS_URL: str = "redis://redis:6379/0"

    @property
    def symbols(self) -> list[SymbolConfig]:
        """Load symbols from config/symbols.yaml."""
        path = Path("config/symbols.yaml")
        if not path.exists():
            return []

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
                return [SymbolConfig(**s) for s in data.get("symbols", [])]
        except Exception as e:
            from app.utils.logger import logger

            logger.error(f"Failed to load symbols from {path}: {e}")
            return []

    @property
    def is_production(self) -> bool:
        return self.TRADING_ENV == TradingEnvironment.PRODUCTION


settings = Settings()
