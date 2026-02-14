"""
Mock data feed implementation for testing and development.

This module provides a simple mock implementation of MarketDataFeed
that generates simulated price data. Useful for testing without
connecting to real data sources.
"""

import random
from typing import Optional, Dict

from data.data_feed import MarketDataFeed


class MockDataFeed(MarketDataFeed):
    """
    Mock market data feed for testing.
    
    Generates simulated price data for testing purposes.
    Prices are randomly generated around a base price with small variations.
    
    Attributes:
        _connected: Connection status flag
        _prices: Dictionary of current prices by symbol
    """
    
    def __init__(self) -> None:
        """Initialize mock data feed with base prices."""
        self._connected: bool = False
        self._prices: Dict[str, float] = {
            "AAPL": 150.0,
            "MSFT": 300.0,
            "GOOGL": 2800.0,
            "AMZN": 3200.0,
            "TSLA": 700.0,
        }
    
    def connect(self) -> None:
        """Establish mock connection."""
        if self._connected:
            raise ConnectionError("Already connected")
        self._connected = True
    
    def disconnect(self) -> None:
        """Close mock connection."""
        self._connected = False
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get simulated price for symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Simulated price with random variation
            
        Raises:
            ConnectionError: If not connected
            ValueError: If symbol not supported
        """
        if not self._connected:
            raise ConnectionError("Not connected to data feed")
        
        if symbol not in self._prices:
            raise ValueError(f"Symbol {symbol} not supported by mock feed")
        
        # Generate price with small random variation (-1% to +1%)
        base_price = self._prices[symbol]
        variation = random.uniform(-0.01, 0.01)
        price = base_price * (1 + variation)
        
        # Update base price for next call (simulate price movement)
        self._prices[symbol] = price
        
        return round(price, 2)
    
    @property
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
