"""
Structured JSON logging configuration for the trading bot.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor


def add_correlation_id(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add correlation ID to log entries."""
    # Get correlation ID from context if available
    correlation_id = getattr(logger, 'correlation_id', None)
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO timestamp to log entries."""
    event_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service information to log entries."""
    event_dict['service'] = 'smart-trading-bot'
    event_dict['version'] = '1.0.0'
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    json_format: bool = True,
    debug_mode: bool = False
) -> None:
    """
    Setup structured logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format for logs
        debug_mode: Enable debug mode with more verbose logging
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level
    )
    
    # Configure structlog
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_service_info,
        add_correlation_id,
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=debug_mode)
        ])
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class CorrelationContext:
    """Context manager for correlation IDs in logging."""
    
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self._previous_correlation_id: Optional[str] = None
    
    def __enter__(self):
        # Store previous correlation ID
        logger = structlog.get_logger()
        self._previous_correlation_id = getattr(logger, 'correlation_id', None)
        
        # Set new correlation ID
        logger.correlation_id = self.correlation_id
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous correlation ID
        logger = structlog.get_logger()
        if self._previous_correlation_id is not None:
            logger.correlation_id = self._previous_correlation_id
        else:
            delattr(logger, 'correlation_id')


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Log function call with parameters (excluding sensitive data).
    
    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters (sensitive data will be filtered)
    """
    logger = get_logger(__name__)
    
    # Filter out sensitive parameters
    sensitive_keys = {'api_key', 'api_secret', 'password', 'token', 'secret'}
    filtered_kwargs = {
        k: '***REDACTED***' if k.lower() in sensitive_keys else v
        for k, v in kwargs.items()
    }
    
    logger.info(
        "Function call",
        function=func_name,
        parameters=filtered_kwargs
    )


def log_trading_signal(
    symbol: str,
    side: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    confidence: float,
    strategy: str,
    **kwargs
) -> None:
    """
    Log trading signal with structured data.
    
    Args:
        symbol: Trading symbol
        side: Buy or Sell
        entry_price: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price
        confidence: Signal confidence (0-1)
        strategy: Strategy name
        **kwargs: Additional signal parameters
    """
    logger = get_logger(__name__)
    
    # Calculate risk-reward ratio
    if side.upper() == "BUY":
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
    
    risk_reward_ratio = reward / risk if risk > 0 else 0
    
    logger.info(
        "Trading signal generated",
        symbol=symbol,
        side=side.upper(),
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        confidence=confidence,
        strategy=strategy,
        risk_reward_ratio=round(risk_reward_ratio, 2),
        **kwargs
    )


def log_order_execution(
    order_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    order_type: str,
    status: str,
    **kwargs
) -> None:
    """
    Log order execution details.
    
    Args:
        order_id: Order identifier
        symbol: Trading symbol
        side: Buy or Sell
        quantity: Order quantity
        price: Execution price
        order_type: Market, Limit, etc.
        status: Order status
        **kwargs: Additional order parameters
    """
    logger = get_logger(__name__)
    
    logger.info(
        "Order executed",
        order_id=order_id,
        symbol=symbol,
        side=side.upper(),
        quantity=quantity,
        price=price,
        order_type=order_type,
        status=status,
        **kwargs
    )


def log_backtest_result(
    backtest_id: str,
    strategy: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    total_return: float,
    win_rate: float,
    total_trades: int,
    **kwargs
) -> None:
    """
    Log backtest results.
    
    Args:
        backtest_id: Backtest identifier
        strategy: Strategy name
        symbol: Trading symbol
        timeframe: Timeframe used
        start_date: Start date
        end_date: End date
        total_return: Total return percentage
        win_rate: Win rate percentage
        total_trades: Total number of trades
        **kwargs: Additional backtest metrics
    """
    logger = get_logger(__name__)
    
    logger.info(
        "Backtest completed",
        backtest_id=backtest_id,
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        total_return=round(total_return, 2),
        win_rate=round(win_rate, 2),
        total_trades=total_trades,
        **kwargs
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log error with structured context.
    
    Args:
        error: Exception that occurred
        context: Additional context information
        **kwargs: Additional error parameters
    """
    logger = get_logger(__name__)
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_traceback": getattr(error, '__traceback__', None),
    }
    
    if context:
        error_data.update(context)
    
    error_data.update(kwargs)
    
    logger.error(
        "Error occurred",
        **error_data
    )
