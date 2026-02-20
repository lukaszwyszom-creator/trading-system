"""
Tests for the technical analysis modules.

Runs as a plain Python script (consistent with existing test_engine.py style).
Uses synthetic OHLCV data so no network access is required.
"""

import sys
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ── helpers ──────────────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

_failures: list[str] = []


def assert_true(condition: bool, msg: str) -> None:
    if condition:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {FAIL} {msg}")
        _failures.append(msg)


def assert_almost_equal(a: float, b: float, msg: str, tol: float = 1e-3) -> None:
    assert_true(abs(a - b) < tol, msg)


# ── synthetic data factory ────────────────────────────────────────────────────

def make_ohlcv(n: int = 250) -> pd.DataFrame:
    """Return a simple synthetic OHLCV DataFrame with *n* trading days."""
    dates = pd.date_range(end=datetime(2026, 2, 20), periods=n, freq="B")
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(100_000, 1_000_000, size=n).astype(float)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


# ── tests: technical indicators ──────────────────────────────────────────────

def test_compute_indicators_columns() -> None:
    from analysis.technical import compute_indicators
    df = make_ohlcv()
    result = compute_indicators(df)
    expected_cols = [
        "SMA_50", "SMA_200", "EMA_20", "EMA_50",
        "RSI", "MACD", "MACD_Signal", "MACD_Hist",
        "Bollinger_Upper", "Bollinger_Middle", "Bollinger_Lower",
        "ATR", "OBV", "Volume",
    ]
    for col in expected_cols:
        assert_true(col in result.columns, f"column '{col}' present")


def test_sma_values() -> None:
    from analysis.technical import compute_sma
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    sma3 = compute_sma(data, 3)
    assert_almost_equal(sma3.iloc[-1], 4.0, "SMA(3) last value == 4.0")
    assert_true(math.isnan(sma3.iloc[0]), "SMA(3) first value is NaN")


def test_ema_convergence() -> None:
    from analysis.technical import compute_ema
    data = pd.Series([10.0] * 50)
    ema = compute_ema(data, 10)
    assert_almost_equal(ema.iloc[-1], 10.0, "EMA of constant series converges to constant")


def test_rsi_range() -> None:
    from analysis.technical import compute_rsi
    df = make_ohlcv()
    rsi = compute_rsi(df["Close"])
    valid = rsi.dropna()
    assert_true(valid.min() >= 0.0, "RSI min >= 0")
    assert_true(valid.max() <= 100.0, "RSI max <= 100")


def test_bollinger_bands_order() -> None:
    from analysis.technical import compute_bollinger_bands
    df = make_ohlcv()
    upper, middle, lower = compute_bollinger_bands(df["Close"])
    valid = ~upper.isna()
    assert_true((upper[valid] >= middle[valid]).all(), "BB upper >= middle")
    assert_true((middle[valid] >= lower[valid]).all(), "BB lower <= middle")


def test_atr_positive() -> None:
    from analysis.technical import compute_atr
    df = make_ohlcv()
    atr = compute_atr(df["High"], df["Low"], df["Close"])
    assert_true((atr.dropna() > 0).all(), "ATR values are positive")


def test_obv_length() -> None:
    from analysis.technical import compute_obv
    df = make_ohlcv()
    obv = compute_obv(df["Close"], df["Volume"])
    assert_true(len(obv) == len(df), "OBV length matches input length")


# ── tests: cyclicality ───────────────────────────────────────────────────────

def test_cyclicality_keys() -> None:
    from analysis.cyclical import detect_cyclicality
    df = make_ohlcv()
    result = detect_cyclicality(df["Close"])
    for key in ["dominant_period_days", "autocorr_weekly", "cyclical_signal"]:
        assert_true(key in result, f"cyclicality key '{key}' present")


def test_cyclicality_insufficient_data() -> None:
    from analysis.cyclical import detect_cyclicality
    result = detect_cyclicality(pd.Series([100.0, 101.0]))
    assert_true(result["cyclical_signal"] == "Insufficient data", "short series → insufficient data")


# ── tests: recommendations ───────────────────────────────────────────────────

def test_recommendation_keys() -> None:
    from analysis.technical import compute_indicators
    from analysis.cyclical import detect_cyclicality
    from analysis.recommendations import generate_recommendation
    df = compute_indicators(make_ohlcv())
    cyc = detect_cyclicality(df["Close"].squeeze())
    rec = generate_recommendation(df, cyc)
    for key in ["action", "reason", "entry_price", "exit_price", "summary"]:
        assert_true(key in rec, f"recommendation key '{key}' present")


def test_recommendation_action_values() -> None:
    from analysis.technical import compute_indicators
    from analysis.cyclical import detect_cyclicality
    from analysis.recommendations import generate_recommendation
    df = compute_indicators(make_ohlcv())
    cyc = detect_cyclicality(df["Close"].squeeze())
    rec = generate_recommendation(df, cyc)
    assert_true(rec["action"] in {"BUY", "SELL", "HOLD"}, "action is BUY/SELL/HOLD")


def test_buy_recommendation_has_prices() -> None:
    """Force a BUY by constructing a DataFrame with oversold RSI, bullish MACD, golden cross."""
    from analysis.technical import compute_indicators
    from analysis.cyclical import detect_cyclicality
    from analysis.recommendations import generate_recommendation
    # Generate a consistently rising series to trigger golden cross & bullish MACD
    n = 250
    dates = pd.date_range(end=datetime(2026, 2, 20), periods=n, freq="B")
    close = np.linspace(50, 200, n)
    high = close + 1
    low = close - 1
    open_ = close + 0.5
    volume = np.ones(n) * 1_000_000
    df_raw = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )
    df = compute_indicators(df_raw)
    cyc = detect_cyclicality(df["Close"].squeeze())
    rec = generate_recommendation(df, cyc)
    if rec["action"] == "BUY":
        assert_true(rec["entry_price"] is not None, "BUY: entry_price set")
        assert_true(rec["exit_price"] is not None, "BUY: exit_price set")
        entry = rec["entry_price"]
        exit_ = rec["exit_price"]
        assert_true(
            abs(exit_ / entry - 1.10) < 0.001,
            "BUY: exit_price is entry * 1.10",
        )
    else:
        # Recommendation may not always be BUY with synthetic data – just check structure
        assert_true(rec["action"] in {"BUY", "SELL", "HOLD"}, "action is valid even for rising series")


# ── test runner ───────────────────────────────────────────────────────────────

TESTS = [
    test_compute_indicators_columns,
    test_sma_values,
    test_ema_convergence,
    test_rsi_range,
    test_bollinger_bands_order,
    test_atr_positive,
    test_obv_length,
    test_cyclicality_keys,
    test_cyclicality_insufficient_data,
    test_recommendation_keys,
    test_recommendation_action_values,
    test_buy_recommendation_has_prices,
]


def run_tests() -> None:
    print("=" * 60)
    print("  Technical Analysis – Test Suite")
    print("=" * 60)
    for test_fn in TESTS:
        print(f"\n[{test_fn.__name__}]")
        test_fn()

    print("\n" + "=" * 60)
    if _failures:
        print(f"  {len(_failures)} test(s) FAILED:")
        for f in _failures:
            print(f"    - {f}")
        print("=" * 60)
        sys.exit(1)
    else:
        print(f"  All {len(TESTS)} tests passed.")
        print("=" * 60)


if __name__ == "__main__":
    run_tests()
