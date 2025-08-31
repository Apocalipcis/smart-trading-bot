# Smart Trading Bot - Developer Cheatsheet

## 🚀 Quick Start

### Activate Virtual Environment

``` bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Install Dependencies

``` bash
pip install -e .
pip install -e ".[dev]"
```

## 🧪 Testing

### Run All Tests

``` bash
python -m pytest tests/ -v
```

### Run a Specific Test

``` bash
python -m pytest tests/test_data_preparation.py::TestBacktestDataPreparer::test_prepare_timeframe_data_download_error -v
```

### Run Tests with Coverage

``` bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Run Strategy Tests

``` bash
python -m pytest tests/test_strategies.py -v
```

## 🐳 Docker Commands

### Rebuild Image Without Cache

``` bash
docker build --no-cache -t smart-trading-bot:latest .
```

### Clean Docker Cache

``` bash
docker system prune -f
```

### Start Services

``` bash
docker compose up -d
```

### Stop Services

``` bash
docker compose down
```

### Check Status

``` bash
docker compose ps
```

### View Logs

``` bash
docker compose logs -f
```

### Restart Services

``` bash
docker compose restart
```

## 🔧 Development

### Run Backend API

``` bash
cd src
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Frontend (Development)

``` bash
cd web
npm run dev
```

### Build Frontend

``` bash
cd web
npm run build
```

## 📊 Data & Analysis

### Run Backtest

``` bash
python examples/backtest_demo.py
```

### Download Data

``` bash
python examples/download_data_demo.py
```

### Simulate Trading

``` bash
python examples/simulation_demo.py
```

## 🚨 Troubleshooting

### If the Interface Doesn't Update After deploy.sh:

1.  Clear Docker cache:

    ``` bash
    docker system prune -f
    ```

2.  Rebuild the image without cache:

    ``` bash
    docker build --no-cache -t smart-trading-bot:latest .
    ```

3.  Restart services:

    ``` bash
    docker compose down
    docker compose up -d
    ```

### If Tests Fail:

1.  Check virtual environment:

    ``` bash
    source venv/Scripts/activate  # Windows
    source venv/bin/activate      # Linux/Mac
    ```

2.  Reinstall dependencies:

    ``` bash
    pip install -e ".[dev]"
    ```

3.  Run the failing test directly:

    ``` bash
    python -m pytest tests/test_name.py::TestClass::test_method -v
    ```

## 📁 Project Structure

    smart-trading-bot/
    ├── src/                    # Core code
    │   ├── api/               # API endpoints
    │   ├── backtests/         # Backtesting engine
    │   ├── data/              # Data handling
    │   ├── strategies/        # Trading strategies
    │   └── orders/            # Order management
    ├── web/                   # Frontend (React/TypeScript)
    ├── tests/                 # Tests
    ├── examples/              # Usage examples
    ├── data/                  # Data & artifacts
    └── logs/                  # Logs

## 🔍 Useful Commands

### Code Search

``` bash
# Text search
grep -r "search_term" src/

# Find files
find . -name "*.py" -type f
```

### Git Commands

``` bash
# View changes
git status
git diff

# Commit changes
git add .
git commit -m "Description of changes"

# View history
git log --oneline -10
```

### Logs & Debugging

``` bash
# Application logs
tail -f logs/app.log

# Docker container logs
docker logs -f container_name
```

## 📚 Additional Resources

-   **API Docs**: http://localhost:8000/docs
-   **Swagger UI**: http://localhost:8000/redoc
-   **Frontend**: http://localhost:80
-   **Backend API**: http://localhost:8000

## ⚠️ Important Notes

1.  **Always use a virtual environment** for Python dependencies\
2.  **Do not commit .env files** -- they contain secrets\
3.  **Rebuild Docker images** after major code changes\
4.  **Run tests** before committing changes

------------------------------------------------------------------------

*Last update: \$(date)*
