# Python-Binance Integration

Цей документ описує нову інтеграцію проекту з офіційною бібліотекою [python-binance](https://python-binance.readthedocs.io/en/latest/).

## 🚀 Переваги інтеграції

### До (власна реалізація):
- ❌ 400+ рядків власного HTTP клієнта
- ❌ Ручна реалізація rate limiting
- ❌ Базова обробка помилок
- ❌ Обмежена підтримка екзотичних символів
- ❌ Складність роботи з історичними даними

### Після (python-binance):
- ✅ Використання офіційної бібліотеки
- ✅ Автоматичний rate limiting
- ✅ Продвинута обробка помилок
- ✅ Підтримка історичних даних через `get_historical_klines()`
- ✅ Краща підтримка екзотичних символів

## 📁 Нові модулі

### 1. `src/data/binance_client_new.py`
Новий Binance клієнт, який використовує python-binance замість власної реалізації.

**Ключові особливості:**
- Асинхронна робота з `AsyncClient`
- Підтримка Futures API
- Вбудована обробка помилок Binance
- Підтримка тестнету та різних TLD

**Приклад використання:**
```python
from src.data.binance_client_new import BinanceClient, BinanceConfig

config = BinanceConfig(
    api_key="your_api_key",  # Опціонально
    api_secret="your_api_secret",  # Опціонально
    testnet=False,  # Використовувати тестнет для розробки
    tld="com"  # com, us, jp, etc.
)

async with BinanceClient(config) as client:
    # Тест підключення
    is_connected = await client.ping()
    
    # Отримання історичних даних
    klines = await client.get_historical_klines(
        symbol="BTCUSDT",
        interval="1h",
        start_str="1 week ago UTC",
        end_str="now UTC"
    )
    
    # Отримання поточної ціни
    price = await client.get_symbol_price("BTCUSDT")
```

### 2. `src/data/downloader_new.py`
Новий завантажувач даних, який використовує python-binance для отримання історичних даних.

**Ключові особливості:**
- Спрощена логіка завантаження
- Використання `get_historical_klines()` з python-binance
- Підтримка екзотичних символів (заглушка для майбутньої реалізації)
- Збереження в Parquet форматі

**Приклад використання:**
```python
from src.data.downloader_new import DataDownloader
from datetime import datetime, timezone, timedelta

downloader = DataDownloader(data_dir="./data")

# Завантаження даних для одного символу
result = await downloader.download_symbol_data(
    symbol="BTCUSDT",
    timeframe="1h",
    start_date=datetime.now(timezone.utc) - timedelta(days=7),
    end_date=datetime.now(timezone.utc)
)

# Завантаження для екзотичного символу
try:
    result = await downloader.download_exotic_symbol_data(
        symbol="BTC",
        timeframe="15m",
        start_date=datetime.now(timezone.utc) - timedelta(days=7),
        end_date=datetime.now(timezone.utc)
    )
except NotImplementedError as e:
    print(f"Потрібна інтеграція з Binance Vision API: {e}")
```

## 🔧 Міграція зі старої системи

### Проста заміна імпорту:
```python
# Старий спосіб
from src.data.downloader import DataDownloader
from src.data.binance_client import BinanceClient

# Новий спосіб
from src.data.downloader_new import DataDownloader
from src.data.binance_client_new import BinanceClient
```

### API залишається тим самим:
```python
# Обидва варіанти мають однаковий інтерфейс
downloader = DataDownloader(data_dir="./data")
result = await downloader.download_symbol_data(
    symbol="BTCUSDT",
    timeframe="1h",
    start_date=start_date,
    end_date=end_date
)
```

## 📊 Підтримувані таймфрейми

- `1m` - 1 хвилина (максимум 1 день)
- `5m` - 5 хвилин (максимум 5 днів)
- `15m` - 15 хвилин (максимум 15 днів)
- `30m` - 30 хвилин (максимум 30 днів)
- `1h` - 1 година (максимум 30 днів)
- `4h` - 4 години (максимум 120 днів)
- `1d` - 1 день (максимум 365 днів)

## 🧪 Тестування

Запустіть тести для нових модулів:
```bash
# Всі тести python-binance інтеграції
python -m pytest tests/test_python_binance_integration.py -v

# Конкретний тест
python -m pytest tests/test_python_binance_integration.py::TestBinanceClient::test_ping -v
```

## 🎯 Демо

Запустіть демо скрипт:
```bash
python examples/download_data_python_binance_demo.py
```

## 🔮 Майбутні покращення

### 1. Інтеграція з Binance Vision API
Для екзотичних символів як `BTC`:
```python
# TODO: Реалізувати завантаження з data.binance.vision
async def download_from_binance_vision(self, symbol, timeframe, start_date, end_date):
    # Пряме завантаження CSV з Binance Vision
    pass
```

### 2. WebSocket підтримка
```python
# TODO: Додати WebSocket для real-time даних
async def start_websocket_stream(self, symbols, intervals):
    # Використання python-binance WebSocket
    pass
```

### 3. Розширена підтримка екзотичних символів
```python
# TODO: Автоматичне визначення джерела даних
async def download_symbol_data_smart(self, symbol, timeframe, start_date, end_date):
    try:
        # Спочатку спробувати стандартне API
        return await self.download_symbol_data(symbol, timeframe, start_date, end_date)
    except Exception:
        # Якщо не вдалося, спробувати Binance Vision
        return await self.download_from_binance_vision(symbol, timeframe, start_date, end_date)
```

## 📚 Корисні посилання

- [python-binance документація](https://python-binance.readthedocs.io/en/latest/)
- [Binance Vision API](https://data.binance.vision/)
- [Binance Futures API](https://binance-docs.github.io/apidocs/futures/en/)
- [Приклади python-binance](https://github.com/sammchardy/python-binance/tree/master/examples)

## 🚨 Відомі проблеми

1. **Читання існуючих Parquet файлів** - потрібно виправити логіку в `_get_existing_data_stats()`
2. **Екзотичні символи** - поки що не реалізовано, використовується заглушка
3. **WebSocket** - поки що не інтегровано

## 💡 Рекомендації

1. **Для нових проектів** - використовуйте нові модулі з python-binance
2. **Для існуючих проектів** - поступово мігруйте, замінюючи імпорти
3. **Для екзотичних символів** - чекайте на реалізацію Binance Vision API інтеграції
4. **Для тестування** - використовуйте `testnet=True` в конфігурації

---

**Примітка:** Ця інтеграція значно спрощує код та розширює можливості проекту. python-binance - це стандарт де-факто для роботи з Binance API в Python.
