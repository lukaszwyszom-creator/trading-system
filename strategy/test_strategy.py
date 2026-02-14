"""
Simple test strategy for testing the trading engine.

This module provides a basic strategy that generates random signals
for testing purposes.
"""

import random
from datetime import datetime
from typing import Optional

from strategy.base import BaseStrategy
from models.signal import TradingSignal


class SimpleTestStrategy(BaseStrategy):
    """
    Simple test strategy that generates random signals.
    
    This strategy is for testing purposes only. It randomly generates
    BUY, SELL, or HOLD signals with low probability to avoid flooding
    the system with signals.
    """
    
    def __init__(self, strategy_id: str, signal_probability: float = 0.05) -> None:
        """
        Initialize the test strategy.
        
        Args:
            strategy_id: Unique identifier for this strategy
            signal_probability: Probability of generating a signal (0.0 to 1.0)
        """
        super().__init__(strategy_id)
        self.signal_probability = signal_probability
    
    def on_price_update(self, symbol: str, price: float) -> Optional[TradingSignal]:
        """
        Generate random signals for testing.
        
        Args:
            symbol: Trading symbol
            price: Current price
            
        Returns:
            Random trading signal or None
        """
        # Generate signal with low probability
        if random.random() > self.signal_probability:
            return None
        
        # Randomly choose signal type
        side = random.choice(["BUY", "SELL", "HOLD"])
        
        # Generate quantity for BUY/SELL
        qty = None if side == "HOLD" else random.randint(1, 100)
        
        return TradingSignal(
            symbol=symbol,
            side=side,
            qty=qty,
            strategy_id=self.strategy_id,
            timestamp=datetime.utcnow(),
            price=price
        )
