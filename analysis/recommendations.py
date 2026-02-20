"""
Trade recommendation module.

Analyses the latest values of technical indicators together with the
cyclicality assessment and produces a human-readable recommendation.

For a BUY signal the module also proposes:
- an entry price (current close),
- a target exit price (entry × 1.10, i.e. +10 %) reachable within 30 days.
"""

import math
import pandas as pd
from typing import Optional


def _latest(series: pd.Series) -> Optional[float]:
    """Return the most recent non-NaN scalar value from a Series."""
    valid = series.dropna()
    if valid.empty:
        return None
    val = valid.iloc[-1]
    if hasattr(val, "item"):
        try:
            return float(val.item())
        except Exception:
            pass
    try:
        return float(val)
    except Exception:
        return None


def generate_recommendation(
    df: pd.DataFrame,
    cyclicality: dict,
) -> dict:
    """
    Generate a trade recommendation from indicator data and cyclicality info.

    Args:
        df: Enriched OHLCV DataFrame produced by ``compute_indicators``.
        cyclicality: Dictionary returned by ``detect_cyclicality``.

    Returns:
        Dictionary with keys:
        - ``action``: "BUY", "SELL", or "HOLD".
        - ``reason``: str – bullet-point explanation of the decision.
        - ``entry_price``: float or None (set only for BUY).
        - ``exit_price``: float or None (set only for BUY, entry × 1.10).
        - ``horizon_days``: int – maximum days to reach exit price (30).
        - ``summary``: str – one-line text suitable for the CSV column.
    """
    recommendation: dict = {
        "action": "HOLD",
        "reason": "",
        "entry_price": None,
        "exit_price": None,
        "horizon_days": 30,
        "summary": "HOLD",
    }

    close_price = _latest(df["Close"].squeeze())
    rsi = _latest(df["RSI"])
    macd = _latest(df["MACD"])
    macd_signal = _latest(df["MACD_Signal"])
    sma_50 = _latest(df["SMA_50"])
    sma_200 = _latest(df["SMA_200"])
    lower_band = _latest(df["Bollinger_Lower"])
    upper_band = _latest(df["Bollinger_Upper"])

    if close_price is None:
        return recommendation

    buy_signals: list[str] = []
    sell_signals: list[str] = []

    # RSI
    if rsi is not None:
        if rsi < 30:
            buy_signals.append(f"RSI={rsi:.1f} (oversold < 30)")
        elif rsi > 70:
            sell_signals.append(f"RSI={rsi:.1f} (overbought > 70)")

    # MACD crossover
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            buy_signals.append(
                f"MACD={macd:.3f} above Signal={macd_signal:.3f} (bullish crossover)"
            )
        else:
            sell_signals.append(
                f"MACD={macd:.3f} below Signal={macd_signal:.3f} (bearish crossover)"
            )

    # Golden / death cross
    if sma_50 is not None and sma_200 is not None:
        if sma_50 > sma_200:
            buy_signals.append(
                f"SMA50={sma_50:.2f} > SMA200={sma_200:.2f} (golden cross)"
            )
        else:
            sell_signals.append(
                f"SMA50={sma_50:.2f} < SMA200={sma_200:.2f} (death cross)"
            )

    # Price vs Bollinger Bands
    if lower_band is not None and close_price < lower_band:
        buy_signals.append(
            f"Close={close_price:.2f} below Bollinger Lower={lower_band:.2f}"
        )
    if upper_band is not None and close_price > upper_band:
        sell_signals.append(
            f"Close={close_price:.2f} above Bollinger Upper={upper_band:.2f}"
        )

    # Cyclicality boost
    cyclical_signal = cyclicality.get("cyclical_signal", "Insufficient data")
    if cyclical_signal == "Strong":
        buy_signals.append("Strong cyclical pattern detected")

    # Decision
    if len(buy_signals) > len(sell_signals):
        entry = round(close_price, 2)
        exit_price = round(entry * 1.10, 2)
        recommendation["action"] = "BUY"
        recommendation["entry_price"] = entry
        recommendation["exit_price"] = exit_price
        recommendation["reason"] = "; ".join(buy_signals)
        recommendation["summary"] = (
            f"BUY: Entry={entry}, Exit={exit_price} (+10% in ≤30 days)"
        )
    elif len(sell_signals) > len(buy_signals):
        recommendation["action"] = "SELL"
        recommendation["reason"] = "; ".join(sell_signals)
        recommendation["summary"] = "SELL"
    else:
        recommendation["action"] = "HOLD"
        reasons = buy_signals + sell_signals
        recommendation["reason"] = "; ".join(reasons) if reasons else "No clear signal"
        recommendation["summary"] = "HOLD"

    return recommendation
