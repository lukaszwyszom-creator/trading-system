# Trading System

A production-ready trading system with clean architecture, structured logging, and extensible design.

## Overview

This trading system provides a modular framework for algorithmic trading with:
- **Core Trading Engine**: Orchestrates market data feeds, strategies, and execution
- **Paper Trading Execution**: Realistic simulation with slippage, commission, and P&L tracking
- **Portfolio Management**: Position tracking with realized and unrealized P&L
- **Market Data Interface**: Abstract interface for connecting to various data sources
- **Strategy Framework**: Base classes for implementing trading strategies
- **Structured Logging**: JSON logging with trade journaling for audit trails
- **Type Safety**: Full type annotations for production code

## Project Structure

```
trading-system/
├── core/                       # Core trading engine
│   ├── __init__.py
│   └── engine.py              # TradingEngine class
├── data/                       # Market data interfaces
│   ├── __init__.py
│   ├── data_feed.py           # Abstract MarketDataFeed base class
│   └── mock_feed.py           # Mock data feed for testing
├── strategy/                   # Trading strategies
│   ├── __init__.py
│   ├── base.py                # BaseStrategy abstract class
│   └── test_strategy.py      # Example test strategy
├── execution/                  # Trade execution handlers
│   ├── __init__.py
│   └── paper.py               # PaperExecutionHandler for paper trading
├── portfolio/                  # Portfolio and position management
│   ├── __init__.py
│   └── positions.py           # Position and Portfolio classes
├── models/                     # Data models
│   ├── __init__.py
│   ├── signal.py              # TradingSignal dataclass
│   └── fill.py                # FillEvent dataclass
├── config.py                   # Configuration management
├── logger.py                   # Structured logging module
├── example_engine.py           # Example usage
├── test_engine.py              # Core engine test suite
├── test_paper_execution.py     # Paper execution test suite
├── main.py                     # Legacy RSI CLI script
├── main_with_logging.py        # Legacy example with logging
├── test_logger.py              # Logger test script
└── requirements.txt            # Dependencies
```

## Configuration

The project uses environment variables for configuration. To set up:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual values:
   ```
   API_KEY=your_actual_api_key
   API_SECRET=your_actual_api_secret
   BASE_URL=https://your-trading-api.com
   
   # Optional logging configuration
   LOG_LEVEL=INFO
   LOG_DIRECTORY=./logs
   CONSOLE_LOGGING=true
   JSON_LOGGING=true
   ```

3. The configuration module will automatically load these values when imported:
   ```python
   from config import get_settings
   
   settings = get_settings()
   print(settings.base_url)  # Access configuration values
   ```

The configuration module validates that all required environment variables are set and provides clear error messages if any are missing.

## Architecture

### Core Trading Engine (`core/engine.py`)

The `TradingEngine` class orchestrates the entire trading system:

- **Dependency Injection**: Accepts data feed, strategies, and optional execution handler
- **Heartbeat Loop**: Configurable interval for processing market data and strategies
- **Lifecycle Management**: `start()`, `stop()`, and `run_loop()` methods
- **Structured Logging**: Full integration with the logging system

Example usage:

```python
from core.engine import TradingEngine
from data.mock_feed import MockDataFeed
from strategy.test_strategy import SimpleTestStrategy

# Create components
data_feed = MockDataFeed()
strategies = [SimpleTestStrategy("strategy_1")]

# Create and start engine
engine = TradingEngine(
    data_feed=data_feed,
    strategies=strategies,
    heartbeat_interval=1.0
)
engine.start()
engine.run_loop(max_iterations=10)
```

### Market Data Interface (`data/data_feed.py`)

Abstract base class `MarketDataFeed` defines the contract for market data providers:

- `connect()`: Establish connection to data source
- `disconnect()`: Close connection and cleanup
- `get_latest_price(symbol)`: Retrieve latest price for a symbol
- `is_connected`: Property to check connection status

The interface is async-friendly but sync compatible. Implementations can be:
- Real-time websocket feeds
- REST API polling
- Historical data providers
- Mock feeds for testing (see `data/mock_feed.py`)

### Strategy Framework (`strategy/base.py`)

Base class `BaseStrategy` defines the interface for trading strategies:

```python
class MyStrategy(BaseStrategy):
    def __init__(self, strategy_id: str):
        super().__init__(strategy_id)
        # Initialize indicators, state, etc.
    
    def on_price_update(self, symbol: str, price: float) -> Optional[TradingSignal]:
        # Analyze price and generate signal
        if self.should_buy(symbol, price):
            return TradingSignal(
                symbol=symbol,
                side="BUY",
                qty=100,
                strategy_id=self.strategy_id,
                timestamp=datetime.utcnow(),
                price=price
            )
        return None
```

### Trading Signals (`models/signal.py`)

The `TradingSignal` dataclass represents trading decisions:

```python
@dataclass
class TradingSignal:
    symbol: str              # Trading symbol
    side: str                # "BUY", "SELL", or "HOLD"
    qty: Optional[float]     # Quantity (None for HOLD)
    strategy_id: str         # Strategy identifier
    timestamp: datetime      # Signal generation time
    price: Optional[float]   # Price at signal generation
    metadata: Optional[dict] # Additional strategy data
```

Signals are validated on creation and automatically logged to the trade journal.

### Paper Trading Execution (`execution/paper.py`)

The `PaperExecutionHandler` provides a realistic paper trading simulation with:

- **Trade Execution**: Executes BUY/SELL signals from strategies
- **Slippage Simulation**: Configurable random slippage in basis points
- **Commission**: Configurable commission rate as a percentage of trade value
- **Position Tracking**: Automatically updates positions with average price calculation
- **P&L Tracking**: Tracks both realized and unrealized profit/loss
- **Trade Journaling**: Logs ORDER and FILL events to trade journal

Example usage:

```python
from core.engine import TradingEngine
from execution.paper import PaperExecutionHandler
from data.mock_feed import MockDataFeed
from strategy.test_strategy import SimpleTestStrategy

# Create paper execution handler
execution_handler = PaperExecutionHandler(
    initial_cash=100000.0,      # Starting cash
    commission_rate=0.001,       # 0.1% commission
    slippage_bps=5.0,           # 5 bps max slippage
    random_seed=42              # For deterministic testing
)

# Create and start engine with execution
engine = TradingEngine(
    data_feed=MockDataFeed(),
    strategies=[SimpleTestStrategy("strategy_1")],
    execution_handler=execution_handler
)
engine.start()
engine.run_loop(max_iterations=100)

# Check portfolio state
summary = execution_handler.get_portfolio_summary()
print(f"Cash: {summary['cash']:.2f}")
print(f"Realized P&L: {summary['realized_pnl']:.2f}")
print(f"Positions: {summary['num_positions']}")
```

### Portfolio Management (`portfolio/positions.py`)

The portfolio module provides position and P&L tracking:

**Position Class**: Tracks individual symbol positions
- Quantity and average entry price
- Smart average price calculation when adding/reducing positions
- Unrealized P&L calculation at current market prices

**Portfolio Class**: Manages overall portfolio state
- Cash balance tracking
- Multiple symbol positions
- Realized P&L from closed trades
- Total equity calculation with current prices
- Validates sufficient cash before trades

### Fill Events (`models/fill.py`)

The `FillEvent` dataclass represents executed trades:

```python
@dataclass
class FillEvent:
    timestamp: datetime      # Execution timestamp
    symbol: str             # Trading symbol
    side: str               # "BUY" or "SELL"
    qty: float              # Quantity filled
    price: float            # Execution price
    strategy_id: str        # Originating strategy
    fee: float              # Commission/fee paid
    slippage: float         # Slippage amount


## Running the System

### Example Script

Run the example to see the engine in action:

```bash
python example_engine.py
```

This demonstrates:
- Creating a mock data feed
- Configuring multiple strategies
- Starting and running the engine
- Automatic signal generation and logging

### Testing

Run the comprehensive test suites:

```bash
# Core engine tests
python test_engine.py

# Paper execution tests
python test_paper_execution.py
```

**Core Engine Tests** cover:
- TradingSignal validation
- MarketDataFeed interface
- BaseStrategy implementation
- TradingEngine lifecycle
- Error handling

**Paper Execution Tests** cover:
- FillEvent creation and validation
- Position tracking and average price calculation
- Portfolio management and P&L tracking
- PaperExecutionHandler with slippage and commission
- Buy/sell lifecycle with realized P&L
- End-to-end engine integration with execution

### Legacy RSI Example

The original RSI signal script is still available:

```bash
python main_with_logging.py AAPL
```

## Logging System

The project includes a production-ready structured logging system with the following features:

### Features

- **Structured JSON Logging**: All logs are written in JSON format for easy parsing and analysis
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Rotating File Handlers**: Daily log rotation with 30-day retention
- **Colored Console Output**: Color-coded console output for development
- **Trade Event Journal**: Separate log file for trade signals, orders, fills, and errors
- **Configurable**: All settings configurable via environment variables

### Usage

```python
from logger import get_logger, TradeEvent

# Get a logger for your module
logger = get_logger(__name__)

# Log standard messages
logger.info("Application started", component="main")
logger.warning("Rate limit approaching", remaining=10)
logger.error("API request failed", status_code=500)

# Log trade events to the trade journal
event = TradeEvent(
    symbol="AAPL",
    side="BUY",
    qty=100,
    price=150.25,
    strategy_id="RSI_STRATEGY",
    event_type="SIGNAL",
    message="RSI below 30"
)
logger.trade_event(event)
```

### Log Files

The logging system creates two main log files in the configured log directory (default: `./logs`):

1. **trading_system.log**: Application logs in structured JSON format
   ```json
   {"timestamp": "2026-02-14T22:27:03.161766Z", "level": "INFO", "logger": "__main__", "message": "Trading system started"}
   ```

2. **trade_journal.log**: Trade events journal with detailed trade information
   ```json
   {"timestamp": "2026-02-14T22:27:03.161766Z", "event_type": "SIGNAL", "symbol": "AAPL", "side": "BUY", "qty": 100, "price": 150.25, "strategy_id": "RSI_STRATEGY", "message": "RSI below 30"}
   ```

### Trade Event Types

- **SIGNAL**: Trading signal generated by strategy
- **ORDER**: Order submitted to exchange
- **FILL**: Order filled/executed
- **ERROR**: Trade-related error occurred

### Testing the Logger

Run the test suite to verify the logging system:

```bash
python test_logger.py
```

This will create log files in the `./logs` directory and verify all logging functionality.
