"""
Tests for the strategies package.

This module tests the base strategy class, registry system, and SMC strategy
implementation using synthetic data and mock objects.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.strategies.base import BaseStrategy, Signal
from src.strategies.registry import StrategyRegistry, StrategyInfo
from src.strategies.smc import SMCStrategy


class MockStrategy(BaseStrategy):
    """Mock strategy for testing the base class."""
    
    def generate_signals(self):
        """Generate a mock signal."""
        return [
            Signal(
                side='long',
                entry=100.0,
                stop_loss=95.0,
                take_profit=115.0,
                confidence=0.8
            )
        ]


class TestSignal:
    """Test the Signal model."""
    
    def test_signal_creation(self):
        """Test creating a signal with all required fields."""
        signal = Signal(
            side='long',
            entry=100.0,
            stop_loss=95.0,
            take_profit=115.0,
            confidence=0.8
        )
        
        assert signal.side == 'long'
        assert signal.entry == 100.0
        assert signal.stop_loss == 95.0
        assert signal.take_profit == 115.0
        assert signal.confidence == 0.8
        assert isinstance(signal.timestamp, datetime)
        assert signal.metadata == {}
    
    def test_signal_validation(self):
        """Test signal validation rules."""
        # Valid signal
        signal = Signal(
            side='short',
            entry=100.0,
            stop_loss=105.0,
            take_profit=85.0,
            confidence=0.7
        )
        assert signal.side == 'short'
        
        # Test confidence bounds
        with pytest.raises(ValueError):
            Signal(
                side='long',
                entry=100.0,
                stop_loss=95.0,
                take_profit=115.0,
                confidence=1.5  # > 1.0
            )
        
        with pytest.raises(ValueError):
            Signal(
                side='long',
                entry=100.0,
                stop_loss=95.0,
                take_profit=115.0,
                confidence=-0.1  # < 0.0
            )


class TestBaseStrategy:
    """Test the base strategy class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.strategy = MockStrategy()
        
        # Mock broker and data
        self.strategy.broker = Mock()
        self.strategy.broker.getcash.return_value = 10000.0
        self.strategy.broker.positions = {}
        self.strategy.broker.trades = []
        
        # Mock data feed
        self.strategy.data = Mock()
        self.strategy.data.close = Mock()
        self.strategy.data.close.__getitem__ = lambda self, idx: 100.0
        self.strategy.data.high = Mock()
        self.strategy.data.high.__getitem__ = lambda self, idx: 105.0
        self.strategy.data.low = Mock()
        self.strategy.data.low.__getitem__ = lambda self, idx: 95.0
        self.strategy.data.open = Mock()
        self.strategy.data.open.__getitem__ = lambda self, idx: 100.0
        self.strategy.data.volume = Mock()
        self.strategy.data.volume.__getitem__ = lambda self, idx: 1000
    
    def test_strategy_initialization(self):
        """Test strategy initialization and parameter validation."""
        assert self.strategy.params.risk_per_trade == 0.02
        assert self.strategy.params.position_size == 0.1
        assert self.strategy.params.min_risk_reward == 3.0
        assert self.strategy.params.max_positions == 5
        
        # Test parameter validation
        with pytest.raises(ValueError):
            self.strategy.params = self.strategy.params._replace(risk_per_trade=0.15)
            self.strategy._validate_parameters()
    
    def test_signal_validation(self):
        """Test signal validation logic."""
        # Valid signal
        valid_signal = Signal(
            side='long',
            entry=100.0,
            stop_loss=95.0,
            take_profit=115.0,
            confidence=0.8
        )
        assert self.strategy._validate_signal(valid_signal) is True
        
        # Invalid signal - low confidence
        low_confidence_signal = Signal(
            side='long',
            entry=100.0,
            stop_loss=95.0,
            take_profit=115.0,
            confidence=0.3
        )
        assert self.strategy._validate_signal(low_confidence_signal) is False
        
        # Invalid signal - poor risk-reward
        poor_rr_signal = Signal(
            side='long',
            entry=100.0,
            stop_loss=95.0,
            take_profit=102.0,  # Only 2:1 risk-reward
            confidence=0.8
        )
        assert self.strategy._validate_signal(poor_rr_signal) is False
    
    def test_position_size_calculation(self):
        """Test position size calculation based on risk."""
        signal = Signal(
            side='long',
            entry=100.0,
            stop_loss=95.0,
            take_profit=115.0,
            confidence=0.8
        )
        
        size = self.strategy._calculate_position_size(signal)
        expected_size = (10000.0 * 0.02) / (100.0 - 95.0)  # risk_amount / risk_per_unit
        assert size == expected_size
    
    def test_strategy_stats(self):
        """Test strategy statistics collection."""
        stats = self.strategy.get_strategy_stats()
        
        assert 'total_signals' in stats
        assert 'current_positions' in stats
        assert 'total_trades' in stats
        assert 'total_pnl' in stats
        assert 'parameters' in stats


class TestStrategyRegistry:
    """Test the strategy registry system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = StrategyRegistry()
        self.registry.strategies = {}  # Clear existing strategies
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        assert isinstance(self.registry.strategies, dict)
        assert self.registry.strategies_dir is not None
    
    def test_manual_strategy_registration(self):
        """Test manually registering a strategy."""
        strategy_info = self.registry.register_strategy(
            'TestStrategy',
            MockStrategy,
            '/path/to/test_strategy.py',
            '1.0.0'
        )
        
        assert isinstance(strategy_info, StrategyInfo)
        assert strategy_info.name == 'TestStrategy'
        assert strategy_info.version == '1.0.0'
        assert 'TestStrategy' in self.registry.strategies
    
    def test_get_strategy(self):
        """Test retrieving a strategy by name."""
        self.registry.register_strategy(
            'TestStrategy',
            MockStrategy,
            '/path/to/test_strategy.py',
            '1.0.0'
        )
        
        strategy_class = self.registry.get_strategy('TestStrategy')
        assert strategy_class == MockStrategy
        
        # Test non-existent strategy
        assert self.registry.get_strategy('NonExistent') is None
    
    def test_list_strategies(self):
        """Test listing all registered strategies."""
        self.registry.register_strategy(
            'Strategy1',
            MockStrategy,
            '/path/to/strategy1.py',
            '1.0.0'
        )
        
        self.registry.register_strategy(
            'Strategy2',
            MockStrategy,
            '/path/to/strategy2.py',
            '2.0.0'
        )
        
        strategies = self.registry.list_strategies()
        assert len(strategies) == 2
        assert any(s['name'] == 'Strategy1' for s in strategies)
        assert any(s['name'] == 'Strategy2' for s in strategies)
    
    def test_strategy_validation(self):
        """Test strategy validation."""
        self.registry.register_strategy(
            'TestStrategy',
            MockStrategy,
            '/path/to/test_strategy.py',
            '1.0.0'
        )
        
        validation = self.registry.validate_strategy('TestStrategy')
        assert validation['valid'] is True
        assert 'errors' in validation
        assert len(validation['errors']) == 0
        
        # Test non-existent strategy
        validation = self.registry.validate_strategy('NonExistent')
        assert validation['valid'] is False
        assert len(validation['errors']) > 0


class TestSMCStrategy:
    """Test the SMC strategy implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create synthetic OHLCV data
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        np.random.seed(42)  # For reproducible tests
        
        data = {
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(100, 200, 100),
            'low': np.random.uniform(100, 200, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000, 10000, 100)
        }
        
        # Ensure high >= low, high >= open, high >= close, low <= open, low <= close
        for i in range(100):
            data['high'][i] = max(data['open'][i], data['close'][i], data['high'][i])
            data['low'][i] = min(data['open'][i], data['close'][i], data['low'][i])
        
        self.df = pd.DataFrame(data, index=dates)
        
        # Create strategy instance
        self.strategy = SMCStrategy()
        
        # Mock broker
        self.strategy.broker = Mock()
        self.strategy.broker.getcash.return_value = 10000.0
        self.strategy.broker.positions = {}
        self.strategy.broker.trades = []
    
    def test_smc_initialization(self):
        """Test SMC strategy initialization."""
        assert self.strategy.version == "1.0.0"
        assert self.strategy.params.lookback_period == 20
        assert self.strategy.params.volume_threshold == 1.5
        assert self.strategy.params.min_risk_reward == 3.0
        assert self.strategy.trend == 'neutral'
        assert len(self.strategy.order_blocks) == 0
        assert len(self.strategy.fair_value_gaps) == 0
    
    def test_market_structure_analysis(self):
        """Test market structure analysis."""
        # Mock data feed with synthetic data
        self.strategy.data.close = Mock()
        self.strategy.data.close.__getitem__ = lambda self, idx: self.df['close'].iloc[idx] if idx < len(self.df) else 0
        
        self.strategy.data.high = Mock()
        self.strategy.data.high.__getitem__ = lambda self, idx: self.df['high'].iloc[idx] if idx < len(self.df) else 0
        
        self.strategy.data.low = Mock()
        self.strategy.data.low.__getitem__ = lambda self, idx: self.df['low'].iloc[idx] if idx < len(self.df) else 0
        
        # Test trend confirmation
        assert self.strategy._is_trend_confirmed('bullish') is False  # Not enough data initially
        
        # Test with more data
        self.strategy.data.close.__len__ = lambda: 10
        self.strategy.data.close.__getitem__ = lambda self, idx: 100 + idx  # Increasing prices
        
        # Mock the data length for trend confirmation
        with patch.object(self.strategy.data, '__len__', return_value=10):
            assert self.strategy._is_trend_confirmed('bullish') is True
    
    def test_order_block_detection(self):
        """Test order block detection."""
        # Mock volume data
        self.strategy.data.volume = Mock()
        self.strategy.data.volume.__getitem__ = lambda self, idx: 5000 if idx == -1 else 2000
        
        self.strategy.data.open = Mock()
        self.strategy.data.open.__getitem__ = lambda self, idx: 100
        
        self.strategy.data.close = Mock()
        self.strategy.data.close.__getitem__ = lambda self, idx: 105 if idx == -1 else 100
        
        self.strategy.data.high = Mock()
        self.strategy.data.high.__getitem__ = lambda self, idx: 110
        
        self.strategy.data.low = Mock()
        self.strategy.data.low.__getitem__ = lambda self, idx: 95 if idx == -1 else 100
        
        # Mock volume ratio
        self.strategy.volume_ratio = Mock()
        self.strategy.volume_ratio.__getitem__ = lambda self, idx: 2.0 if idx == -1 else 1.0
        
        # Test order block detection
        self.strategy._detect_order_blocks()
        
        # Should detect bullish order block
        assert len(self.strategy.order_blocks) > 0
        if self.strategy.order_blocks:
            assert self.strategy.order_blocks[0]['type'] == 'bullish'
    
    def test_signal_generation(self):
        """Test signal generation."""
        # Mock data for signal generation
        self.strategy.data.close = Mock()
        self.strategy.data.close.__getitem__ = lambda self, idx: 100.0
        
        # Mock indicators
        self.strategy.rsi = Mock()
        self.strategy.rsi.__getitem__ = lambda self, idx: 50.0
        
        self.strategy.volume_ratio = Mock()
        self.strategy.volume_ratio.__getitem__ = lambda self, idx: 1.5
        
        # Set up bullish conditions
        self.strategy.trend = 'bullish'
        self.strategy.order_blocks = [{'type': 'bullish', 'high': 110, 'low': 90, 'volume': 5000, 'bar_index': -1}]
        self.strategy.fair_value_gaps = [{'type': 'bullish', 'high': 105, 'low': 95, 'gap_size': 0.02, 'bar_index': -1}]
        self.strategy.liquidity_zones = [{'type': 'support', 'price': 95, 'strength': 3000, 'bar_index': -1}]
        
        # Test bullish signal generation
        signal = self.strategy._generate_bullish_signal()
        assert signal is not None
        assert signal.side == 'long'
        assert signal.entry == 100.0
        assert signal.stop_loss < signal.entry
        assert signal.take_profit > signal.entry
        assert signal.confidence >= 0.5
    
    def test_confidence_calculation(self):
        """Test signal confidence calculation."""
        # Mock data
        self.strategy.volume_ratio = Mock()
        self.strategy.volume_ratio.__getitem__ = lambda self, idx: 2.0
        
        self.strategy.rsi = Mock()
        self.strategy.rsi.__getitem__ = lambda self, idx: 50.0
        
        # Set up bullish conditions
        self.strategy.trend = 'bullish'
        self.strategy.order_blocks = [{'type': 'bullish'}]
        self.strategy.fair_value_gaps = [{'type': 'bullish'}]
        
        confidence = self.strategy._calculate_signal_confidence('bullish')
        assert confidence > 0.5
        assert confidence <= 1.0
        
        # Test bearish confidence
        self.strategy.trend = 'bearish'
        self.strategy.order_blocks = [{'type': 'bearish'}]
        self.strategy.fair_value_gaps = [{'type': 'bearish'}]
        
        confidence = self.strategy._calculate_signal_confidence('bearish')
        assert confidence > 0.5
        assert confidence <= 1.0


class TestStrategyIntegration:
    """Test integration between strategy components."""
    
    def test_strategy_registry_integration(self):
        """Test that strategies are properly registered and discoverable."""
        registry = StrategyRegistry()
        
        # The SMC strategy should be auto-discovered
        smc_strategy = registry.get_strategy('SMC')
        assert smc_strategy is not None
        assert smc_strategy == SMCStrategy
        
        # Test strategy info
        smc_info = registry.get_strategy_info('SMC')
        assert smc_info is not None
        assert smc_info.name == 'SMC'
        assert smc_info.version == '1.0.0'
    
    def test_strategy_validation_integration(self):
        """Test that all registered strategies pass validation."""
        registry = StrategyRegistry()
        
        for strategy_name in registry.strategies:
            validation = registry.validate_strategy(strategy_name)
            assert validation['valid'] is True, f"Strategy {strategy_name} failed validation: {validation['errors']}"
    
    def test_strategy_parameters_integration(self):
        """Test that strategy parameters are properly extracted."""
        registry = StrategyRegistry()
        
        for strategy_name in registry.strategies:
            params = registry.get_strategy_parameters(strategy_name)
            assert isinstance(params, dict)
            assert len(params) > 0  # Should have some parameters


if __name__ == '__main__':
    pytest.main([__file__])
