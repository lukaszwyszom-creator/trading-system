#!/usr/bin/env python3
"""
Test script for the logging module.

This script demonstrates and tests the logging functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logger import get_logger, TradeEvent


def test_basic_logging():
    """Test basic logging functionality."""
    print("=" * 60)
    print("Testing basic logging functionality")
    print("=" * 60)
    
    logger = get_logger("test_module")
    
    logger.debug("This is a debug message", component="test")
    logger.info("This is an info message", component="test")
    logger.warning("This is a warning message", component="test")
    logger.error("This is an error message", component="test")
    
    print("\n✓ Basic logging test completed")


def test_trade_journal():
    """Test trade journal functionality."""
    print("\n" + "=" * 60)
    print("Testing trade journal functionality")
    print("=" * 60)
    
    logger = get_logger("trade_test")
    
    # Test signal event
    signal_event = TradeEvent(
        symbol="AAPL",
        side="BUY",
        qty=100,
        price=150.25,
        strategy_id="RSI_STRATEGY",
        event_type="SIGNAL",
        message="RSI below 30"
    )
    logger.trade_event(signal_event)
    print("✓ Logged SIGNAL event")
    
    # Test order event
    order_event = TradeEvent(
        symbol="AAPL",
        side="BUY",
        qty=100,
        price=150.30,
        strategy_id="RSI_STRATEGY",
        event_type="ORDER",
        message="Order submitted"
    )
    logger.trade_event(order_event)
    print("✓ Logged ORDER event")
    
    # Test fill event
    fill_event = TradeEvent(
        symbol="AAPL",
        side="BUY",
        qty=100,
        price=150.28,
        strategy_id="RSI_STRATEGY",
        event_type="FILL",
        message="Order filled"
    )
    logger.trade_event(fill_event)
    print("✓ Logged FILL event")
    
    # Test error event
    error_event = TradeEvent(
        symbol="AAPL",
        side="SELL",
        strategy_id="RSI_STRATEGY",
        event_type="ERROR",
        message="Insufficient balance"
    )
    logger.trade_event(error_event)
    print("✓ Logged ERROR event")
    
    print("\n✓ Trade journal test completed")


def test_multiple_loggers():
    """Test multiple logger instances."""
    print("\n" + "=" * 60)
    print("Testing multiple logger instances")
    print("=" * 60)
    
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    logger3 = get_logger("module1")  # Should return cached instance
    
    logger1.info("Message from module1")
    logger2.info("Message from module2")
    
    # Verify logger3 is the same instance as logger1
    assert logger1 is logger3, "Logger caching not working"
    print("✓ Logger caching verified")
    
    print("\n✓ Multiple loggers test completed")


def verify_log_files():
    """Verify that log files were created."""
    print("\n" + "=" * 60)
    print("Verifying log files")
    print("=" * 60)
    
    log_dir = Path("./logs")
    
    if not log_dir.exists():
        print("✗ Log directory not created")
        return False
    
    print(f"✓ Log directory exists: {log_dir}")
    
    app_log = log_dir / "trading_system.log"
    trade_log = log_dir / "trade_journal.log"
    
    if app_log.exists():
        print(f"✓ Application log exists: {app_log}")
        size = app_log.stat().st_size
        print(f"  Size: {size} bytes")
    else:
        print(f"✗ Application log not found: {app_log}")
    
    if trade_log.exists():
        print(f"✓ Trade journal exists: {trade_log}")
        size = trade_log.stat().st_size
        print(f"  Size: {size} bytes")
    else:
        print(f"✗ Trade journal not found: {trade_log}")
    
    print("\n✓ Log files verification completed")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LOGGER MODULE TEST SUITE")
    print("=" * 60)
    
    try:
        test_basic_logging()
        test_trade_journal()
        test_multiple_loggers()
        verify_log_files()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nCheck the ./logs directory for generated log files:")
        print("  - trading_system.log (structured JSON logs)")
        print("  - trade_journal.log (trade events)")
        print()
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
