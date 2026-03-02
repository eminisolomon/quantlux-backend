"""Symbol configuration management."""

from app.core.settings import SymbolConfig, settings
from app.utils.logger import logger


class SymbolManager:
    """Manage trading symbols configuration from YAML settings."""

    def __init__(self):
        self._load_config()

    def _load_config(self):
        self.configs = {s.symbol: s for s in settings.symbols}
        logger.info(f"Loaded {len(self.configs)} symbols from configuration.")

    def get_enabled_symbols(self) -> list[str]:
        return [s.symbol for s in self.configs.values() if s.enabled]

    def get_symbol_config(self, symbol: str) -> SymbolConfig | None:
        return self.configs.get(symbol)

    def is_symbol_enabled(self, symbol: str) -> bool:
        config = self.get_symbol_config(symbol)
        return config.enabled if config else False

    def get_max_positions(self, symbol: str) -> int:
        config = self.get_symbol_config(symbol)
        return config.max_positions if config else 1
