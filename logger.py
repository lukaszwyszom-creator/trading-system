"""
Structured logging module for the trading system.

This module provides structured JSON logging with rotating file handlers,
colored console output, and specialized trade event journaling.
"""

import json
import logging
import sys
from datetime import datetime
from enum import Enum
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from config import get_settings
except ImportError:
    # Allow module to work even if config is not available
    get_settings = None  # type: ignore


class LogLevel(str, Enum):
    """Log levels for the trading system."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color to console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Get the raw level name without color codes
        level_name = record.levelname
        # Remove ANSI color codes if present
        import re
        level_name = re.sub(r'\x1b\[[0-9;]*m', '', level_name)
        
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level_name,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'taskName', 'asctime']:
                log_data[key] = value
        
        return json.dumps(log_data)


class TradeEvent:
    """
    Structured trade event data.
    
    Attributes:
        timestamp: Event timestamp in ISO format
        symbol: Trading symbol (e.g., 'AAPL')
        side: Order side ('BUY', 'SELL', 'HOLD')
        qty: Quantity
        price: Price per unit
        strategy_id: Strategy identifier
        event_type: Type of event ('SIGNAL', 'ORDER', 'FILL', 'ERROR')
        message: Optional additional message
    """
    
    def __init__(
        self,
        symbol: str,
        side: str,
        qty: Optional[float] = None,
        price: Optional[float] = None,
        strategy_id: Optional[str] = None,
        event_type: str = "SIGNAL",
        message: Optional[str] = None
    ) -> None:
        """Initialize trade event."""
        self.timestamp: str = datetime.utcnow().isoformat() + 'Z'
        self.symbol: str = symbol
        self.side: str = side
        self.qty: Optional[float] = qty
        self.price: Optional[float] = price
        self.strategy_id: Optional[str] = strategy_id
        self.event_type: str = event_type
        self.message: Optional[str] = message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade event to dictionary."""
        data = {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'symbol': self.symbol,
            'side': self.side,
        }
        if self.qty is not None:
            data['qty'] = self.qty
        if self.price is not None:
            data['price'] = self.price
        if self.strategy_id is not None:
            data['strategy_id'] = self.strategy_id
        if self.message is not None:
            data['message'] = self.message
        return data
    
    def to_json(self) -> str:
        """Convert trade event to JSON string."""
        return json.dumps(self.to_dict())


class TradingLogger:
    """
    Logger wrapper with trade journaling support.
    
    Attributes:
        logger: Standard Python logger instance
        trade_logger: Logger for trade events
    """
    
    def __init__(self, name: str) -> None:
        """Initialize trading logger."""
        self.logger: logging.Logger = logging.getLogger(name)
        self.trade_logger: logging.Logger = logging.getLogger(f"{name}.trade")
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def trade_event(self, event: TradeEvent) -> None:
        """
        Log a trade event to the trade journal.
        
        Args:
            event: TradeEvent instance to log
        """
        self.trade_logger.info(event.to_json())


# Configuration state
_configured: bool = False
_loggers: Dict[str, TradingLogger] = {}


def _get_log_config() -> Dict[str, Any]:
    """
    Get logging configuration from settings or defaults.
    
    Returns:
        Dictionary with log configuration
    """
    config: Dict[str, Any] = {
        'log_level': 'INFO',
        'log_directory': './logs',
        'console_logging': True,
        'json_logging': True,
    }
    
    # Try to get settings from config module if available
    if get_settings is not None:
        try:
            settings = get_settings()
            # Check if settings has logging attributes
            if hasattr(settings, 'log_level'):
                config['log_level'] = settings.log_level
            if hasattr(settings, 'log_directory'):
                config['log_directory'] = settings.log_directory
            if hasattr(settings, 'console_logging'):
                config['console_logging'] = settings.console_logging
            if hasattr(settings, 'json_logging'):
                config['json_logging'] = settings.json_logging
        except Exception:
            # If settings fail to load, use defaults
            pass
    
    return config


def _configure_logging() -> None:
    """Configure the logging system with handlers and formatters."""
    global _configured
    
    if _configured:
        return
    
    config = _get_log_config()
    
    # Create log directory
    log_dir = Path(config['log_directory'])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get log level
    log_level = getattr(logging, config['log_level'].upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add console handler if enabled
    if config['console_logging']:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Use colored formatter for console
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        console_handler.setFormatter(ColoredFormatter(console_format))
        root_logger.addHandler(console_handler)
    
    # Add rotating file handler for application logs
    app_log_file = log_dir / 'trading_system.log'
    file_handler = TimedRotatingFileHandler(
        filename=str(app_log_file),
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # Use JSON formatter for file logs if enabled
    if config['json_logging']:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        file_handler.setFormatter(logging.Formatter(file_format))
    
    root_logger.addHandler(file_handler)
    
    # Configure trade journal logger - independent of root logger
    # We need to configure all loggers ending with '.trade'
    _configure_trade_logger(log_dir)
    
    _configured = True


def _configure_trade_logger(log_dir: Path) -> None:
    """Configure the trade journal logger."""
    # Create a filter that only allows trade loggers
    class TradeLoggerFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.name.endswith('.trade')
    
    # Add trade journal file handler to root logger with filter
    trade_log_file = log_dir / 'trade_journal.log'
    trade_handler = TimedRotatingFileHandler(
        filename=str(trade_log_file),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    trade_handler.setLevel(logging.INFO)
    trade_handler.setFormatter(logging.Formatter('%(message)s'))  # Just the JSON
    trade_handler.addFilter(TradeLoggerFilter())
    
    # Add to root logger so trade events get logged to trade journal
    root_logger = logging.getLogger()
    root_logger.addHandler(trade_handler)


def get_logger(name: str) -> TradingLogger:
    """
    Get a logger instance for the specified name.
    
    This function configures logging on first call and returns a cached
    logger instance for subsequent calls with the same name.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        TradingLogger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
        >>> 
        >>> # Log a trade event
        >>> event = TradeEvent(
        ...     symbol="AAPL",
        ...     side="BUY",
        ...     qty=100,
        ...     price=150.25,
        ...     strategy_id="RSI_STRATEGY"
        ... )
        >>> logger.trade_event(event)
    """
    # Configure logging if not already done
    _configure_logging()
    
    # Return cached logger if available
    if name in _loggers:
        return _loggers[name]
    
    # Create and cache new logger
    logger = TradingLogger(name)
    _loggers[name] = logger
    
    return logger


def reset_logging() -> None:
    """
    Reset the logging configuration.
    
    This function is primarily useful for testing purposes to allow
    reconfiguring the logging system.
    """
    global _configured, _loggers
    
    _configured = False
    _loggers.clear()
    
    # Clear all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
