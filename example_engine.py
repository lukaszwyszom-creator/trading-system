#!/usr/bin/env python3
"""
Example usage of the trading engine.

This script demonstrates how to set up and run the trading engine
with custom strategies and data feeds.
"""

import sys

from core.engine import TradingEngine
from data.mock_feed import MockDataFeed
from strategy.test_strategy import SimpleTestStrategy
from logger import get_logger


def main():
    """Main example demonstrating the trading engine."""
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("Trading Engine Example")
    print("=" * 60)
    
    # 1. Create a data feed (using mock for this example)
    print("\n1. Creating mock data feed...")
    data_feed = MockDataFeed()
    print("   ✓ Data feed created")
    
    # 2. Create strategies
    print("\n2. Creating trading strategies...")
    strategies = [
        SimpleTestStrategy("momentum_strategy", signal_probability=0.15),
        SimpleTestStrategy("mean_reversion_strategy", signal_probability=0.10),
    ]
    print(f"   ✓ Created {len(strategies)} strategies")
    
    # 3. Create the trading engine
    print("\n3. Creating trading engine...")
    engine = TradingEngine(
        data_feed=data_feed,
        strategies=strategies,
        heartbeat_interval=1.0  # 1 second between iterations
    )
    print(f"   ✓ Engine created: {engine}")
    
    # 4. Start the engine
    print("\n4. Starting trading engine...")
    engine.start()
    print("   ✓ Engine started")
    
    # 5. Run for a limited number of iterations
    print("\n5. Running trading loop (10 iterations)...")
    print("   Watch for generated signals...\n")
    
    try:
        engine.run_loop(max_iterations=10)
    except KeyboardInterrupt:
        print("\n   Interrupted by user")
    
    print("\n6. Engine stopped")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nCheck the logs directory for detailed logs:")
    print("  - logs/trading_system.log")
    print("  - logs/trade_journal.log")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Example failed: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {e}")
        sys.exit(1)
