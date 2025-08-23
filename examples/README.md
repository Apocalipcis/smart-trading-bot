# Examples

This directory contains demonstration scripts for the smart-trading-bot package.

## Running the Examples

### Option 1: Direct Python Execution
```bash
# From the project root directory
python examples/backtest_demo.py
```

### Option 2: As a Module
```bash
# From the project root directory
python -m examples
```

### Option 3: Install in Development Mode (Recommended)
```bash
# Install the package in development mode to resolve import issues
python install_dev.py

# Then run examples normally
python examples/backtest_demo.py
```

## Available Examples

### backtest_demo.py
Demonstrates the core functionality of the backtests package:

- **Storage Demo**: Shows how to save and load backtest results
- **Metrics Demo**: Demonstrates performance and risk metrics calculation
- **Data Integrity Demo**: Shows data quality checking and fixing

## What You'll See

The demo will output:
- Backtest storage operations (save/load)
- Performance metrics calculation
- Risk analysis (drawdown, VaR, etc.)
- Data integrity checking
- Data quality issue detection and fixing

## Requirements

- Python 3.11+
- Virtual environment activated
- Required packages installed (pandas, numpy, etc.)

## Troubleshooting

If you encounter import errors:
1. Make sure you're running from the project root directory
2. Activate your virtual environment
3. Install the package in development mode: `python install_dev.py`
4. Check that all required packages are installed

## Next Steps

After running the examples, you can:
- Explore the source code in `src/backtests/`
- Run the test suite: `pytest tests/`
- Move on to implementing strategies (Step 4)
