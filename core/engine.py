"""
Trading engine for the trading system.

This module implements the core trading engine that orchestrates
market data feeds, strategies, and execution.
"""

import time
from typing import Optional, List
from logger import TradeEvent
from logger import get_logger
from data.data_feed import MarketDataFeed
from strategy.base import BaseStrategy
from models.signal import TradingSignal


class TradingEngine:
    """
    Core trading engine that orchestrates the trading system.
    
    The engine manages the lifecycle of the trading system, coordinates
    market data feeds with trading strategies, and handles the execution
    of trading signals.
    
    Attributes:
        data_feed: Market data feed provider
        strategies: List of trading strategies to execute
        heartbeat_interval: Time in seconds between heartbeat cycles
        logger: Structured logger instance
        _running: Flag indicating if engine is running
    """
    
    def __init__(
        self,
        data_feed: MarketDataFeed,
        strategies: List[BaseStrategy],
        heartbeat_interval: float = 1.0,
        execution_handler: Optional[object] = None
    ) -> None:
        """
        Initialize the trading engine.
        
        Args:
            data_feed: Market data feed implementation
            strategies: List of trading strategies to run
            heartbeat_interval: Seconds between heartbeat cycles (default: 1.0)
            execution_handler: Optional execution handler for trade execution
                              (not implemented yet, reserved for future use)
        
        Raises:
            ValueError: If strategies list is empty or heartbeat_interval is invalid
        """
        if not strategies:
            raise ValueError("At least one strategy is required")
        
        if heartbeat_interval <= 0:
            raise ValueError("Heartbeat interval must be positive")
        
        self.data_feed: MarketDataFeed = data_feed
        self.strategies: List[BaseStrategy] = strategies
        self.heartbeat_interval: float = heartbeat_interval
        self.execution_handler: Optional[object] = execution_handler
        self.logger = get_logger(__name__)
        self._running: bool = False
        
        self.logger.info(
            "TradingEngine initialized",
            num_strategies=len(strategies),
            heartbeat_interval=heartbeat_interval,
            has_execution_handler=execution_handler is not None
        )
    
    def start(self) -> None:
        """
        Start the trading engine.
        
        This method initializes the engine, connects to the data feed,
        and prepares strategies for execution.
        
        Raises:
            RuntimeError: If engine is already running
            ConnectionError: If data feed connection fails
        """
        if self._running:
            raise RuntimeError("Trading engine is already running")
        
        self.logger.info("Starting trading engine")
        
        try:
            # Connect to data feed
            self.logger.info("Connecting to data feed")
            self.data_feed.connect()
            
            if not self.data_feed.is_connected:
                raise ConnectionError("Failed to connect to data feed")
            
            self.logger.info("Data feed connected successfully")
            
            # Initialize strategies
            for strategy in self.strategies:
                self.logger.info(f"Initializing strategy: {strategy.strategy_id}")
            
            self._running = True
            self.logger.info("Trading engine started successfully")
            
        except Exception as e:
            self.logger.error(
                f"Failed to start trading engine: {str(e)}",
                exc_info=True
            )
            raise
    
    def stop(self) -> None:
        """
        Stop the trading engine.
        
        This method gracefully shuts down the engine, disconnects from
        the data feed, and cleans up resources.
        """
        if not self._running:
            self.logger.warning("Trading engine is not running")
            return
        
        self.logger.info("Stopping trading engine")
        
        try:
            # Disconnect from data feed
            self.logger.info("Disconnecting from data feed")
            self.data_feed.disconnect()
            
            self._running = False
            self.logger.info("Trading engine stopped successfully")
            
        except Exception as e:
            self.logger.error(
                f"Error during engine shutdown: {str(e)}",
                exc_info=True
            )
            self._running = False
            raise
    
    def run_loop(self, max_iterations: Optional[int] = None) -> None:
        """
        Run the main trading loop.
        
        This method executes the heartbeat loop that continuously:
        1. Fetches latest prices for all symbols
        2. Updates strategies with new prices
        3. Processes generated signals
        4. Sleeps for the heartbeat interval
        
        Args:
            max_iterations: Optional maximum number of iterations to run.
                           If None, runs indefinitely until stop() is called.
        
        Raises:
            RuntimeError: If engine is not started
        """
        if not self._running:
            raise RuntimeError("Trading engine must be started before running loop")
        
        self.logger.info(
            "Starting trading loop",
            max_iterations=max_iterations if max_iterations else "infinite"
        )
        
        iteration = 0
        
        try:
            while self._running:
                # Check iteration limit
                if max_iterations is not None and iteration >= max_iterations:
                    self.logger.info(
                        "Reached maximum iterations",
                        iterations=iteration
                    )
                    break
                
                iteration += 1
                
                # Heartbeat log
                self.logger.debug(f"Heartbeat #{iteration}")
                
                # Process each strategy
                for strategy in self.strategies:
                    self._process_strategy(strategy)
                
                # Sleep for heartbeat interval
                time.sleep(self.heartbeat_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, stopping engine")
            self.stop()
        except Exception as e:
            self.logger.error(
                f"Error in trading loop: {str(e)}",
                iteration=iteration,
                exc_info=True
            )
            raise
        finally:
            if self._running:
                self.stop()
    
    def _process_strategy(self, strategy: BaseStrategy) -> None:
        """
        Process a single strategy.
        
        This internal method fetches prices and updates the strategy.
        For now, it processes a hardcoded list of symbols. In the future,
        this will be configurable per strategy.
        
        Args:
            strategy: Strategy to process
        """
        # TODO: Make symbols configurable per strategy
        # For now, using a placeholder approach
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        for symbol in symbols:
            try:
                # Get latest price
                price = self.data_feed.get_latest_price(symbol)
                
                if price is None:
                    self.logger.debug(
                        f"No price available for {symbol}",
                        strategy_id=strategy.strategy_id
                    )
                    continue
                
                # Update strategy with price
                signal = strategy.on_price_update(symbol, price)
                
                # Process signal if generated
                if signal:
                    self._process_signal(signal)
                    
            except Exception as e:
                self.logger.error(
                    f"Error processing {symbol} for strategy {strategy.strategy_id}: {str(e)}",
                    symbol=symbol,
                    strategy_id=strategy.strategy_id,
                    exc_info=True
                )
    
    def _process_signal(self, signal: TradingSignal) -> None:
        """
        Process a trading signal.
        
        This method logs the signal and would normally send it to
        an execution handler. For now, it just logs the signal.
        
        Args:
            signal: Trading signal to process
        """
        self.logger.info(
            f"Signal generated: {signal}",
            symbol=signal.symbol,
            side=signal.side,
            qty=signal.qty,
            strategy_id=signal.strategy_id
        )
        
        # Log to trade journal
        self.logger.trade_event(signal.to_trade_event(event_type="SIGNAL"))
        
        # TODO: Send to execution handler when implemented
        if self.execution_handler:
            self.logger.debug("Execution handler not yet implemented")
    
    @property
    def is_running(self) -> bool:
        """
        Check if engine is currently running.
        
        Returns:
            True if engine is running, False otherwise
        """
        return self._running
    
    def __repr__(self) -> str:
        """Return string representation of engine."""
        return (
            f"TradingEngine(strategies={len(self.strategies)}, "
            f"heartbeat_interval={self.heartbeat_interval}, "
            f"running={self._running})"
        )
