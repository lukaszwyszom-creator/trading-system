"""
Fill event model for the trading system.

This module defines the FillEvent dataclass used to represent
executed trades in the paper trading system.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from logger import TradeEvent


@dataclass
class FillEvent:
    """
    Represents a filled order (executed trade).
    
    Attributes:
        timestamp: Fill execution timestamp (UTC)
        symbol: Trading symbol (e.g., 'AAPL', 'BTCUSD')
        side: Order side ('BUY', 'SELL')
        qty: Quantity filled
        price: Execution price per unit
        strategy_id: Identifier of the strategy that generated the original signal
        fee: Commission/fee charged for the trade
        slippage: Slippage amount (difference from expected price)
    """
    
    timestamp: datetime
    symbol: str
    side: str
    qty: float
    price: float
    strategy_id: str
    fee: float = 0.0
    slippage: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate fill event data after initialization."""
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid side: {self.side}. Must be BUY or SELL")
        
        if self.qty <= 0:
            raise ValueError(f"Quantity must be positive, got {self.qty}")
        
        if self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")
        
        if self.fee < 0:
            raise ValueError(f"Fee cannot be negative, got {self.fee}")
    
    def to_trade_event(self, event_type: str = "FILL") -> TradeEvent:
        """
        Convert fill event to TradeEvent for journaling.
        
        Args:
            event_type: Type of event (default: "FILL")
            
        Returns:
            TradeEvent instance for logging to trade journal
        """
        return TradeEvent(
            symbol=self.symbol,
            side=self.side,
            qty=self.qty,
            price=self.price,
            strategy_id=self.strategy_id,
            event_type=event_type,
            message=f"Fill executed: {self.qty} @ {self.price:.2f} (fee: {self.fee:.2f}, slippage: {self.slippage:.4f})",
        )
    
    def __repr__(self) -> str:
        """Return string representation of fill event."""
        return (
            f"FillEvent(symbol='{self.symbol}', side='{self.side}', "
            f"qty={self.qty}, price={self.price:.2f}, "
            f"fee={self.fee:.2f}, slippage={self.slippage:.4f}, "
            f"strategy_id='{self.strategy_id}')"
        )
