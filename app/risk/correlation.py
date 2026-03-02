from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from app.core import messages as msg
from app.core.settings import settings
from app.utils.logger import logger


class CorrelationManager:
    """Manages portfolio correlation risk."""

    def __init__(self):
        self.correlation_matrix = pd.DataFrame()
        self.last_update = datetime.min
        self.update_interval = timedelta(hours=24)
        self.max_correlation = getattr(settings, "MAX_CORRELATION", 0.8)

    async def update_correlations(self, symbols: list[str]):
        """Download history and calculate correlation matrix."""
        if not symbols:
            return

        # Check if update is needed
        if (
            datetime.now() - self.last_update < self.update_interval
            and not self.correlation_matrix.empty
        ):
            return

        try:
            logger.info(msg.CORR_UPDATING)
            data = yf.download(
                tickers=" ".join(symbols),
                period="1mo",
                interval="60m",
                group_by="ticker",
                progress=False,
            )

            # Extract Close prices
            closes = pd.DataFrame()
            if len(symbols) == 1:
                closes[symbols[0]] = data["Close"]
            else:
                for symbol in symbols:
                    if symbol in data.columns.levels[0]:  # MultiIndex check
                        closes[symbol] = data[symbol]["Close"]
                    elif symbol in data.columns:  # Flat check
                        closes[symbol] = data[symbol]

            self.correlation_matrix = closes.corr()
            self.last_update = datetime.now()
            logger.info(msg.CORR_UPDATED)
            logger.debug(f"\n{self.correlation_matrix}")

        except Exception as e:
            logger.error(msg.CORR_UPDATE_FAILED.format(error=e))

    def check_correlation(self, new_symbol: str, current_positions: list[str]) -> bool:
        """
        Check if new_symbol is highly correlated with any existing position.
        Returns False if correlation is too high (Risk!).
        """
        if self.correlation_matrix.empty:
            return True  # Fail open if no data

        if new_symbol not in self.correlation_matrix.columns:
            logger.warning(msg.CORR_SYM_NOT_FOUND.format(symbol=new_symbol))
            return True

        for pos_symbol in current_positions:
            if pos_symbol in self.correlation_matrix.columns:
                corr = self.correlation_matrix.loc[new_symbol, pos_symbol]
                if abs(corr) > self.max_correlation:
                    logger.warning(
                        msg.CORR_REJECT.format(
                            symbol=new_symbol,
                            other=pos_symbol,
                            corr=corr,
                            limit=self.max_correlation,
                        )
                    )
                    return False

        return True
