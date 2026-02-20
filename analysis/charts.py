"""
Chart generation module.

Produces a multi-panel figure with price/moving-averages, volume, RSI,
MACD, and Bollinger Bands and saves it to a PNG file.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend – safe for scripts
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional


def generate_charts(df: pd.DataFrame, ticker: str, output_dir: str = ".") -> str:
    """
    Generate a multi-panel technical analysis chart and save it as a PNG.

    The chart contains five panels:
    1. Closing price with SMA50, SMA200, and Bollinger Bands.
    2. Volume (bar chart).
    3. RSI with overbought / oversold reference lines.
    4. MACD line, signal line, and histogram.
    5. OBV (On-Balance Volume).

    Args:
        df: Enriched OHLCV DataFrame produced by ``compute_indicators``.
        ticker: Stock ticker symbol used in the chart title and filename.
        output_dir: Directory where the PNG file will be saved (default: cwd).

    Returns:
        Absolute path of the saved PNG file.
    """
    os.makedirs(output_dir, exist_ok=True)

    close = df["Close"].squeeze()
    dates = df.index

    fig, axes = plt.subplots(
        5, 1, figsize=(14, 18), sharex=True,
        gridspec_kw={"height_ratios": [3, 1, 1, 1, 1]},
    )
    fig.suptitle(f"{ticker} – Technical Analysis", fontsize=16, fontweight="bold")

    # --- Panel 1: Price + Moving Averages + Bollinger Bands ---
    ax1 = axes[0]
    ax1.plot(dates, close, label="Close", color="black", linewidth=1.2)
    if "SMA_50" in df.columns:
        ax1.plot(dates, df["SMA_50"], label="SMA 50", color="blue", linewidth=1.0)
    if "SMA_200" in df.columns:
        ax1.plot(dates, df["SMA_200"], label="SMA 200", color="red", linewidth=1.0)
    if "Bollinger_Upper" in df.columns:
        ax1.plot(
            dates, df["Bollinger_Upper"], label="BB Upper",
            color="grey", linewidth=0.8, linestyle="--",
        )
        ax1.plot(
            dates, df["Bollinger_Lower"], label="BB Lower",
            color="grey", linewidth=0.8, linestyle="--",
        )
        ax1.fill_between(
            dates,
            df["Bollinger_Lower"],
            df["Bollinger_Upper"],
            alpha=0.05,
            color="grey",
        )
    ax1.set_ylabel("Price")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # --- Panel 2: Volume ---
    ax2 = axes[1]
    ax2.bar(dates, df["Volume"], color="steelblue", alpha=0.6, width=0.8)
    ax2.set_ylabel("Volume")
    ax2.grid(True, alpha=0.3)

    # --- Panel 3: RSI ---
    ax3 = axes[2]
    ax3.plot(dates, df["RSI"], color="purple", linewidth=1.0)
    ax3.axhline(70, color="red", linestyle="--", linewidth=0.8, label="Overbought (70)")
    ax3.axhline(30, color="green", linestyle="--", linewidth=0.8, label="Oversold (30)")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI")
    ax3.legend(loc="upper left", fontsize=8)
    ax3.grid(True, alpha=0.3)

    # --- Panel 4: MACD ---
    ax4 = axes[3]
    ax4.plot(dates, df["MACD"], label="MACD", color="blue", linewidth=1.0)
    ax4.plot(dates, df["MACD_Signal"], label="Signal", color="orange", linewidth=1.0)
    ax4.bar(
        dates, df["MACD_Hist"],
        color=df["MACD_Hist"].apply(lambda x: "green" if x >= 0 else "red"),
        alpha=0.4,
        width=0.8,
    )
    ax4.axhline(0, color="black", linewidth=0.5)
    ax4.set_ylabel("MACD")
    ax4.legend(loc="upper left", fontsize=8)
    ax4.grid(True, alpha=0.3)

    # --- Panel 5: OBV ---
    ax5 = axes[4]
    ax5.plot(dates, df["OBV"], color="teal", linewidth=1.0)
    ax5.set_ylabel("OBV")
    ax5.grid(True, alpha=0.3)

    # Format x-axis dates
    ax5.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax5.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()

    output_path = os.path.abspath(os.path.join(output_dir, f"{ticker}_analysis.png"))
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return output_path
