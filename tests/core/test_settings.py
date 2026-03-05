from unittest.mock import PropertyMock, patch

import pytest

from app.core.enums import TradingEnvironment
from app.core.settings import Settings, SymbolConfig


@pytest.fixture
def mock_symbols():
    return [
        {"symbol": "EURUSD", "enabled": True, "max_positions": 2},
        {"symbol": "GBPUSD", "enabled": False, "max_positions": 1},
    ]


def test_required_settings():
    settings = Settings(
        TRADING_ENV=TradingEnvironment.DEVELOPMENT,
        METAAPI_TOKEN="test_token",
        METAAPI_ACCOUNT_ID="test_id",
        MAX_OPEN_TRADES=5,
    )

    assert settings.TRADING_ENV == TradingEnvironment.DEVELOPMENT
    assert settings.is_production is False
    assert settings.MAX_OPEN_TRADES == 5


def test_symbols_loading(mock_symbols):
    with patch(
        "app.core.settings.Settings.symbols", new_callable=PropertyMock
    ) as mock_sym:
        mock_sym.return_value = [SymbolConfig(**s) for s in mock_symbols]
        settings = Settings(TRADING_ENV=TradingEnvironment.DEVELOPMENT)

        symbols = settings.symbols
        assert len(symbols) == 2
        assert symbols[0].symbol == "EURUSD"
        assert symbols[0].enabled is True
        assert symbols[1].enabled is False


def test_settings_is_production():
    settings = Settings(
        TRADING_ENV=TradingEnvironment.PRODUCTION,
    )
    assert settings.is_production is True
