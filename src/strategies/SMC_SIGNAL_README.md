# SMCSignalStrategy - Signal-Only Smart Money Concepts Strategy

## Overview

The `SMCSignalStrategy` is a production-ready Smart Money Concepts (SMC) strategy that generates trading signals based on institutional order flow analysis. This strategy is designed to be **signal-only** - it generates entry, stop-loss, and take-profit levels but does NOT automatically manage trades after entry. The trader manually decides how to manage trades.

## Key Features

- **Multi-Timeframe Analysis**: HTF (1D/4H) for bias and key zones, LTF (15M) for entry timing
- **Advanced SMC Detection**: Order Blocks, Fair Value Gaps, Liquidity Pools, Liquidity Sweeps, BoS/ChoCH
- **Configurable Filters**: RSI, OBV, Volume, Bollinger Bands
- **Fixed Risk Management**: Calculates SL/TP once at entry, no auto-adjustment
- **Full Backtestability**: Compatible with Backtrader for performance evaluation

## Strategy Logic

### 1. Higher Timeframe (HTF) Analysis
- **Market Bias Detection**: Uses 50 EMA and price structure to determine bullish/bearish bias
- **Order Block Detection**: Identifies last opposing candle before impulsive moves with volume expansion
- **Fair Value Gap Detection**: Finds imbalance zones with configurable minimum gap size
- **Liquidity Pool Marking**: Identifies swing highs/lows for potential liquidity zones

### 2. Lower Timeframe (LTF) Entry Validation
- **Zone Validation**: Only generates signals when price is inside/near HTF zones
- **Liquidity Sweep Detection**: Confirms wicks through swing levels with close back in range
- **Break of Structure (BoS)**: Validates micro-structure breaks in HTF bias direction
- **FVG Refinement**: Optional entry optimization using fresh LTF gaps

### 3. Signal Generation
- **Entry Price**: Current market price when conditions align
- **Stop Loss**: Fixed at OB boundary + ATR buffer (no auto-adjustment)
- **Take Profit**: Minimum 3:1 risk-reward ratio from entry
- **Confidence Score**: 0.0-1.0 based on filters passed and SMC confirmations

## Configuration

### Basic Parameters
```python
cfg = {
    'htf_timeframe': '4H',           # Higher timeframe (1D/4H)
    'ltf_timeframe': '15m',          # Lower timeframe (15M)
    'scalping_mode': False,          # Enable M1-M5 scalping
    'risk_per_trade': 0.01,          # 1% risk per trade
    'min_risk_reward': 3.0,          # Minimum 3:1 R:R
    'max_positions': 3,              # Max concurrent positions
}
```

### SMC Detection Parameters
```python
cfg.update({
    'volume_ratio_threshold': 1.5,   # Volume expansion threshold
    'fvg_min_pct': 0.5,             # Minimum FVG gap (0.5%)
    'ob_lookback_bars': 20,         # Bars to look back for OBs
    'swing_threshold': 0.02,         # Minimum swing size (2%)
    'sl_buffer_atr': 0.15,           # SL buffer in ATR multiples
})
```

### Indicator Filters
```python
cfg.update({
    'use_rsi': True,                 # Enable RSI filter
    'use_obv': True,                 # Enable OBV filter
    'use_bbands': False,             # Enable Bollinger Bands filter
    'rsi_overbought': 70,            # RSI overbought threshold
    'rsi_oversold': 30,              # RSI oversold threshold
})
```

## Usage Examples

### Basic Setup
```python
import backtrader as bt
from src.strategies.smc_signal import SMCSignalStrategy

# Create Cerebro engine
cerebro = bt.Cerebro()

# Add data feeds with roles
htf_data = bt.feeds.PandasData(dataname=htf_df, name='HTF')
ltf_data = bt.feeds.PandasData(dataname=ltf_df, name='LTF')

cerebro.adddata(htf_data, name='HTF')
cerebro.adddata(ltf_data, name='LTF')

# Add strategy
cerebro.addstrategy(SMCSignalStrategy, 
    htf_timeframe='4H',
    ltf_timeframe='15m',
    risk_per_trade=0.01
)

# Run backtest
results = cerebro.run()
strategy = results[0]
```

### Multi-Timeframe Data Setup
```python
# HTF data (4H timeframe)
htf_df = pd.read_parquet('data/candles/binance_futures/BTCUSDT/4h.parquet')
htf_data = bt.feeds.PandasData(
    dataname=htf_df,
    datetime=None,
    open='open', high='high', low='low', close='close', volume='volume',
    name='HTF'
)

# LTF data (15m timeframe)
ltf_df = pd.read_parquet('data/candles/binance_futures/BTCUSDT/15m.parquet')
ltf_data = bt.feeds.PandasData(
    dataname=ltf_df,
    datetime=None,
    open='open', high='high', low='low', close='close', volume='volume',
    name='LTF'
)

# Add to Cerebro
cerebro.adddata(htf_data, name='HTF')
cerebro.adddata(ltf_data, name='LTF')
```

## Signal Output

### Signal Structure
```python
Signal(
    side='long' | 'short',
    entry=float,           # Entry price
    stop_loss=float,       # Fixed stop loss
    take_profit=float,     # Take profit target
    confidence=float,      # 0.0-1.0 confidence score
    metadata=dict          # SMC-specific information
)
```

### Signal Metadata
```python
metadata = {
    'strategy': 'SMCSignalStrategy',
    'htf_trend': 'bullish' | 'bearish' | 'neutral',
    'matched_ob_id': 'OB_bull_123',           # Matched order block ID
    'matched_fvg_id': None,                   # Matched FVG ID (if applicable)
    'liquidity_sweep': True,                  # Liquidity sweep detected
    'bos_confirmation': True,                 # BoS confirmed
    'filters_passed': ['rsi', 'volume', 'obv'], # Passed filters
    'confidence_factors': {                   # Confidence breakdown
        'base': 0.5,
        'rsi': 0.15,
        'volume': 0.15,
        'obv': 0.1,
        'trend': 0.1,
        'sweep': 0.1,
        'bos': 0.1
    },
    'htf_zone_type': 'OrderBlock',           # Type of HTF zone
    'sweep_bar_index': 1234,                 # Index of sweep bar
    'bos_level': 50000.0                     # Price level of BoS
}
```

## Risk Management

### Position Sizing
- Uses `risk_per_trade` parameter for position sizing
- Position size calculated from stop loss distance
- Maximum concurrent positions limited by `max_positions`

### Stop Loss & Take Profit
- **Stop Loss**: Fixed at entry, calculated as OB boundary + ATR buffer
- **Take Profit**: Fixed at entry, minimum 3:1 risk-reward ratio
- **No Auto-Adjustment**: Stops remain fixed after entry

### Example Risk Calculation
```python
# For a long position:
entry_price = 50000.0
ob_low = 49500.0
atr = 200.0
sl_buffer = atr * 0.15 = 30.0

stop_loss = ob_low - sl_buffer = 49470.0
risk_per_unit = entry_price - stop_loss = 530.0

# If risk_per_trade = 0.01 (1%):
risk_amount = account_balance * 0.01
position_size = risk_amount / risk_per_unit

# Take profit at 3:1 R:R:
take_profit = entry_price + (risk_per_unit * 3) = 51590.0
```

## Performance Metrics

### Strategy Statistics
```python
stats = strategy.get_strategy_stats()

# Base metrics
total_signals = stats['total_signals']
current_positions = stats['current_positions']
total_trades = stats['total_trades']
total_pnl = stats['total_pnl']
win_rate = stats['win_rate']

# SMC-specific metrics
htf_trend = stats['htf_trend']
htf_order_blocks = stats['htf_order_blocks_count']
htf_fair_value_gaps = stats['htf_fair_value_gaps_count']
htf_liquidity_pools = stats['htf_liquidity_pools_count']
current_rsi = stats['current_rsi']
current_volume_ratio = stats['current_volume_ratio']
```

## Backtesting Integration

### Backtest Configuration
```python
from src.backtests.models import BacktestConfig

config = BacktestConfig(
    symbol="BTCUSDT",
    strategy_name="SMCSignalStrategy",
    strategy_params={
        'htf_timeframe': '4H',
        'ltf_timeframe': '15m',
        'risk_per_trade': 0.01,
        'min_risk_reward': 3.0,
        'use_rsi': True,
        'use_obv': True
    },
    timeframes=["4H", "15m"],
    tf_roles={"4H": "HTF", "15m": "LTF"},
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    initial_cash=10000.0
)
```

### Running Backtests
```python
from src.backtests.runner import BacktestRunner

runner = BacktestRunner()
result = runner.run_backtest(config)

print(f"Total Return: {result.total_return:.2%}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Win Rate: {result.win_rate:.2%}")
```

## Advanced Configuration

### Scalping Mode
```python
# Enable M1-M5 scalping
cfg = {
    'scalping_mode': True,
    'htf_timeframe': '1H',      # Use 1H as HTF for scalping
    'ltf_timeframe': '1m',      # Use 1m as LTF for scalping
    'risk_per_trade': 0.005,    # Lower risk for scalping
    'min_risk_reward': 2.0,     # Lower R:R for scalping
}
```

### Custom Filter Thresholds
```python
cfg = {
    'rsi_overbought': 75,       # More conservative RSI
    'rsi_oversold': 25,         # More conservative RSI
    'volume_ratio_threshold': 2.0,  # Higher volume requirement
    'fvg_min_pct': 1.0,        # Larger FVG requirement
    'swing_threshold': 0.03,    # Larger swing requirement
}
```

## Troubleshooting

### Common Issues

1. **"Invalid multi-timeframe setup"**
   - Ensure data feeds are named 'HTF' and 'LTF'
   - Check that both data feeds have sufficient data

2. **"HTF and LTF data feeds not available"**
   - Verify data feed names match expected roles
   - Check data feed initialization order

3. **No signals generated**
   - Ensure sufficient historical data (50+ HTF bars, 20+ LTF bars)
   - Check indicator readiness
   - Verify SMC detection parameters

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check strategy state
print(f"HTF Trend: {strategy.htf_trend}")
print(f"HTF Order Blocks: {len(strategy.htf_order_blocks)}")
print(f"LTF Swings: {len(strategy.ltf_swings)}")
```

## Best Practices

### Data Quality
- Use high-quality, clean OHLCV data
- Ensure proper timestamp alignment between timeframes
- Avoid data gaps and anomalies

### Parameter Tuning
- Start with default parameters
- Adjust based on market conditions and asset characteristics
- Use walk-forward analysis for parameter optimization

### Risk Management
- Never risk more than 2% per trade
- Consider market volatility when setting ATR buffers
- Monitor strategy performance regularly

## Performance Considerations

### Memory Usage
- Strategy keeps HTF and LTF data in memory
- SMC detection results cached for performance
- Consider data length limits for large datasets

### Computational Efficiency
- SMC detection runs on each bar
- Optimized algorithms for real-time performance
- Minimal impact on backtest execution speed

## Future Enhancements

### Planned Features
- Enhanced FVG detection algorithms
- Advanced liquidity sweep patterns
- Machine learning confidence scoring
- Real-time market structure analysis

### Customization Points
- Custom SMC detection algorithms
- Additional indicator filters
- Alternative risk management models
- Multi-asset correlation analysis

## Support

For questions, issues, or feature requests:
- Check the strategy logs for detailed error messages
- Review the demo script for usage examples
- Consult the base strategy documentation
- Review the SMC methodology literature

---

**Note**: This strategy is designed for educational and research purposes. Always test thoroughly in simulation before using with real capital. Past performance does not guarantee future results.
