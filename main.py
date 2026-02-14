import yfinance as yf
import pandas as pd
import sys

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def print_rsi_signal(rsi):
    if rsi is None or pd.isna(rsi):
        print("Not enough data to calculate RSI.")
    elif rsi < 30:
        print(f"RSI: {rsi:.2f} - BUY signal")
    elif rsi > 70:
        print(f"RSI: {rsi:.2f} - SELL signal")
    else:
        print(f"RSI: {rsi:.2f} - HOLD signal")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER>")
        sys.exit(1)
    ticker = sys.argv[1]
    data = yf.download(ticker, period="2mo", interval="1d")
    if data.empty:
        print("No data found for ticker.")
        sys.exit(1)
    close = data['Close']
    rsi_series = calculate_rsi(close)
    latest_rsi = rsi_series.iloc[-1]
    # Ensure latest_rsi is a scalar, not a Series
    if hasattr(latest_rsi, 'item'):
        try:
            latest_rsi = latest_rsi.item()
        except Exception:
            pass
    print_rsi_signal(latest_rsi)

if __name__ == "__main__":
    main()
