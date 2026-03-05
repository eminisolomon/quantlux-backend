from app.core.symbols import SymbolManager


def test_symbol_manager_initialization():
    manager = SymbolManager()
    enabled_symbols = manager.get_enabled_symbols()
    assert "EURUSD" in enabled_symbols
    assert "GBPUSD" in enabled_symbols


def test_get_symbol_config():
    manager = SymbolManager()
    config = manager.get_symbol_config("EURUSD")
    assert config is not None
    assert config.symbol == "EURUSD"
    assert config.enabled is True
    assert config.max_positions >= 1

    config = manager.get_symbol_config("UNKNOWN_SYMBOL_XYZ")
    assert config is None


def test_is_symbol_enabled():
    manager = SymbolManager()
    assert manager.is_symbol_enabled("EURUSD") is True
    assert manager.is_symbol_enabled("NON_EXISTENT") is False


def test_get_max_positions():
    manager = SymbolManager()
    max_pos = manager.get_max_positions("EURUSD")
    assert isinstance(max_pos, int)
    assert max_pos >= 1
