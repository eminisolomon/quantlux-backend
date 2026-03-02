import pandas as pd

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import MARKET_ANALYSIS_PROMPT, MARKET_ANALYSIS_SYSTEM
from app.core.decorators import fallback_on_failure, require_feature
from app.indicators.atr import calculate_atr
from app.indicators.rsi.calculator import ModernRSI
from app.metaapi.adapter import MetaApiAdapter


@require_feature(
    "ENABLE_AI_FEATURES", fallback_return="⚠️ AI features are disabled via settings."
)
@fallback_on_failure(default_return="⚠️ AI analysis error occurred.")
async def analyze_market(
    gemini: GeminiClient,
    metaapi: MetaApiAdapter,
    symbol: str,
    timeframe: str = "H1",
    candle_count: int = 30,
) -> str | None:
    """Perform AI-powered market analysis for a symbol."""
    if not gemini.is_available:
        return "⚠️ AI features unavailable — GEMINI_API_KEY not configured."

    # Fetch OHLCV data
    df = await metaapi.get_candles_as_dataframe(
        symbol, timeframe=timeframe, limit=candle_count
    )

    if df is None or df.empty:
        return f"⚠️ No candle data available for {symbol} {timeframe}."

    # Calculate basic indicators
    close = df["close"]
    current_price = float(close.iloc[-1])

    # RSI(14) using ModernRSI
    rsi_calc = ModernRSI()
    rsi_series = rsi_calc.calculate(close)
    rsi_value = (
        float(rsi_series.iloc[-1])
        if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1])
        else 50.0
    )

    # ATR(14) using calculate_atr
    atr_value = calculate_atr(
        df["high"].tolist(), df["low"].tolist(), df["close"].tolist(), period=14
    )

    # Format candle summary (last 10 for brevity)
    recent = df.tail(10)
    candle_lines = []
    for _, row in recent.iterrows():
        candle_lines.append(
            f"  O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f}"
        )
    candles_text = "\n".join(candle_lines)

    prompt = MARKET_ANALYSIS_PROMPT.format(
        symbol=symbol,
        timeframe=timeframe,
        candle_count=candle_count,
        candles=candles_text,
        rsi=f"{rsi_value:.1f}",
        atr=f"{atr_value:.5f}",
        price=f"{current_price:.5f}",
    )

    result = await gemini.generate(
        prompt=prompt,
        system_instruction=MARKET_ANALYSIS_SYSTEM,
    )

    if result:
        return f"🤖 *AI Market Analysis — {symbol} {timeframe}*\n\n{result}"
    return "⚠️ AI analysis returned empty — please try again later."
