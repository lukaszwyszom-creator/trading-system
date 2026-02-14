#!/usr/bin/env python3
"""
Test script for the trading engine skeleton.

This script demonstrates and tests the core trading engine functionality
with mock data feeds and test strategies.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import TradingEngine
from data.mock_feed import MockDataFeed
from strategy.test_strategy import SimpleTestStrategy
from logger import get_logger


def test_signal_creation():
    """Test TradingSignal creation and validation."""
    print("=" * 60)
    print("Testing TradingSignal creation")
    print("=" * 60)
    
    from models.signal import TradingSignal
    from datetime import datetime
    
    # Test valid BUY signal
    signal = TradingSignal(
        symbol="AAPL",
        side="BUY",
        qty=100.0,
        strategy_id="test_strategy",
        timestamp=datetime.utcnow(),
        price=150.25
    )
    print(f"✓ Created BUY signal: {signal}")
    
    # Test valid HOLD signal
    hold_signal = TradingSignal(
        symbol="MSFT",
        side="HOLD",
        qty=None,
        strategy_id="test_strategy",
        timestamp=datetime.utcnow()
    )
    print(f"✓ Created HOLD signal: {hold_signal}")
    
    # Test invalid side
    try:
        invalid_signal = TradingSignal(
            symbol="AAPL",
            side="INVALID",
            qty=100.0,
            strategy_id="test_strategy",
            timestamp=datetime.utcnow()
        )
        print("✗ Should have raised ValueError for invalid side")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid side: {e}")
    
    # Test missing quantity for BUY
    try:
        invalid_signal = TradingSignal(
            symbol="AAPL",
            side="BUY",
            qty=None,
            strategy_id="test_strategy",
            timestamp=datetime.utcnow()
        )
        print("✗ Should have raised ValueError for missing qty on BUY")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected missing qty: {e}")
    
    print("\n✓ TradingSignal tests passed")
    return True


def test_data_feed():
    """Test MarketDataFeed interface with MockDataFeed."""
    print("\n" + "=" * 60)
    print("Testing MarketDataFeed interface")
    print("=" * 60)
    
    feed = MockDataFeed()
    
    # Test connection
    assert not feed.is_connected, "Feed should not be connected initially"
    print("✓ Initial state: not connected")
    
    feed.connect()
    assert feed.is_connected, "Feed should be connected after connect()"
    print("✓ Connected successfully")
    
    # Test price retrieval
    price = feed.get_latest_price("AAPL")
    assert price is not None, "Should get price for AAPL"
    assert price > 0, "Price should be positive"
    print(f"✓ Got price for AAPL: ${price:.2f}")
    
    price2 = feed.get_latest_price("MSFT")
    assert price2 is not None, "Should get price for MSFT"
    print(f"✓ Got price for MSFT: ${price2:.2f}")
    
    # Test invalid symbol
    try:
        feed.get_latest_price("INVALID")
        print("✗ Should have raised ValueError for invalid symbol")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid symbol: {e}")
    
    # Test disconnect
    feed.disconnect()
    assert not feed.is_connected, "Feed should be disconnected"
    print("✓ Disconnected successfully")
    
    # Test operation while disconnected
    try:
        feed.get_latest_price("AAPL")
        print("✗ Should have raised ConnectionError when disconnected")
        return False
    except ConnectionError as e:
        print(f"✓ Correctly raised ConnectionError: {e}")
    
    print("\n✓ MarketDataFeed tests passed")
    return True


def test_strategy():
    """Test BaseStrategy interface with SimpleTestStrategy."""
    print("\n" + "=" * 60)
    print("Testing BaseStrategy interface")
    print("=" * 60)
    
    strategy = SimpleTestStrategy("test_strategy_1", signal_probability=1.0)
    
    print(f"✓ Created strategy: {strategy}")
    
    # Test on_price_update
    signal = strategy.on_price_update("AAPL", 150.0)
    if signal:
        print(f"✓ Strategy generated signal: {signal}")
    else:
        print("✓ Strategy returned no signal (also valid)")
    
    print("\n✓ BaseStrategy tests passed")
    return True


def test_trading_engine():
    """Test TradingEngine with mock components."""
    print("\n" + "=" * 60)
    print("Testing TradingEngine")
    print("=" * 60)
    
    logger = get_logger("test_engine")
    
    # Create components
    feed = MockDataFeed()
    strategies = [
        SimpleTestStrategy("strategy_1", signal_probability=0.2),
        SimpleTestStrategy("strategy_2", signal_probability=0.1),
    ]
    
    # Create engine
    engine = TradingEngine(
        data_feed=feed,
        strategies=strategies,
        heartbeat_interval=0.5  # Fast for testing
    )
    print(f"✓ Created engine: {engine}")
    
    # Test initial state
    assert not engine.is_running, "Engine should not be running initially"
    print("✓ Initial state: not running")
    
    # Start engine
    engine.start()
    assert engine.is_running, "Engine should be running after start()"
    print("✓ Engine started successfully")
    
    # Run for a few iterations
    logger.info("Running engine for 5 iterations")
    engine.run_loop(max_iterations=5)
    print("✓ Engine completed 5 iterations")
    
    # Engine should auto-stop after iterations
    assert not engine.is_running, "Engine should stop after max_iterations"
    print("✓ Engine stopped after iterations")
    
    print("\n✓ TradingEngine tests passed")
    return True


def test_engine_error_handling():
    """Test TradingEngine error handling."""
    print("\n" + "=" * 60)
    print("Testing TradingEngine error handling")
    print("=" * 60)
    
    feed = MockDataFeed()
    strategies = [SimpleTestStrategy("strategy_1")]
    
    # Test starting already running engine
    engine = TradingEngine(data_feed=feed, strategies=strategies)
    engine.start()
    
    try:
        engine.start()
        print("✗ Should have raised RuntimeError for already running")
        return False
    except RuntimeError as e:
        print(f"✓ Correctly rejected second start: {e}")
    
    engine.stop()
    
    # Test running without starting
    engine2 = TradingEngine(data_feed=feed, strategies=strategies)
    try:
        engine2.run_loop(max_iterations=1)
        print("✗ Should have raised RuntimeError for not started")
        return False
    except RuntimeError as e:
        print(f"✓ Correctly rejected run without start: {e}")
    
    # Test invalid configuration
    try:
        invalid_engine = TradingEngine(data_feed=feed, strategies=[])
        print("✗ Should have raised ValueError for empty strategies")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected empty strategies: {e}")
    
    try:
        invalid_engine = TradingEngine(
            data_feed=feed,
            strategies=strategies,
            heartbeat_interval=0.0
        )
        print("✗ Should have raised ValueError for invalid heartbeat")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected invalid heartbeat: {e}")
    
    print("\n✓ Error handling tests passed")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TRADING ENGINE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Signal Creation", test_signal_creation),
        ("Data Feed", test_data_feed),
        ("Strategy", test_strategy),
        ("Trading Engine", test_trading_engine),
        ("Error Handling", test_engine_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n✗ {name} test failed")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED")
        print("\nCheck the ./logs directory for generated log files:")
        print("  - trading_system.log (engine logs)")
        print("  - trade_journal.log (trade signals)")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
