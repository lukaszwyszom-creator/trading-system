"""
Market data feed interface for the trading system.

This module defines the abstract base class for market data providers.
Implementations can be synchronous or asynchronous.
"""

from abc import ABC, abstractmethod
from typing import Optional


class MarketDataFeed(ABC):
    """
    Abstract base class for market data feeds.
    
    This interface defines the contract for market data providers.
    Implementations should handle connection management and provide
    real-time or historical price data.
    
    The interface is designed to be async-friendly but sync compatible,
    allowing for both synchronous and asynchronous implementations.
    """
    
    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the data source.
        
        This method should handle authentication, websocket connections,
        or any other setup required to start receiving data.
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the data source.
        
        This method should clean up resources, close websockets,
        and perform any necessary cleanup operations.
        """
        pass
    
    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest price for a given symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL', 'BTCUSD')
            
        Returns:
            Latest price as float, or None if price unavailable
            
        Raises:
            ValueError: If symbol is invalid or not supported
            ConnectionError: If not connected to data source
        """
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if feed is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
