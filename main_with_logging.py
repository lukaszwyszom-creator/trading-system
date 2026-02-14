"""
Example of integrating the logger with the trading system.

This demonstrates how to use the logger in the main trading application.
"""

import yfinance as yf
import pandas as pd
import sys

from logger import get_logger, TradeEvent


def calculate_rsi(series, period=14):
    """Calculate RSI indicator."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def print_rsi_signal(rsi, ticker, logger):
    """Print RSI signal and log trade event."""
    if rsi is None or pd.isna(rsi):
        message = "Not enough data to calculate RSI."
        logger.warning(message, ticker=ticker)
        print(message)
    elif rsi < 30:
        message = f"RSI: {rsi:.2f} - BUY signal"
        print(message)
        logger.info(message, ticker=ticker, rsi=rsi, signal="BUY")
        
        # Log trade event to journal
        event = TradeEvent(
            symbol=ticker,
            side="BUY",
            strategy_id="RSI_STRATEGY",
            event_type="SIGNAL",
            message=f"RSI below 30: {rsi:.2f}"
        )
        logger.trade_event(event)
        
    elif rsi > 70:
        message = f"RSI: {rsi:.2f} - SELL signal"
        print(message)
        logger.info(message, ticker=ticker, rsi=rsi, signal="SELL")
        
        # Log trade event to journal
        event = TradeEvent(
            symbol=ticker,
            side="SELL",
            strategy_id="RSI_STRATEGY",
            event_type="SIGNAL",
            message=f"RSI above 70: {rsi:.2f}"
        )
        logger.trade_event(event)
        
    else:
        message = f"RSI: {rsi:.2f} - HOLD signal"
        print(message)
        logger.info(message, ticker=ticker, rsi=rsi, signal="HOLD")


def main():
    """Main application entry point."""
    # Get logger for this module
    logger = get_logger(__name__)
    
    logger.info("Trading system started")
    
    if len(sys.argv) < 2:
        logger.error("No ticker provided")
        print("Usage: python main_with_logging.py <TICKER>")
        sys.exit(1)
    
    ticker = sys.argv[1]
    logger.info(f"Processing ticker: {ticker}", ticker=ticker)
    
    try:
        # Download data
        logger.debug(f"Downloading data for {ticker}", ticker=ticker)
        data = yf.download(ticker, period="2mo", interval="1d")
        
        if data.empty:
            logger.error("No data found for ticker", ticker=ticker)
            print("No data found for ticker.")
            sys.exit(1)
        
        logger.info(f"Downloaded {len(data)} data points", ticker=ticker, data_points=len(data))
        
        # Calculate RSI
        close = data['Close']
        rsi_series = calculate_rsi(close)
        latest_rsi = rsi_series.iloc[-1]
        
        # Ensure latest_rsi is a scalar, not a Series
        if hasattr(latest_rsi, 'item'):
            try:
                latest_rsi = latest_rsi.item()
            except Exception:
                pass
        
        # Print signal and log trade event
        print_rsi_signal(latest_rsi, ticker, logger)
        
        logger.info("Trading system completed successfully", ticker=ticker)
        
    except Exception as e:
        logger.error(f"Error processing ticker: {str(e)}", ticker=ticker, error=str(e), exc_info=True)
        
        # Log error event to trade journal
        event = TradeEvent(
            symbol=ticker,
            side="ERROR",
            strategy_id="RSI_STRATEGY",
            event_type="ERROR",
            message=str(e)
        )
        logger.trade_event(event)
        
        raise


if __name__ == "__main__":
    main()
