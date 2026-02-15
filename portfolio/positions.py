"""
Portfolio management for the trading system.

This module provides Position and Portfolio classes for tracking
positions, cash, and profit/loss in the paper trading system.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Position:
    """
    Represents a position in a single symbol.
    
    Attributes:
        symbol: Trading symbol (e.g., 'AAPL')
        qty: Current quantity held (positive for long, negative for short)
        avg_price: Average entry price per unit
    """
    
    symbol: str
    qty: float = 0.0
    avg_price: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate position data after initialization."""
        if self.qty != 0 and self.avg_price <= 0:
            raise ValueError(f"Average price must be positive when qty is non-zero, got {self.avg_price}")
    
    @property
    def market_value(self) -> float:
        """
        Calculate the market value of the position at current average price.
        
        Returns:
            Market value (qty * avg_price)
        """
        return abs(self.qty) * self.avg_price
    
    def update(self, qty_delta: float, price: float) -> None:
        """
        Update position with a new trade.
        
        Args:
            qty_delta: Change in quantity (positive for buy, negative for sell)
            price: Trade execution price
        
        Raises:
            ValueError: If price is not positive
        """
        if price <= 0:
            raise ValueError(f"Price must be positive, got {price}")
        
        new_qty = self.qty + qty_delta
        
        # Calculate new average price
        if new_qty == 0:
            # Position closed
            self.avg_price = 0.0
        elif self.qty == 0:
            # Opening a new position
            self.avg_price = price
        elif (self.qty > 0 and qty_delta > 0) or (self.qty < 0 and qty_delta < 0):
            # Adding to existing position (same direction)
            total_cost = (abs(self.qty) * self.avg_price) + (abs(qty_delta) * price)
            self.avg_price = total_cost / abs(new_qty)
        elif (self.qty > 0 and qty_delta < 0) or (self.qty < 0 and qty_delta > 0):
            # Reducing or reversing position (opposite direction)
            if abs(new_qty) < abs(self.qty):
                # Partial close - keep same avg_price
                pass
            else:
                # Reversing position - new avg_price is the current trade price
                self.avg_price = price
        
        self.qty = new_qty
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized P&L at a given market price.
        
        Args:
            current_price: Current market price
            
        Returns:
            Unrealized P&L (positive for profit, negative for loss)
        """
        if self.qty == 0:
            return 0.0
        return self.qty * (current_price - self.avg_price)
    
    def __repr__(self) -> str:
        """Return string representation of position."""
        return f"Position(symbol='{self.symbol}', qty={self.qty}, avg_price={self.avg_price:.2f})"


class Portfolio:
    """
    Manages portfolio state including positions, cash, and P&L.
    
    Attributes:
        cash: Current cash balance
        initial_cash: Initial starting cash
        positions: Dictionary mapping symbols to Position objects
        realized_pnl: Total realized profit/loss from closed trades
    """
    
    def __init__(self, initial_cash: float = 100000.0) -> None:
        """
        Initialize portfolio with starting cash.
        
        Args:
            initial_cash: Starting cash balance (default: 100000.0)
            
        Raises:
            ValueError: If initial_cash is not positive
        """
        if initial_cash <= 0:
            raise ValueError(f"Initial cash must be positive, got {initial_cash}")
        
        self.cash: float = initial_cash
        self.initial_cash: float = initial_cash
        self.positions: Dict[str, Position] = {}
        self.realized_pnl: float = 0.0
    
    def get_position(self, symbol: str) -> Position:
        """
        Get position for a symbol, creating it if it doesn't exist.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position object for the symbol
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]
    
    def update_position(self, symbol: str, qty_delta: float, price: float) -> None:        
        """
        Update position and cash after a trade.
        
        Args:
            symbol: Trading symbol
            qty_delta: Change in quantity (positive for buy, negative for sell)
            price: Trade execution price
            
        Raises:
            ValueError: If insufficient cash for a buy order
        """
        position = self.get_position(symbol)
        
        # Calculate trade value and total cost
        trade_value = abs(qty_delta) * price
       
        
        # For buy orders (qty_delta > 0), check sufficient cash
        if qty_delta > 0:
            if trade_value > self.cash:
                raise ValueError(
                    f"Insufficient cash for trade: need {trade_value:.2f}, have {self.cash:.2f}"
                )
        
        # Calculate realized P&L if closing/reducing a position
        if position.qty != 0 and ((qty_delta < 0 and position.qty > 0) or (qty_delta > 0 and position.qty < 0)):
            # Closing or reducing a position
            qty_closed = min(abs(qty_delta), abs(position.qty))
            realized_pnl_per_unit = (price - position.avg_price) * (1 if position.qty > 0 else -1)
            self.realized_pnl += realized_pnl_per_unit * qty_closed
        
        # Update position
        position.update(qty_delta, price)
        
        # Update cash (buy decreases cash, sell increases cash)
        if qty_delta > 0:
            self.cash -= trade_value
        else:
            self.cash += trade_value
    
    def calculate_unrealized_pnl(self, prices: Dict[str, float]) -> float:
        """
        Calculate total unrealized P&L across all positions.
        
        Args:
            prices: Dictionary mapping symbols to current prices
            
        Returns:
            Total unrealized P&L
        """
        unrealized_pnl = 0.0
        for symbol, position in self.positions.items():
            if position.qty != 0 and symbol in prices:
                unrealized_pnl += position.calculate_unrealized_pnl(prices[symbol])
        return unrealized_pnl
    
    @property
    def equity(self) -> float:
        """
        Get current cash balance.
        
        Note: This property returns only cash without position values.
        Use calculate_total_equity(prices) to get total equity including positions.
        
        Returns:
            Current cash balance
        """
        return self.cash
    
    def calculate_total_equity(self, prices: Dict[str, float]) -> float:
        """
        Calculate total equity including cash and position values.
        
        Args:
            prices: Dictionary mapping symbols to current prices
            
        Returns:
            Total equity (cash + unrealized P&L + initial position values)
        """
        total_equity = self.cash
        for symbol, position in self.positions.items():
            if position.qty != 0 and symbol in prices:
                # Market value of position
                total_equity += position.qty * prices[symbol]
        return total_equity
    
    def __repr__(self) -> str:
        """Return string representation of portfolio."""
        num_positions = len([p for p in self.positions.values() if p.qty != 0])
        return (
            f"Portfolio(cash={self.cash:.2f}, "
            f"realized_pnl={self.realized_pnl:.2f}, "
            f"positions={num_positions})"
        )
