"""
Base strategy interface for the trading system.

This module defines the base class for trading strategies.
All strategies should inherit from BaseStrategy and implement
the on_price_update method.
"""

from abc import ABC, abstractmethod
from typing import Optional

from models.signal import TradingSignal


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    This class defines the interface that all trading strategies must implement.
    Strategies receive price updates and generate trading signals based on
    their internal logic and indicators.
    
    Attributes:
        strategy_id: Unique identifier for this strategy instance
    """
    
    def __init__(self, strategy_id: str) -> None:
        """
        Initialize the strategy.
        
        Args:
            strategy_id: Unique identifier for this strategy
        """
        self.strategy_id: str = strategy_id
    
    @abstractmethod
    def on_price_update(self, symbol: str, price: float) -> Optional[TradingSignal]:
        """
        Process a price update and generate a trading signal if applicable.
        
        This method is called by the trading engine whenever a new price
        is received for a symbol. The strategy should analyze the price
        and return a trading signal if the strategy conditions are met.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTCUSD')
            price: Current price for the symbol
            
        Returns:
            TradingSignal if a trading action should be taken (BUY, SELL, HOLD),
            or None if no signal is generated
        """
        pass
    
    def reset(self) -> None:
        """
        Reset the strategy state.
        
        This method can be overridden by subclasses to reset any internal
        state, indicators, or historical data. Called when the strategy
        needs to be reinitialized.
        """
        pass
    
    def __repr__(self) -> str:
        """Return string representation of strategy."""
        return f"{self.__class__.__name__}(strategy_id='{self.strategy_id}')"
