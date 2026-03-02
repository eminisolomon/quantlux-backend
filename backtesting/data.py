"""Data utilities for backtesting."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.utils.logger import logger


def load_historical_data_csv(filepath: str) -> pd.DataFrame:
    """Load historical data from a CSV file."""
    try:
        df = pd.read_csv(filepath)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return pd.DataFrame()


def load_sample_data(
    symbol: str = "EURUSD", start: str = None, end: str = None
) -> pd.DataFrame:
    """Generate sample data for backtesting if no real data is available."""
    logger.info(f"Generating sample data for {symbol}")

    if not start:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")

    dates = pd.date_range(start=start, end=end, freq="H")
    n = len(dates)

    # Generate random walk data
    close_prices = 1.1000 + np.cumsum(np.random.normal(0, 0.001, n))
    high_prices = close_prices + np.random.uniform(0, 0.002, n)
    low_prices = close_prices - np.random.uniform(0, 0.002, n)
    open_prices = close_prices - np.random.normal(0, 0.0005, n)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": np.random.randint(100, 1000, n),
        },
        index=dates,
    )

    df.index.name = "datetime"
    return df
