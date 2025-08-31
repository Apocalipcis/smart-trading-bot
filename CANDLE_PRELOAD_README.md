# Candle Preload for Backtests

## Overview

The Candle Preload feature automatically ensures that all required Binance candles (for selected trading pairs and timeframes) are downloaded and stored in the project's Parquet format before initiating a backtest. This eliminates the need for manual data preparation and ensures data completeness.

## Features

- **Automatic Data Discovery**: Checks existing Parquet files for coverage
- **Smart Downloading**: Only downloads missing data segments
- **Multi-timeframe Support**: Handles HTF/LTF role assignments
- **Backwards Compatibility**: Supports existing single-timeframe configurations
- **Error Handling**: Graceful fallback for download failures
- **Performance Optimization**: Reuses existing data when possible

## Architecture

### Core Components

1. **`BacktestDataPreparer`** (`src/backtests/preparation.py`)
   - Main class for data preparation logic
   - Handles data availability checks
   - Coordinates with `DataDownloader` for missing data

2. **Enhanced `BacktestConfig`** (`src/backtests/models.py`)
   - Supports multiple timeframes and roles
   - Maintains backwards compatibility
   - Includes validation for timeframe constraints

3. **Updated `BacktestRunner`** (`src/backtests/runner.py`)
   - Integrates data preparation before backtest execution
   - Supports multiple timeframe data loading
   - Maintains legacy compatibility

4. **API Integration** (`src/api/routers/backtests.py`)
   - Automatically triggers data preparation
   - Handles preparation errors gracefully
   - Provides meaningful user feedback

## Usage

### Basic Usage

```python
from src.backtests.preparation import prepare_backtest_data
from datetime import datetime, timezone

# Prepare data for a single symbol and multiple timeframes
preparation_result = await prepare_backtest_data(
    symbol="BTCUSDT",
    timeframes=["5m", "1h"],
    start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    end_date=datetime(2024, 1, 31, tzinfo=timezone.utc)
)

print(f"Files downloaded: {preparation_result['total_files_downloaded']}")
print(f"Files reused: {preparation_result['total_files_reused']}")
```

### Multi-Symbol Preparation

```python
from src.backtests.preparation import BacktestDataPreparer

preparer = BacktestDataPreparer()

# Prepare data for multiple symbols
result = await preparer.prepare_multiple_symbols_data(
    symbols=["BTCUSDT", "ETHUSDT"],
    timeframes=["1h", "4h"],
    start_date=start_date,
    end_date=end_date
)
```

### Backtest Configuration

```python
from src.backtests.models import BacktestConfig

# New multi-timeframe configuration
config = BacktestConfig(
    symbol="BTCUSDT",
    strategy_name="SMCSignalStrategy",
    timeframes=["5m", "1h", "4h"],
    tf_roles={
        "5m": "LTF",   # Lower Timeframe
        "1h": "LTF",   # Lower Timeframe
        "4h": "HTF"    # Higher Timeframe
    },
    start_date=start_date,
    end_date=end_date,
    initial_cash=10000.0
)

# Legacy single-timeframe configuration (still supported)
legacy_config = BacktestConfig(
    symbol="BTCUSDT",
    strategy_name="SMCSignalStrategy",
    timeframe="1h",  # Legacy field
    start_date=start_date,
    end_date=end_date,
    initial_cash=10000.0
)
```

### Running Backtests

```python
from src.backtests.runner import BacktestRunner

# Data preparation happens automatically
runner = BacktestRunner()
result = await runner.run_backtest(config)

if result.status == "completed":
    print(f"Backtest completed: {result.total_return:.2f}% return")
else:
    print(f"Backtest failed: {result.error_message}")
```

## API Usage

### Creating a Backtest

```bash
curl -X POST "http://localhost:8000/backtests/" \
  -H "Content-Type: application/json" \
  -d '{
    "pairs": ["BTCUSDT"],
    "strategy": "SMCSignalStrategy",
    "timeframes": ["5m", "1h", "4h"],
    "tf_roles": {
      "5m": "LTF",
      "1h": "LTF", 
      "4h": "HTF"
    },
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "initial_balance": 10000.0
  }'
```

### Legacy API Support

```bash
# Legacy single-timeframe request (automatically converted)
curl -X POST "http://localhost:8000/backtests/" \
  -H "Content-Type: application/json" \
  -d '{
    "pair": "BTCUSDT",
    "strategy": "SMCSignalStrategy",
    "timeframe": "1h",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "initial_capital": 10000.0
  }'
```

## Data Storage

### File Structure

```
data/
└── candles/
    └── binance_futures/
        ├── BTCUSDT/
        │   ├── 5m.parquet
        │   ├── 1h.parquet
        │   └── 4h.parquet
        └── ETHUSDT/
            ├── 5m.parquet
            ├── 1h.parquet
            └── 4h.parquet
```

### Data Format

Each Parquet file contains OHLCV data with a datetime index:

- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price  
- `close`: Closing price
- `volume`: Trading volume
- `datetime`: Datetime index (UTC)

## Supported Timeframes

- **Minutes**: `1m`, `3m`, `5m`, `15m`, `30m`
- **Hours**: `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- **Days**: `1d`, `3d`
- **Weeks**: `1w`
- **Months**: `1M`

## Error Handling

### Common Errors

1. **Data Preparation Failed**
   - Network issues during download
   - Insufficient disk space
   - Invalid date ranges

2. **Unsupported Timeframes**
   - Requested timeframe not in supported list
   - Invalid timeframe format

3. **Date Range Issues**
   - Start date after end date
   - Future dates requested
   - Date range too large for timeframe

### Error Response Format

```json
{
  "detail": {
    "message": "Data preparation failed",
    "error": "Failed to download 1h data: Network timeout",
    "warnings": ["Legacy 'timeframe' field is deprecated"]
  }
}
```

## Performance Considerations

### Data Caching

- Existing Parquet files are reused when possible
- Only missing data segments are downloaded
- Data coverage is checked before downloading

### Rate Limiting

- Respects Binance API rate limits
- Configurable delays between requests
- Batch processing for multiple symbols/timeframes

### Storage Optimization

- Parquet format for efficient storage and querying
- Compressed data storage
- Automatic cleanup of temporary files

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/test_data_preparation.py
pytest tests/test_backtest_runner_integration.py

# Run with coverage
pytest --cov=src tests/
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Error Scenarios**: Failure mode testing
- **Backwards Compatibility**: Legacy API testing

## Configuration

### Environment Variables

```bash
# Data directory (default: "data")
DATA_DIR=/path/to/data

# Binance API configuration
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
```

### Custom Settings

```python
from src.backtests.preparation import BacktestDataPreparer

# Custom data directory
preparer = BacktestDataPreparer(data_dir="/custom/data/path")

# Custom downloader settings
preparer.downloader.rate_limit_delay = 0.2  # 200ms between requests
```

## Troubleshooting

### Common Issues

1. **"Data preparation failed"**
   - Check network connectivity
   - Verify Binance API credentials
   - Ensure sufficient disk space

2. **"Unsupported timeframes"**
   - Verify timeframe format (e.g., "1h", not "1H")
   - Check supported timeframe list

3. **"No data available after filtering"**
   - Verify date range is valid
   - Check if data exists for requested period
   - Ensure timezone handling is correct

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
preparer = BacktestDataPreparer()
result = await preparer.prepare_backtest_data(...)
print(f"Debug info: {result}")
```

## Future Enhancements

### Planned Features

1. **Additional Exchanges**: Support for other cryptocurrency exchanges
2. **Live Trading Integration**: Real-time data preparation for live strategies
3. **Advanced Caching**: Redis-based caching for frequently accessed data
4. **Data Validation**: Enhanced data quality checks and validation
5. **Compression Options**: Configurable compression algorithms

### Extension Points

The modular design allows for easy extension:

- Custom data sources
- Alternative storage formats
- Additional validation rules
- Custom error handling

## Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run tests: `pytest tests/`

### Code Standards

- Follow PEP 8 style guidelines
- Include type hints for all functions
- Write comprehensive docstrings
- Add unit tests for new features
- Maintain backwards compatibility

## Support

For questions or issues:

1. Check the troubleshooting section
2. Review test examples
3. Check existing GitHub issues
4. Create a new issue with detailed information

## License

This feature is part of the Smart Trading Bot project and follows the same license terms.
