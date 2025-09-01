# SMC Strategy Configuration System

## Overview

The Smart Money Concepts (SMC) Strategy has been upgraded with a **fully configurable system** that allows you to customize indicators, filters, and SMC elements without changing the code. This system provides:

- **Dynamic indicator configuration** - Enable/disable and configure RSI, MACD, Bollinger Bands, Stochastic, Volume, and ATR
- **Flexible filter system** - Configure which filters to use and their parameters
- **Customizable SMC elements** - Adjust Order Blocks, Fair Value Gaps, Liquidity Pools, and Break of Structure detection
- **Risk management settings** - Configure risk per trade, risk-reward ratios, and position limits
- **Configuration presets** - Ready-to-use configurations for different trading styles

## 🚀 Quick Start

### 1. Load a Configuration Preset

```python
from strategies.smc_config import load_config_from_json

# Load a preset configuration
config = load_config_from_json('configs/smc_presets/conservative.json')

# Use in strategy
strategy_params = {
    'indicators_config': config.indicators.model_dump(),
    'filters_config': config.filters.model_dump(),
    'smc_config': config.smc_elements.model_dump(),
    'risk_config': config.risk_management.model_dump()
}

cerebro.addstrategy(SMCSignalStrategy, **strategy_params)
```

### 2. Create Custom Configuration

```python
from strategies.smc_config import SMCStrategyConfig

custom_config = SMCStrategyConfig(
    name="My Custom SMC",
    htf_timeframe="1h",
    ltf_timeframe="5m",
    indicators={
        'rsi': {'enabled': True, 'period': 21, 'overbought': 75, 'oversold': 25},
        'macd': {'enabled': True, 'fast_period': 8, 'slow_period': 21, 'signal_period': 5}
    },
    filters={
        'rsi': {'enabled': True, 'min_confidence': 0.5},
        'volume': {'enabled': True, 'min_volume_ratio': 1.1}
    }
)
```

### 3. Run Demo Scripts

```bash
# Test all configuration presets
python examples/smc_config_demo.py

# Test with existing demo
python examples/smc_signal_demo.py
```

## 📁 Configuration Structure

### Available Presets

- **`conservative.json`** - Low risk, high quality signals
- **`aggressive.json`** - High frequency, more signals  
- **`scalping.json`** - Fast entries, tight stops
- **`custom.json`** - Template for custom configurations

### Configuration Schema

```json
{
  "name": "Strategy Name",
  "description": "Strategy description",
  "htf_timeframe": "4H",
  "ltf_timeframe": "15m",
  "scalping_mode": false,
  "indicators": {
    "rsi": {"enabled": true, "period": 14, "overbought": 70, "oversold": 30},
    "macd": {"enabled": false, "fast_period": 12, "slow_period": 26, "signal_period": 9},
    "bbands": {"enabled": false, "period": 20, "deviation": 2.0},
    "stochastic": {"enabled": false, "k_period": 14, "d_period": 3, "overbought": 80, "oversold": 20},
    "volume": {"enabled": true, "period": 20},
    "atr": {"enabled": true, "period": 14}
  },
  "filters": {
    "rsi": {"enabled": true, "min_confidence": 0.5},
    "volume": {"enabled": true, "min_volume_ratio": 1.0},
    "bbands": {"enabled": false, "position_threshold": 0.1},
    "macd": {"enabled": false, "signal_cross": true},
    "stochastic": {"enabled": false, "overbought": 80, "oversold": 20},
    "min_filters_required": 2
  },
  "smc_elements": {
    "order_blocks": {"enabled": true, "lookback_bars": 20, "volume_threshold": 1.5},
    "fair_value_gaps": {"enabled": true, "min_gap_pct": 0.5},
    "liquidity_pools": {"enabled": true, "swing_threshold": 0.02},
    "break_of_structure": {"enabled": true, "confirmation_bars": 2}
  },
  "risk_management": {
    "risk_per_trade": 0.015,
    "min_risk_reward": 3.0,
    "max_positions": 3,
    "sl_buffer_atr": 0.15
  }
}
```

## 🔧 Configuration Options

### Indicators

#### RSI
- **`enabled`** - Enable/disable RSI indicator
- **`period`** - RSI calculation period (1-100)
- **`overbought`** - Overbought threshold (50-100)
- **`oversold`** - Oversold threshold (0-50)

#### MACD
- **`enabled`** - Enable/disable MACD indicator
- **`fast_period`** - Fast EMA period (1-50)
- **`slow_period`** - Slow EMA period (1-100)
- **`signal_period`** - Signal line period (1-50)

#### Bollinger Bands
- **`enabled`** - Enable/disable Bollinger Bands
- **`period`** - SMA period (1-100)
- **`deviation`** - Standard deviation multiplier (0.5-5.0)

#### Stochastic
- **`enabled`** - Enable/disable Stochastic oscillator
- **`k_period`** - %K period (1-50)
- **`d_period`** - %D period (1-20)
- **`overbought`** - Overbought threshold (50-100)
- **`oversold`** - Oversold threshold (0-50)

#### Volume
- **`enabled`** - Enable/disable Volume SMA
- **`period`** - Volume SMA period (1-100)

#### ATR
- **`enabled`** - Enable/disable ATR indicator
- **`period`** - ATR calculation period (1-100)

### Filters

#### RSI Filter
- **`enabled`** - Enable/disable RSI filter
- **`min_confidence`** - Minimum confidence threshold (0.0-1.0)

#### Volume Filter
- **`enabled`** - Enable/disable volume filter
- **`min_volume_ratio`** - Minimum volume ratio (0.1-10.0)

#### Bollinger Bands Filter
- **`enabled`** - Enable/disable BB filter
- **`position_threshold`** - Position within bands threshold (0.0-1.0)

#### MACD Filter
- **`enabled`** - Enable/disable MACD filter
- **`signal_cross`** - Require MACD/signal line cross

#### Stochastic Filter
- **`enabled`** - Enable/disable Stochastic filter
- **`overbought`** - Overbought threshold (50-100)
- **`oversold`** - Oversold threshold (0-50)

#### Filter Requirements
- **`min_filters_required`** - Minimum number of filters that must pass (1-5)

### SMC Elements

#### Order Blocks
- **`enabled`** - Enable/disable order block detection
- **`lookback_bars`** - Bars to look back (5-100)
- **`volume_threshold`** - Volume expansion threshold (0.5-5.0)

#### Fair Value Gaps
- **`enabled`** - Enable/disable FVG detection
- **`min_gap_pct`** - Minimum gap percentage (0.1-10.0)

#### Liquidity Pools
- **`enabled`** - Enable/disable liquidity pool detection
- **`swing_threshold`** - Minimum swing size (0.005-0.1)

#### Break of Structure
- **`enabled`** - Enable/disable BoS detection
- **`confirmation_bars`** - Confirmation bars required (1-10)

### Risk Management

- **`risk_per_trade`** - Risk per trade (0.001-0.1)
- **`min_risk_reward`** - Minimum risk-reward ratio (1.0-10.0)
- **`max_positions`** - Maximum concurrent positions (1-10)
- **`sl_buffer_atr`** - Stop loss buffer in ATR multiples (0.05-1.0)

## 📊 Trading Styles

### Conservative Configuration
- **Risk Level**: Low
- **Signal Quality**: High
- **Frequency**: Low
- **Indicators**: RSI, MACD, Bollinger Bands
- **Filters**: Strict (3+ filters required)
- **Risk**: 1% per trade, 4:1 R:R minimum

### Aggressive Configuration
- **Risk Level**: Medium-High
- **Signal Quality**: Medium
- **Frequency**: High
- **Indicators**: RSI, Volume
- **Filters**: Lenient (2+ filters required)
- **Risk**: 2% per trade, 2.5:1 R:R minimum

### Scalping Configuration
- **Risk Level**: High
- **Signal Quality**: Medium
- **Frequency**: Very High
- **Indicators**: RSI, Stochastic, Volume
- **Filters**: Medium (2+ filters required)
- **Risk**: 0.5% per trade, 2:1 R:R minimum

## 🔄 Backward Compatibility

The new configuration system is **fully backward compatible** with existing code:

- Legacy parameters still work
- Old demo scripts continue to function
- Existing strategies will use default configuration
- Gradual migration path available

### Legacy Parameter Mapping

```python
# Old way (still works)
strategy_params = {
    'use_rsi': True,
    'rsi_overbought': 70,
    'risk_per_trade': 0.01
}

# New way (recommended)
strategy_params = {
    'indicators_config': {'rsi': {'enabled': True, 'overbought': 70}},
    'risk_config': {'risk_per_trade': 0.01}
}
```

## 🧪 Testing

### Run Configuration Tests

```bash
# Test all presets
python examples/smc_config_demo.py

# Test specific configuration
python examples/smc_signal_demo.py
```

### Validation

The configuration system includes automatic validation:

- Parameter range checking
- Required field validation
- Timeframe format validation
- Configuration structure validation

## 📈 Performance Monitoring

The strategy now provides enhanced statistics:

```python
stats = strategy.get_strategy_stats()

# Configuration information
config_info = stats['configuration']
print(f"Configuration: {config_info['name']}")
print(f"Indicators Enabled: {config_info['indicators_enabled']}")
print(f"Filters Enabled: {config_info['filters_enabled']}")
print(f"SMC Elements Enabled: {config_info['smc_elements_enabled']}")
```

## 🚀 Advanced Usage

### Dynamic Configuration Changes

```python
# Load configuration
config = load_config_from_json('configs/smc_presets/conservative.json')

# Modify during runtime
config.indicators.rsi.period = 21
config.filters.min_filters_required = 3

# Apply to strategy
strategy.config = config
```

### Custom Filter Logic

```python
# Create custom filter
def custom_filter(direction: str, config) -> bool:
    # Your custom logic here
    return True

# Add to strategy
strategy._check_custom_filter = custom_filter
```

### Configuration Templates

```python
# Create template
template = SMCStrategyConfig.get_conservative_config()
template.name = "My Template"
template.description = "Based on conservative preset"

# Save template
save_config_to_json(template, 'my_template.json')
```

## 🔍 Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file path and JSON syntax
   - Verify required fields are present
   - Check parameter value ranges

2. **Indicators not working**
   - Ensure indicators are enabled in configuration
   - Check data feed availability
   - Verify indicator parameters

3. **Filters too strict**
   - Reduce `min_filters_required`
   - Enable more filters
   - Adjust filter thresholds

### Debug Mode

Enable debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Examples

See the `examples/` directory for complete working examples:

- `smc_config_demo.py` - Configuration system demonstration
- `smc_signal_demo.py` - Updated signal strategy demo
- `backtest_demo.py` - Backtesting with configurations

## 🤝 Contributing

To add new configuration options:

1. Update `SMCStrategyConfig` class
2. Add validation rules
3. Update default configurations
4. Add to preset configurations
5. Update documentation

## 📄 License

This configuration system is part of the Smart Trading Bot project and follows the same license terms.

---

**Need Help?** Check the examples, run the demo scripts, or review the configuration presets for guidance.
