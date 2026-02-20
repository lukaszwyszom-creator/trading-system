"""
Technical indicators computation module.

Computes SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, and Volume
for a given OHLCV DataFrame downloaded via yfinance.
"""

import numpy as np
import pandas as pd
from typing import Optional


def compute_sma(close: pd.Series, window: int) -> pd.Series:
    """
    Compute Simple Moving Average.

    Args:
        close: Series of closing prices.
        window: Look-back period in trading days.

    Returns:
        Series of SMA values.
    """
    return close.rolling(window=window).mean()


def compute_ema(close: pd.Series, window: int) -> pd.Series:
    """
    Compute Exponential Moving Average.

    Args:
        close: Series of closing prices.
        window: Span for the EMA calculation.

    Returns:
        Series of EMA values.
    """
    return close.ewm(span=window, adjust=False).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute Relative Strength Index.

    Args:
        close: Series of closing prices.
        period: Look-back period (default 14).

    Returns:
        Series of RSI values in the range [0, 100].
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def compute_macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Compute MACD line, signal line, and histogram.

    Args:
        close: Series of closing prices.
        fast: Fast EMA period (default 12).
        slow: Slow EMA period (default 26).
        signal: Signal EMA period (default 9).

    Returns:
        Tuple of (macd_line, signal_line, histogram) Series.
    """
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger_bands(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Compute Bollinger Bands (upper, middle, lower).

    Args:
        close: Series of closing prices.
        window: Rolling window period (default 20).
        num_std: Number of standard deviations (default 2).

    Returns:
        Tuple of (upper_band, middle_band, lower_band) Series.
    """
    middle = close.rolling(window=window).mean()
    std = close.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def compute_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """
    Compute Average True Range.

    Args:
        high: Series of daily high prices.
        low: Series of daily low prices.
        close: Series of closing prices.
        period: Look-back period (default 14).

    Returns:
        Series of ATR values.
    """
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window=period).mean()


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    Compute On-Balance Volume.

    Args:
        close: Series of closing prices.
        volume: Series of trading volumes.

    Returns:
        Series of OBV values.
    """
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def compute_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators and return an enriched DataFrame.

    The input DataFrame must contain Open, High, Low, Close, Volume columns
    as returned by yfinance.

    Args:
        data: OHLCV DataFrame from yfinance.

    Returns:
        DataFrame with added indicator columns:
        SMA_50, SMA_200, EMA_20, EMA_50, RSI, MACD, MACD_Signal,
        MACD_Hist, Bollinger_Upper, Bollinger_Middle, Bollinger_Lower,
        ATR, OBV, Volume.

    Raises:
        ValueError: If required columns are missing from data.
    """
    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")

    df = data.copy()

    # Flatten MultiIndex columns produced by yfinance when downloading
    # a single ticker (e.g. ("Close", "AAPL") → "Close").
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    volume = df["Volume"].squeeze()

    df["SMA_50"] = compute_sma(close, 50)
    df["SMA_200"] = compute_sma(close, 200)
    df["EMA_20"] = compute_ema(close, 20)
    df["EMA_50"] = compute_ema(close, 50)
    df["RSI"] = compute_rsi(close)

    macd_line, signal_line, histogram = compute_macd(close)
    df["MACD"] = macd_line
    df["MACD_Signal"] = signal_line
    df["MACD_Hist"] = histogram

    upper, middle, lower = compute_bollinger_bands(close)
    df["Bollinger_Upper"] = upper
    df["Bollinger_Middle"] = middle
    df["Bollinger_Lower"] = lower

    df["ATR"] = compute_atr(high, low, close)
    df["OBV"] = compute_obv(close, volume)
    df["Volume"] = volume

    return df
