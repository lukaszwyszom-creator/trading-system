"""
Cyclical pattern detection module.

Uses scipy to detect recurring price-movement patterns within a year
by analysing autocorrelation and dominant frequency components via FFT.
"""

import numpy as np
import pandas as pd
from scipy import signal as sp_signal
from typing import Optional


def detect_cyclicality(close: pd.Series) -> dict:
    """
    Detect recurring cyclical patterns in a closing-price series.

    The function applies a Fast Fourier Transform to the de-trended price
    series and identifies the dominant frequency component.  It also
    computes the Pearson autocorrelation at several lags (weekly, bi-weekly,
    monthly) to surface shorter repeating cycles.

    Args:
        close: Series of closing prices indexed by date (at least 30 rows).

    Returns:
        Dictionary with keys:
        - ``dominant_period_days``: int – length of the dominant cycle
          in trading days (None when too little data).
        - ``autocorr_weekly``: float – autocorrelation at lag-5.
        - ``autocorr_biweekly``: float – autocorrelation at lag-10.
        - ``autocorr_monthly``: float – autocorrelation at lag-21.
        - ``cyclical_signal``: str – qualitative assessment
          ("Strong", "Moderate", "Weak", or "Insufficient data").
    """
    result: dict = {
        "dominant_period_days": None,
        "autocorr_weekly": None,
        "autocorr_biweekly": None,
        "autocorr_monthly": None,
        "cyclical_signal": "Insufficient data",
    }

    prices = close.dropna()

    if len(prices) < 30:
        return result

    # --- Autocorrelation at standard lags ---
    result["autocorr_weekly"] = float(prices.autocorr(lag=5))
    result["autocorr_biweekly"] = float(prices.autocorr(lag=10))
    result["autocorr_monthly"] = float(prices.autocorr(lag=21))

    # --- Dominant frequency via FFT on de-trended returns ---
    returns = prices.pct_change().dropna().values
    if len(returns) < 10:
        return result

    detrended = sp_signal.detrend(returns)
    fft_vals = np.abs(np.fft.rfft(detrended))
    freqs = np.fft.rfftfreq(len(detrended))

    # Exclude DC component (index 0)
    dominant_idx = int(np.argmax(fft_vals[1:]) + 1)
    dominant_freq = float(freqs[dominant_idx])
    if dominant_freq > 0:
        result["dominant_period_days"] = int(round(1.0 / dominant_freq))
    else:
        result["dominant_period_days"] = None

    # --- Qualitative assessment ---
    autocorrs = [
        abs(v)
        for v in [
            result["autocorr_weekly"],
            result["autocorr_biweekly"],
            result["autocorr_monthly"],
        ]
        if v is not None and not np.isnan(v)
    ]
    if autocorrs:
        avg_autocorr = float(np.mean(autocorrs))
        if avg_autocorr >= 0.7:
            result["cyclical_signal"] = "Strong"
        elif avg_autocorr >= 0.4:
            result["cyclical_signal"] = "Moderate"
        else:
            result["cyclical_signal"] = "Weak"

    return result
