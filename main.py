"""
Stock technical analysis CLI.

Usage:
    python main.py <TICKER> [DAYS]

Arguments:
    TICKER  Exchange ticker symbol (e.g. AAPL, MSFT, PKN.WA).
    DAYS    Number of calendar days of history to analyse (default: 365).

Outputs:
    - <TICKER>_analysis.csv  – table of indicator values + recommendation.
    - <TICKER>_analysis.png  – multi-panel technical chart.
    - Console summary of the latest indicator values and recommendation.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import yfinance as yf
import pandas as pd

from analysis.technical import compute_indicators
from analysis.cyclical import detect_cyclicality
from analysis.recommendations import generate_recommendation
from analysis.charts import generate_charts


# ── helpers ──────────────────────────────────────────────────────────────────

def _scalar(val: object) -> Optional[float]:
    """Safely convert a potentially Series-wrapped value to a Python float."""
    if val is None:
        return None
    if hasattr(val, "item"):
        try:
            return float(val.item())
        except Exception:
            pass
    try:
        return float(val)  # type: ignore[arg-type]
    except Exception:
        return None


def _download_data(ticker: str, days: int) -> pd.DataFrame:
    """
    Download OHLCV data via yfinance for the given ticker and time window.

    Args:
        ticker: Exchange ticker symbol.
        days: Number of calendar days of history to fetch.

    Returns:
        OHLCV DataFrame indexed by date.

    Raises:
        SystemExit: If no data is returned for the ticker.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    data = yf.download(
        ticker,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if data.empty:
        print(f"No data found for ticker '{ticker}'. Please check the symbol.")
        sys.exit(1)

    # Flatten MultiIndex columns produced by yfinance for a single ticker
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data


def _build_results_table(df: pd.DataFrame, recommendation_summary: str) -> pd.DataFrame:
    """
    Build the output CSV table from the enriched indicator DataFrame.

    Args:
        df: DataFrame produced by ``compute_indicators``.
        recommendation_summary: One-line recommendation string.

    Returns:
        DataFrame matching the required CSV schema.
    """
    cols = {
        "SMA_50": "SMA_50",
        "SMA_200": "SMA_200",
        "RSI": "RSI",
        "MACD_Signal": "MACD_Signal",
        "Bollinger_Upper": "Bollinger_Upper",
        "Bollinger_Lower": "Bollinger_Lower",
        "ATR": "ATR",
        "OBV": "OBV",
        "Volume": "Volume",
    }
    out = pd.DataFrame(index=df.index)
    for col, label in cols.items():
        out[label] = df[col] if col in df.columns else pd.NA
    out["Recommendation"] = ""
    if not out.empty:
        out.iloc[-1, out.columns.get_loc("Recommendation")] = recommendation_summary
    return out


def _print_summary(
    ticker: str,
    df: pd.DataFrame,
    cyclicality: dict,
    recommendation: dict,
) -> None:
    """Print a human-readable analysis summary to stdout."""
    last = df.iloc[-1]

    def fmt(col: str) -> str:
        val = _scalar(last.get(col))
        return f"{val:.4f}" if val is not None else "N/A"

    print("\n" + "=" * 60)
    print(f"  Technical Analysis – {ticker}")
    print("=" * 60)
    print(f"  Date          : {df.index[-1].date()}")
    print(f"  Close         : {fmt('Close')}")
    print(f"  SMA 50        : {fmt('SMA_50')}")
    print(f"  SMA 200       : {fmt('SMA_200')}")
    print(f"  EMA 20        : {fmt('EMA_20')}")
    print(f"  EMA 50        : {fmt('EMA_50')}")
    print(f"  RSI           : {fmt('RSI')}")
    print(f"  MACD          : {fmt('MACD')}")
    print(f"  MACD Signal   : {fmt('MACD_Signal')}")
    print(f"  Bollinger Up  : {fmt('Bollinger_Upper')}")
    print(f"  Bollinger Low : {fmt('Bollinger_Lower')}")
    print(f"  ATR           : {fmt('ATR')}")
    print(f"  OBV           : {fmt('OBV')}")
    print(f"  Volume        : {fmt('Volume')}")
    print("-" * 60)
    print(f"  Cyclical Signal    : {cyclicality.get('cyclical_signal', 'N/A')}")
    dominant = cyclicality.get("dominant_period_days")
    print(f"  Dominant Period    : {dominant} days" if dominant else "  Dominant Period    : N/A")
    print("-" * 60)
    action = recommendation["action"]
    print(f"  Recommendation     : {action}")
    if action == "BUY":
        print(f"  Entry Price        : {recommendation['entry_price']}")
        print(f"  Exit Price (≥+10%) : {recommendation['exit_price']}")
        print(f"  Horizon            : ≤{recommendation['horizon_days']} days")
    if recommendation["reason"]:
        print(f"  Reason             : {recommendation['reason']}")
    print("=" * 60 + "\n")


# ── main entry point ──────────────────────────────────────────────────────────

def main() -> None:
    """Run the full technical analysis pipeline for a given ticker."""
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER> [DAYS]")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    days = int(sys.argv[2]) if len(sys.argv) >= 3 else 365

    # 1. Download data
    raw_data = _download_data(ticker, days)

    # 2. Compute all technical indicators
    df = compute_indicators(raw_data)

    # 3. Detect cyclical patterns
    close = df["Close"].squeeze()
    cyclicality = detect_cyclicality(close)

    # 4. Generate recommendation
    recommendation = generate_recommendation(df, cyclicality)

    # 5. Print summary to console
    _print_summary(ticker, df, cyclicality, recommendation)

    # 6. Save results CSV
    results = _build_results_table(df, recommendation["summary"])
    csv_path = f"{ticker}_analysis.csv"
    results.to_csv(csv_path)
    print(f"Results saved to: {os.path.abspath(csv_path)}")

    # 7. Generate and save charts
    chart_path = generate_charts(df, ticker)
    print(f"Chart saved to  : {chart_path}")


if __name__ == "__main__":
    main()
