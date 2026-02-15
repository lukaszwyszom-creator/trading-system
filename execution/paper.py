"""
Paper trading execution handler.

This module provides the PaperExecutionHandler class for simulating
trade execution in a paper trading environment with slippage and commission.
"""

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from logger import TradeEvent, get_logger
from models.fill import FillEvent
from models.signal import TradingSignal
from portfolio.positions import Portfolio


class PaperExecutionHandler:
    """
    Paper trading execution handler with position and P&L tracking.

    This class simulates trade execution with configurable slippage and commission.
    It maintains a portfolio to track positions, cash, and profit/loss.

    Attributes:
        portfolio: Portfolio instance tracking positions and cash
        commission_rate: Commission rate as a fraction of trade value (e.g., 0.001 = 0.1%)
        slippage_bps: Slippage in basis points (e.g., 5 = 0.05%)
        logger: Structured logger instance
        _rng: Random number generator (for deterministic testing when seeded)
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_bps: float = 5.0,
        random_seed: Optional[int] = None,
    ) -> None:
        """
        Initialize the paper execution handler.

        Args:
            initial_cash: Starting cash balance (default: 100000.0)
            commission_rate: Commission as fraction of trade value (default: 0.001 = 0.1%)
            slippage_bps: Slippage in basis points (default: 5.0 = 0.05%)
            random_seed: Optional seed for random number generator (for deterministic tests)

        Raises:
            ValueError: If parameters are invalid
        """
        if initial_cash <= 0:
            raise ValueError(f"Initial cash must be positive, got {initial_cash}")

        if commission_rate < 0:
            raise ValueError(f"Commission rate cannot be negative, got {commission_rate}")

        if slippage_bps < 0:
            raise ValueError(f"Slippage cannot be negative, got {slippage_bps}")

        self.portfolio = Portfolio(initial_cash=initial_cash)
        self.commission_rate = commission_rate
        self.slippage_bps = slippage_bps
        self.logger = get_logger(__name__)

        # Initialize random number generator for deterministic slippage
        self._rng = random.Random(random_seed) if random_seed is not None else random.Random()

        self.logger.info(
            "PaperExecutionHandler initialized",
            initial_cash=initial_cash,
            commission_rate=commission_rate,
            slippage_bps=slippage_bps,
        )

    def execute(self, signal: TradingSignal, price: Optional[float] = None) -> FillEvent:
        """
        Execute a trading signal and return a fill event.

        This method simulates trade execution by:
        1. Using the provided price or signal price
        2. Applying slippage
        3. Calculating commission
        4. Updating the portfolio
        5. Creating and returning a FillEvent

        Args:
            signal: Trading signal to execute
            price: Optional execution price (uses signal.price if not provided)

        Returns:
            FillEvent representing the executed trade

        Raises:
            ValueError: If signal is invalid (HOLD, missing price, etc.)
        """
        # Validate signal
        if signal.side == "HOLD":
            raise ValueError("Cannot execute HOLD signal")

        if signal.side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid signal side: {signal.side}")

        if signal.qty is None or signal.qty <= 0:
            raise ValueError(f"Invalid quantity: {signal.qty}")

        # Determine execution price
        exec_price = price if price is not None else signal.price
        if exec_price is None:
            raise ValueError("Execution price must be provided either in signal or as parameter")

        if exec_price <= 0:
            raise ValueError(f"Execution price must be positive, got {exec_price}")

        # Apply slippage (simulate market impact)
        # For BUY orders: positive slippage increases price (worse for buyer)
        # For SELL orders: negative slippage decreases price (worse for seller)
        slippage_factor = self._calculate_slippage(signal.side)
        slipped_price = exec_price * (1 + slippage_factor)
        slippage_amount = abs(slipped_price - exec_price)

        # Calculate commission
        trade_value = signal.qty * slipped_price
        commission = trade_value * self.commission_rate

        # Log ORDER event to trade journal
        self.logger.trade_event(
            TradeEvent(
                symbol=signal.symbol,
                side=signal.side,
                qty=signal.qty,
                price=slipped_price,
                strategy_id=signal.strategy_id,
                event_type="ORDER",
                message=f"Order placed: {signal.side} {signal.qty} @ {slipped_price:.2f}",
            )
        )

        # Determine quantity delta (positive for buy, negative for sell)
        qty_delta = signal.qty if signal.side == "BUY" else -signal.qty

        # Update portfolio
        try:
            self.portfolio.update_position(signal.symbol, qty_delta, slipped_price)

            # Book commission as a separate cost (does not affect avg_price)
            self.portfolio.cash -= commission
            self.portfolio.realized_pnl -= commission

        except ValueError as e:
            # Log error if portfolio update fails (e.g., insufficient cash)
            self.logger.error(
                f"Failed to execute trade: {str(e)}",
                symbol=signal.symbol,
                side=signal.side,
                qty=signal.qty,
                price=slipped_price,
                fee=commission,
                exc_info=True,
            )
            raise

        # Create fill event
        fill_event = FillEvent(
            timestamp=datetime.now(timezone.utc),
            symbol=signal.symbol,
            side=signal.side,
            qty=signal.qty,
            price=slipped_price,
            strategy_id=signal.strategy_id,
            fee=commission,
            slippage=slippage_amount,
        )

        # Log FILL event to trade journal
        self.logger.trade_event(fill_event.to_trade_event(event_type="FILL"))

        self.logger.info(
            f"Trade executed: {fill_event}",
            symbol=signal.symbol,
            side=signal.side,
            qty=signal.qty,
            price=slipped_price,
            fee=commission,
            slippage=slippage_amount,
            portfolio_cash=self.portfolio.cash,
            realized_pnl=self.portfolio.realized_pnl,
        )

        return fill_event

    def _calculate_slippage(self, side: str) -> float:
        """
        Calculate random slippage for a trade.

        Slippage is modeled as a uniform random value between 0 and slippage_bps.
        For BUY orders, slippage is positive (worse price).
        For SELL orders, slippage is negative (worse price).

        Args:
            side: Order side ('BUY' or 'SELL')

        Returns:
            Slippage as a fraction (e.g., 0.0005 = 0.05%)
        """
        slippage = self._rng.uniform(0, self.slippage_bps / 10000.0)
        return slippage if side == "BUY" else -slippage

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get current portfolio summary.

        Returns:
            Dictionary with portfolio state including cash, positions, and P&L
        """
        positions_summary: List[Dict[str, Any]] = []
        for symbol, position in self.portfolio.positions.items():
            if position.qty != 0:
                positions_summary.append(
                    {
                        "symbol": symbol,
                        "qty": position.qty,
                        "avg_price": position.avg_price,
                        "market_value": position.market_value,
                    }
                )

        return {
            "cash": self.portfolio.cash,
            "initial_cash": self.portfolio.initial_cash,
            "realized_pnl": self.portfolio.realized_pnl,
            "positions": positions_summary,
            "num_positions": len(positions_summary),
        }

    def __repr__(self) -> str:
        """Return string representation of execution handler."""
        return (
            f"PaperExecutionHandler(cash={self.portfolio.cash:.2f}, "
            f"commission={self.commission_rate:.4f}, "
            f"slippage={self.slippage_bps:.2f}bps)"
        )