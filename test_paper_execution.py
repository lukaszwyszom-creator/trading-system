#!/usr/bin/env python3
"""
Test script for paper execution handler, positions, and portfolio.

This script demonstrates and tests the paper trading functionality
including execution, position tracking, and P&L calculations.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import portfolio

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.signal import TradingSignal
from models.fill import FillEvent
from portfolio.positions import Position, Portfolio
from execution.paper import PaperExecutionHandler
from core.engine import TradingEngine
from data.mock_feed import MockDataFeed
from strategy.test_strategy import SimpleTestStrategy


def test_fill_event():
    """Test FillEvent creation and validation."""
    print("=" * 60)
    print("Testing FillEvent")
    print("=" * 60)
    
    # Test valid fill
    fill = FillEvent(
        timestamp=datetime.now(timezone.utc),
        symbol="AAPL",
        side="BUY",
        qty=100.0,
        price=150.25,
        strategy_id="test_strategy",
        fee=15.03,
        slippage=0.05
    )
    print(f"✓ Created fill event: {fill}")
    
    # Test to_trade_event conversion
    trade_event = fill.to_trade_event(event_type="FILL")
    assert trade_event.event_type == "FILL"
    assert trade_event.symbol == "AAPL"
    print(f"✓ Converted to trade event: {trade_event.to_dict()}")
    
    # Test invalid side
    try:
        invalid_fill = FillEvent(
            timestamp=datetime.now(timezone.utc),
            symbol="AAPL",
            side="HOLD",
            qty=100.0,
            price=150.25,
            strategy_id="test_strategy"
        )
        print("✗ Should have raised ValueError for HOLD side")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected HOLD side: {e}")
    
    # Test invalid quantity
    try:
        invalid_fill = FillEvent(
            timestamp=datetime.now(timezone.utc),
            symbol="AAPL",
            side="BUY",
            qty=-100.0,
            price=150.25,
            strategy_id="test_strategy"
        )
        print("✗ Should have raised ValueError for negative qty")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected negative qty: {e}")
    
    print("\n✓ FillEvent tests passed")
    return True


def test_position():
    """Test Position model."""
    print("\n" + "=" * 60)
    print("Testing Position")
    print("=" * 60)
    
    # Create empty position
    pos = Position(symbol="AAPL")
    assert pos.qty == 0.0
    assert pos.avg_price == 0.0
    print(f"✓ Created empty position: {pos}")
    
    # Buy 100 shares at $150
    pos.update(100.0, 150.0)
    assert pos.qty == 100.0
    assert pos.avg_price == 150.0
    print(f"✓ After buying 100 @ 150: {pos}")
    
    # Buy 50 more at $160 (average should update)
    pos.update(50.0, 160.0)
    expected_avg = (100 * 150 + 50 * 160) / 150
    assert pos.qty == 150.0
    assert abs(pos.avg_price - expected_avg) < 0.01
    print(f"✓ After buying 50 @ 160: {pos}")
    print(f"  Average price: {pos.avg_price:.2f} (expected: {expected_avg:.2f})")
    
    # Sell 50 shares (partial close)
    pos.update(-50.0, 170.0)
    assert pos.qty == 100.0
    assert abs(pos.avg_price - expected_avg) < 0.01  # avg_price unchanged
    print(f"✓ After selling 50 @ 170: {pos}")
    
    # Calculate unrealized P&L at current price
    current_price = 165.0
    unrealized_pnl = pos.calculate_unrealized_pnl(current_price)
    expected_pnl = 100.0 * (current_price - pos.avg_price)
    assert abs(unrealized_pnl - expected_pnl) < 0.01
    print(f"✓ Unrealized P&L at {current_price}: {unrealized_pnl:.2f} (expected: {expected_pnl:.2f})")
    
    # Close position
    pos.update(-100.0, 165.0)
    assert pos.qty == 0.0
    assert pos.avg_price == 0.0
    print(f"✓ After closing position: {pos}")
    
    print("\n✓ Position tests passed")
    return True


def test_portfolio():
    """Test Portfolio model."""
    print("\n" + "=" * 60)
    print("Testing Portfolio")
    print("=" * 60)
    
    # Create portfolio with initial cash
    portfolio = Portfolio(initial_cash=100000.0)
    assert portfolio.cash == 100000.0
    assert portfolio.realized_pnl == 0.0
    print(f"✓ Created portfolio: {portfolio}")
    
    # Buy AAPL
    portfolio.update_position("AAPL", 100.0, 150.0)
    portfolio.cash -= 15.0
    portfolio.realized_pnl -= 15.0
    assert portfolio.cash < 100000.0
    expected_cash = 100000.0 - (100.0 * 150.0) - 15.0
    assert abs(portfolio.cash - expected_cash) < 0.01
    print(f"✓ After buying 100 AAPL @ 150: cash={portfolio.cash:.2f}")
    
    # Check position
    aapl_pos = portfolio.get_position("AAPL")
    assert aapl_pos.qty == 100.0
    assert aapl_pos.avg_price == 150.0
    print(f"✓ AAPL position: {aapl_pos}")
    
    # Buy MSFT
    portfolio.update_position("MSFT", 50.0, 300.0)
    portfolio.cash -= 15.0
    portfolio.realized_pnl -= 15.0
    print(f"✓ After buying 50 MSFT @ 300: cash={portfolio.cash:.2f}")
    
    # Sell half of AAPL position (realize profit)
    portfolio.update_position("AAPL", -50.0, 160.0)
    portfolio.cash -= 8.0
    portfolio.realized_pnl -= 8.0
    print(f"✓ After selling 50 AAPL @ 160: cash={portfolio.cash:.2f}, realized_pnl={portfolio.realized_pnl:.2f}")
    
    # Calculate unrealized P&L
    current_prices = {"AAPL": 165.0, "MSFT": 310.0}
    unrealized_pnl = portfolio.calculate_unrealized_pnl(current_prices)
    print(f"✓ Unrealized P&L: {unrealized_pnl:.2f}")
    
    # Calculate total equity
    total_equity = portfolio.calculate_total_equity(current_prices)
    print(f"✓ Total equity: {total_equity:.2f}")
    
    # Test insufficient cash
    try:
        portfolio.update_position("GOOGL", 1000.0, 2800.0)
        print("✗ Should have raised ValueError for insufficient cash")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected trade with insufficient cash: {e}")
    
    print("\n✓ Portfolio tests passed")
    return True


def test_paper_execution_handler():
    """Test PaperExecutionHandler."""
    print("\n" + "=" * 60)
    print("Testing PaperExecutionHandler")
    print("=" * 60)
    
    # Create handler with deterministic slippage
    handler = PaperExecutionHandler(
        initial_cash=100000.0,
        commission_rate=0.001,
        slippage_bps=5.0,
        random_seed=42
    )
    print(f"✓ Created handler: {handler}")
    
    # Create a BUY signal
    buy_signal = TradingSignal(
        symbol="AAPL",
        side="BUY",
        qty=100.0,
        strategy_id="test_strategy",
        timestamp=datetime.now(timezone.utc),
        price=150.0
    )
    
    # Execute the signal
    fill = handler.execute(buy_signal)
    assert fill.symbol == "AAPL"
    assert fill.side == "BUY"
    assert fill.qty == 100.0
    assert fill.price >= 150.0  # Should include slippage
    assert fill.fee > 0
    print(f"✓ Executed BUY: {fill}")
    print(f"  Slippage: {fill.slippage:.4f}, Fee: {fill.fee:.2f}")
    
    # Check portfolio state
    assert handler.portfolio.cash < 100000.0
    aapl_pos = handler.portfolio.get_position("AAPL")
    assert aapl_pos.qty == 100.0
    print(f"✓ Portfolio after BUY: cash={handler.portfolio.cash:.2f}, AAPL qty={aapl_pos.qty}")
    
    # Create a SELL signal
    sell_signal = TradingSignal(
        symbol="AAPL",
        side="SELL",
        qty=50.0,
        strategy_id="test_strategy",
        timestamp=datetime.now(timezone.utc),
        price=160.0
    )
    
    # Execute the signal
    fill = handler.execute(sell_signal)
    assert fill.symbol == "AAPL"
    assert fill.side == "SELL"
    assert fill.qty == 50.0
    print(f"✓ Executed SELL: {fill}")
    print(f"  Slippage: {fill.slippage:.4f}, Fee: {fill.fee:.2f}")
    
    # Check realized P&L
    assert handler.portfolio.realized_pnl != 0
    print(f"✓ Realized P&L: {handler.portfolio.realized_pnl:.2f}")
    
    # Test HOLD signal rejection
    hold_signal = TradingSignal(
        symbol="AAPL",
        side="HOLD",
        qty=None,
        strategy_id="test_strategy",
        timestamp=datetime.now(timezone.utc),
        price=160.0
    )
    
    try:
        handler.execute(hold_signal)
        print("✗ Should have raised ValueError for HOLD signal")
        return False
    except ValueError as e:
        print(f"✓ Correctly rejected HOLD signal: {e}")
    
    # Get portfolio summary
    summary = handler.get_portfolio_summary()
    print(f"✓ Portfolio summary: {summary}")
    
    print("\n✓ PaperExecutionHandler tests passed")
    return True


def test_engine_with_execution():
    """Test TradingEngine with PaperExecutionHandler."""
    print("\n" + "=" * 60)
    print("Testing TradingEngine with PaperExecutionHandler")
    print("=" * 60)
    
    # Create components
    feed = MockDataFeed()
    strategies = [SimpleTestStrategy("strategy_1", signal_probability=0.5)]
    handler = PaperExecutionHandler(
        initial_cash=100000.0,
        commission_rate=0.001,
        slippage_bps=5.0,
        random_seed=42
    )
    
    # Create engine with execution handler
    engine = TradingEngine(
        data_feed=feed,
        strategies=strategies,
        heartbeat_interval=0.1,
        execution_handler=handler
    )
    print(f"✓ Created engine with execution handler: {engine}")
    
    # Start and run engine
    engine.start()
    print("✓ Engine started")
    
    # Run for a few iterations
    engine.run_loop(max_iterations=10)
    print("✓ Engine completed 10 iterations")
    
    # Check portfolio state
    summary = handler.get_portfolio_summary()
    print(f"✓ Portfolio summary after trading:")
    print(f"  Cash: {summary['cash']:.2f}")
    print(f"  Realized P&L: {summary['realized_pnl']:.2f}")
    print(f"  Positions: {summary['num_positions']}")
    for pos in summary['positions']:
        print(f"    {pos['symbol']}: qty={pos['qty']}, avg_price={pos['avg_price']:.2f}")
    
    print("\n✓ TradingEngine with execution tests passed")
    return True


def test_buy_sell_lifecycle():
    """Test complete buy/sell lifecycle with P&L tracking."""
    print("\n" + "=" * 60)
    print("Testing Buy/Sell Lifecycle")
    print("=" * 60)
    
    handler = PaperExecutionHandler(
        initial_cash=100000.0,
        commission_rate=0.001,
        slippage_bps=0.0,  # No slippage for deterministic testing
        random_seed=42
    )
    
    initial_cash = handler.portfolio.cash
    print(f"Initial cash: {initial_cash:.2f}")
    
    # Buy 100 shares at $100
    buy_signal = TradingSignal(
        symbol="TEST",
        side="BUY",
        qty=100.0,
        strategy_id="test",
        timestamp=datetime.now(timezone.utc),
        price=100.0
    )
    buy_fill = handler.execute(buy_signal)
    print(f"✓ BUY 100 @ {buy_fill.price:.2f}, fee={buy_fill.fee:.2f}")
    
    # Check position
    pos = handler.portfolio.get_position("TEST")
    assert pos.qty == 100.0
    print(f"  Position: qty={pos.qty}, avg_price={pos.avg_price:.2f}")
    
    # Sell 100 shares at $110 (profit expected)
    sell_signal = TradingSignal(
        symbol="TEST",
        side="SELL",
        qty=100.0,
        strategy_id="test",
        timestamp=datetime.now(timezone.utc),
        price=110.0
    )
    sell_fill = handler.execute(sell_signal)
    print(f"✓ SELL 100 @ {sell_fill.price:.2f}, fee={sell_fill.fee:.2f}")
    
    # Check position is closed
    pos = handler.portfolio.get_position("TEST")
    assert pos.qty == 0.0
    print(f"  Position: qty={pos.qty} (closed)")
    
    # Check realized P&L
    realized_pnl = handler.portfolio.realized_pnl
    print(f"  Realized P&L: {realized_pnl:.2f}")
    
    # Expected: (110 - 100) * 100 = 1000 profit
    # Less fees: buy_fee + sell_fee
    expected_profit = 1000.0 - buy_fill.fee - sell_fill.fee
    print(f"  Expected profit: {expected_profit:.2f}")
    
    # Final cash should be close to initial + profit
    final_cash = handler.portfolio.cash
    print(f"  Final cash: {final_cash:.2f}")
    print(f"  Net change: {final_cash - initial_cash:.2f}")
    
    # Allow small rounding errors
    assert abs((final_cash - initial_cash) - expected_profit) < 0.01
    print("✓ P&L calculation correct!")
    
    print("\n✓ Buy/Sell lifecycle tests passed")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PAPER EXECUTION HANDLER TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("FillEvent", test_fill_event),
        ("Position", test_position),
        ("Portfolio", test_portfolio),
        ("PaperExecutionHandler", test_paper_execution_handler),
        ("Buy/Sell Lifecycle", test_buy_sell_lifecycle),
        ("Engine with Execution", test_engine_with_execution),
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
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
