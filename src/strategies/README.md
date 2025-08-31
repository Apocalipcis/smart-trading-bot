# Trading Strategies Package

A comprehensive, plugin-based trading strategy system built on Backtrader for the Smart Trading Bot.

## 🚀 Quick Start

### What This Package Does
- **Base Strategy Class**: Abstract foundation for all trading strategies
- **Strategy Registry**: Auto-discovery and management of strategy files
- **Signal System**: Standardized trading signal format with validation
- **SMC Signal Strategy**: Simplified, optimized Smart Money Concepts implementation
- **Plugin Architecture**: Easy to add new strategies

### Run the Demo (5 minutes)
```bash
# From project root
cd examples
python strategy_demo.py
```

You should see:
- Strategy registry discovery
- needtrategy information
- Sample signal generation
- Custom strategy examples

## 📦 Installation & Setup

### Dependencies
```bash
pip install backtrader fastapi pandas numpy
```

### Fix Import Issues
If you see "Import 'backtrader' could not be resolved":

1. **Activate virtual environment**:
   ```bash
   source venv/Scripts/activate  # Windows
   # or
   source venv/bin/activate      # Linux/Mac
   ```

2. **Install backtrader**:
   ```bash
   pip install backtrader
   ```

3. **Check Python path**:
   ```python
   import sys
   sys.path.insert(0, 'src')
   from strategies.base import Signal
   ```

## 🎯 Basic Usage

### Using the SMC Signal Strategy

```python
from strategies.smc_signal import SMCSignalStrategy
from strategies.base import Signal

# Create strategy instance (in Backtrader context)
strategy = SMCSignalStrategy()

# Generate signals
signals = strategy.generate_signals()

# Access strategy parameters
print(f"Risk per trade: {strategy.params.risk_per_trade}")
print(f"Min risk-reward: {strategy.params.min_risk_reward}")
```

### Creating a Simple Signal

```python
from strategies.base import Signal

# Long position signal
long_signal = Signal(
    side='long',
    entry=100.0,
    stop_loss=95.0,
    take_profit=115.0,
    confidence=0.8,
    metadata={'strategy': 'MyStrategy'}
)

# Short position signal
short_signal = Signal(
    side='short',
    entry=100.0,
    stop_loss=105.0,
    take_profit=85.0,
    confidence=0.75
)
```

## 🛠️ Creating Custom Strategies

### Step 1: Inherit from BaseStrategy

```python
from strategies.base import BaseStrategy, Signal
from typing import List

class MyCustomStrategy(BaseStrategy):
    """
    My Awesome Trading Strategy
    
    This strategy implements [your logic here]
    """
    
    # Strategy version
    version = "1.0.0"
    
    # Strategy parameters
    params = (
        ('my_param', 10),           # Custom parameter
        ('risk_per_trade', 0.02),   # Inherited from base
        ('min_risk_reward', 3.0),   # Inherited from base
    )
    
    def __init__(self):
        super().__init__()
        # Initialize your indicators here
        self.my_indicator = None
    
    def generate_signals(self) -> List[Signal]:
        """
        Generate trading signals based on your strategy logic.
        
        Returns:
            List[Signal]: List of valid trading signals
        """
        signals = []
        
        # Your strategy logic here
        if self._should_buy():
            signal = Signal(
                side='long',
                entry=self.data.close[0],
                stop_loss=self.data.close[0] * 0.95,
                take_profit=self.data.close[0] * 1.15,
                confidence=0.8,
                metadata={'strategy': 'MyCustomStrategy'}
            )
            signals.append(signal)
        
        return signals
    
    def _should_buy(self) -> bool:
        """Your buy condition logic"""
        # Example: Buy when price is above moving average
        return self.data.close[0] > self.data.close[-1]
```

### Step 2: Save Your Strategy

Save your strategy in `src/strategies/` with a descriptive name:
- `src/strategies/my_strategy.py`
- `src/strategies/mean_reversion.py`
- `src/strategies/breakout.py`

### Step 3: Auto-Discovery

Your strategy will be automatically discovered and available:

```python
from strategies.registry import get_registry

registry = get_registry()
my_strategy = registry.get_strategy('MyCustomStrategy')
print(f"Strategy loaded: {my_strategy.__name__}")
```

## 🔍 Strategy Registry

### Auto-Discovery
The registry automatically finds all strategy files in the `src/strategies/` directory:

```python
from strategies.registry import get_registry

registry = get_registry()

# List all discovered strategies
strategies = registry.list_strategies()
for strategy in strategies:
    print(f"- {strategy['name']} v{strategy['version']}")

# Get specific strategy
smc = registry.get_strategy('SMCSignalStrategy')
smc_info = registry.get_strategy_info('SMCSignalStrategy')
```

### Manual Registration
```python
from strategies.registry import register_strategy

# Register a strategy manually
register_strategy(
    name='MyStrategy',
    strategy_class=MyCustomStrategy,
    file_path='/path/to/strategy.py',
    version='1.0.0'
)
```

### Validation
```python
# Validate a strategy
validation = registry.validate_strategy('MyStrategy')
if validation['valid']:
    print("Strategy is valid!")
else:
    print("Issues found:", validation['errors'])
```

## 📊 Signal System

### Signal Format
All strategies must return signals in this format:

```python
Signal(
    side='long' | 'short',      # Required: Trade direction
    entry=float,                 # Required: Entry price
    stop_loss=float,             # Required: Stop loss price
    take_profit=float,           # Required: Take profit price
    confidence=float,            # Required: 0.0-1.0 confidence
    timestamp=datetime,          # Optional: Auto-generated
    metadata=dict                # Optional: Strategy-specific data
)
```

### Signal Validation
The base strategy automatically validates signals:

- ✅ **Risk-Reward**: Minimum 3:1 ratio enforced
- ✅ **Confidence**: Must be ≥ 0.5 (50%)
- ✅ **Position Limits**: Respects max_positions setting
- ✅ **Price Logic**: Stop loss and take profit must be valid

### Metadata Examples
```python
# SMC strategy metadata
metadata = {
    'strategy': 'SMCSignalStrategy',
    'trend': 'bullish',
    'rsi': 45.0,
    'volume_ratio': 1.8,
    'order_blocks': 3,
    'fair_value_gaps': 2
}

# Custom strategy metadata
metadata = {
    'strategy': 'MyStrategy',
    'indicator_value': 0.75,
    'market_condition': 'trending',
    'signal_strength': 'strong'
}
```

## 🔧 Integration with Backtesting

### Basic Backtest Setup
```python
import backtrader as bt
from strategies.smc_signal import SMCSignalStrategy

# Create Cerebro engine
cerebro = bt.Cerebro()

# Add data feed
data = bt.feeds.YourDataFeed(...)
cerebro.adddata(data)

# Add strategy
cerebro.addstrategy(SMCSignalStrategy)

# Set initial cash
cerebro.broker.setcash(10000.0)

# Run backtest
results = cerebro.run()
```

### Strategy Parameters
```python
# Customize strategy parameters
cerebro.addstrategy(
    SMCSignalStrategy,
    risk_per_trade=0.03,        # 3% risk per trade
    min_risk_reward=2.5,        # 2.5:1 minimum
    lookback_period=30,         # 30 bars lookback
    volume_threshold=2.0        # 2x average volume
)
```

## 📚 Examples & Code Snippets

### Complete Strategy Example
```python
from strategies.base import BaseStrategy, Signal
from typing import List
import backtrader as bt

class SimpleMovingAverageStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy
    
    Buys when fast MA crosses above slow MA
    Sells when fast MA crosses below slow MA
    """
    
    version = "1.0.0"
    
    params = (
        ('fast_period', 10),
        ('slow_period', 20),
        ('risk_per_trade', 0.02),
        ('min_risk_reward', 2.0),
    )
    
    def __init__(self):
        super().__init__()
        
        # Create indicators
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_period
        )
        
        # Track previous values for crossover detection
        self.prev_fast = None
        self.prev_slow = None
    
    def generate_signals(self) -> List[Signal]:
        """Generate signals based on MA crossover"""
        signals = []
        
        if len(self.data) < 2:  # Need at least 2 bars
            return signals
        
        # Check for crossover
        current_fast = self.fast_ma[0]
        current_slow = self.slow_ma[0]
        
        if self.prev_fast is not None and self.prev_slow is not None:
            # Bullish crossover: fast MA crosses above slow MA
            if (self.prev_fast <= self.prev_slow and 
                current_fast > current_slow):
                
                signal = Signal(
                    side='long',
                    entry=self.data.close[0],
                    stop_loss=self.data.close[0] * 0.98,  # 2% below entry
                    take_profit=self.data.close[0] * 1.04,  # 4% above entry
                    confidence=0.7,
                    metadata={
                        'strategy': 'SMA_Crossover',
                        'fast_ma': current_fast,
                        'slow_ma': current_slow,
                        'crossover_type': 'bullish'
                    }
                )
                signals.append(signal)
            
            # Bearish crossover: fast MA crosses below slow MA
            elif (self.prev_fast >= self.prev_slow and 
                  current_fast < current_slow):
                
                signal = Signal(
                    side='short',
                    entry=self.data.close[0],
                    stop_loss=self.data.close[0] * 1.02,  # 2% above entry
                    take_profit=self.data.close[0] * 0.96,  # 4% below entry
                    confidence=0.7,
                    metadata={
                        'strategy': 'SMA_Crossover',
                        'fast_ma': current_fast,
                        'slow_ma': current_slow,
                        'crossover_type': 'bearish'
                    }
                )
                signals.append(signal)
        
        # Update previous values
        self.prev_fast = current_fast
        self.prev_slow = current_slow
        
        return signals
```

### Running the Example
```python
# Save the strategy as src/strategies/sma_crossover.py
# It will be auto-discovered

# Test it
from strategies.registry import get_registry
registry = get_registry()

# Verify it's loaded
sma_strategy = registry.get_strategy('SimpleMovingAverageStrategy')
print(f"Strategy loaded: {sma_strategy.__name__}")

# Validate it
validation = registry.validate_strategy('SimpleMovingAverageStrategy')
print(f"Valid: {validation['valid']}")
```

## 🚨 Troubleshooting

### Common Import Issues

#### 1. "Import 'backtrader' could not be resolved"
**Solution**: Install backtrader in your virtual environment
```bash
source venv/Scripts/activate  # Windows
pip install backtrader
```

#### 2. "attempted relative import with no known parent package"
**Solution**: Fix import paths in your code
```python
# Wrong
from .base import BaseStrategy

# Right (when running from examples/)
import sys
sys.path.insert(0, 'src')
from strategies.base import BaseStrategy
```

#### 3. "ModuleNotFoundError: No module named 'strategies'"
**Solution**: Check your Python path
```python
import sys
print("Python path:", sys.path)
sys.path.insert(0, 'src')  # Add src directory
```

### Strategy Validation Issues

#### 1. "Missing required method: generate_signals"
**Solution**: Implement the required method
```python
def generate_signals(self) -> List[Signal]:
    # Your signal generation logic here
    return []
```

#### 2. "Parameter validation failed"
**Solution**: Check parameter bounds
```python
# Valid ranges
risk_per_trade: 0.0 < x <= 0.1 (0-10%)
position_size: 0.0 < x <= 1.0 (0-100%)
min_risk_reward: x >= 1.0
```

#### 3. "Strategy class is abstract"
**Solution**: Implement all abstract methods
```python
# Make sure you implement generate_signals
def generate_signals(self) -> List[Signal]:
    # Implementation here
    pass
```

### Performance Issues

#### 1. Strategy runs slowly
**Solutions**:
- Reduce lookback periods
- Optimize indicator calculations
- Use vectorized operations where possible

#### 2. Memory usage high
**Solutions**:
- Limit stored data arrays
- Clear old signals periodically
- Use efficient data structures

## 📖 API Reference

### BaseStrategy Class

#### Parameters
```python
params = (
    ('risk_per_trade', 0.02),      # Risk per trade (0-10%)
    ('position_size', 0.1),        # Position size (0-100%)
    ('use_stop_loss', True),       # Enable stop loss
    ('use_take_profit', True),     # Enable take profit
    ('min_risk_reward', 3.0),      # Minimum risk-reward ratio
    ('max_positions', 5),          # Maximum concurrent positions
)
```

#### Methods
```python
def generate_signals(self) -> List[Signal]:
    """Override this method to implement your strategy"""
    pass

def _validate_signal(self, signal: Signal) -> bool:
    """Validate a trading signal (called automatically)"""
    pass

def _calculate_position_size(self, signal: Signal) -> float:
    """Calculate position size based on risk (called automatically)"""
    pass

def get_strategy_stats(self) -> Dict[str, Any]:
    """Get strategy performance statistics"""
    pass
```

### Signal Class

#### Fields
```python
side: str                    # 'long' or 'short'
entry: float                # Entry price
stop_loss: float            # Stop loss price
take_profit: float          # Take profit price
confidence: float           # 0.0-1.0 confidence
timestamp: datetime         # Signal timestamp
metadata: Dict[str, Any]    # Strategy-specific data
```

#### Validation
- `side` must be 'long' or 'short'
- `confidence` must be 0.0-1.0
- `entry`, `stop_loss`, `take_profit` must be positive
- `stop_loss` and `take_profit` must be different from `entry`

### StrategyRegistry Class

#### Methods
```python
def discover_strategies(self) -> List[str]:
    """Auto-discover strategies in the strategies directory"""
    pass

def register_strategy(self, name: str, strategy_class: Type[BaseStrategy], 
                     file_path: str, version: str = "1.0.0") -> StrategyInfo:
    """Manually register a strategy"""
    pass

def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
    """Get a strategy class by name"""
    pass

def validate_strategy(self, name: str) -> Dict[str, Any]:
    """Validate a strategy for correctness"""
    pass

def list_strategies(self) -> List[Dict[str, Any]]:
    """List all registered strategies"""
    pass
```

## 🎓 Best Practices

### Strategy Development
1. **Start Simple**: Begin with basic logic, add complexity gradually
2. **Test Thoroughly**: Use synthetic data and small backtests first
3. **Document Everything**: Clear docstrings and parameter explanations
4. **Follow Patterns**: Use the established signal format and validation
5. **Handle Edge Cases**: Consider market gaps, data issues, etc.

### Performance Optimization
1. **Efficient Indicators**: Use built-in Backtrader indicators when possible
2. **Minimize Storage**: Don't store unnecessary data
3. **Vectorize Operations**: Use numpy/pandas for bulk calculations
4. **Profile Your Code**: Identify bottlenecks with profiling tools

### Risk Management
1. **Always Use Stop Loss**: Never trade without risk control
2. **Respect Position Limits**: Don't exceed max_positions
3. **Validate Risk-Reward**: Ensure minimum 3:1 ratio
4. **Test Parameters**: Backtest with different parameter combinations

## 🤝 Contributing

### Adding New Strategies
1. Create your strategy file in `src/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `generate_signals()` method
4. Add proper documentation
5. Test thoroughly
6. Submit a pull request

### Reporting Issues
1. Check the troubleshooting section first
2. Provide error messages and stack traces
3. Include your environment details
4. Describe what you were trying to do

### Getting Help
- Check the main project README
- Look at existing strategy examples
- Run the demo scripts to see working examples
- Create a minimal reproduction of your issue

## 📝 License

This package is part of the Smart Trading Bot project and follows the same license terms.

---

**Happy Trading! 🚀**

*Remember: This software is for educational purposes. Always test strategies thoroughly before using real money.*
