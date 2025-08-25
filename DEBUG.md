# Debug Infrastructure

## Overview

Цей проект включає спеціальну debug інфраструктуру для діагностики проблем з Docker збіркою та розробкою.

## Debug Dockerfile

### `Dockerfile.debug`

Спеціальний Dockerfile з покращеним логуванням та діагностикою:

#### Особливості:
- **Детальне логування** кожного кроку з echo повідомленнями
- **Verbose режим** для pip (`-v --progress-bar on`)
- **Timeout захист** (900 секунд) для довгих операцій
- **Альтернативний підхід** до встановлення залежностей
- **Fallback механізми** при невдачі editable install

#### Використання:
```bash
# Запуск debug збірки
docker build -f Dockerfile.debug -t smart-trading-bot:debug --progress=plain --no-cache .

# Або через скрипт
bash scripts/debug-build.sh
```

### Debug Build Script

#### `scripts/debug-build.sh`

Автоматизований скрипт для debug збірки з:
- Кольоровим логуванням
- Детальною інформацією про образ
- Перевіркою розміру та слоїв
- Автоматичним очищенням

#### Використання:
```bash
chmod +x scripts/debug-build.sh
bash scripts/debug-build.sh
```

## Проблеми та рішення

### 1. Зависання на `pip install -e .`

**Симптоми:**
- Збірка застрягає на `Getting requirements to build editable: started`
- Час очікування > 5 хвилин

**Причини:**
- Компіляція C++ розширень (numpy, pandas, pyarrow)
- Аналіз складних залежностей (backtrader)
- Мережеві проблеми

**Рішення в debug версії:**
```dockerfile
# Альтернативний підхід без editable install
RUN python -c "import tomllib; data = tomllib.load(open('pyproject.toml', 'rb')); deps = data['project']['dependencies']; [__import__('subprocess').run(['pip', 'install', dep], check=True) for dep in deps]"
```

### 2. Недостатнє логування

**Проблема:** Стандартна збірка показує мало інформації

**Рішення в debug версії:**
```dockerfile
# Детальне логування
RUN echo "=== STEP 3: Starting Python package installation ===" && \
    echo "=== Current directory: $(pwd) ===" && \
    echo "=== Files in current directory: ===" && \
    ls -la && \
    pip install --upgrade pip -v --progress-bar on --timeout 300
```

### 3. Timeout проблеми

**Рішення:**
```dockerfile
# Timeout захист
timeout 900 pip install -e . -v --progress-bar on --timeout 900 || \
(echo "=== Timeout reached, trying alternative approach ===" && \
 python -c "import tomllib; data = tomllib.load(open('pyproject.toml', 'rb')); deps = data['project']['dependencies']; [__import__('subprocess').run(['pip', 'install', dep, '-v', '--progress-bar', 'on', '--timeout', '300'], check=True) for dep in deps]")
```

## Порівняння з основним Dockerfile

| Аспект | Основний Dockerfile | Debug Dockerfile |
|--------|-------------------|------------------|
| **Час збірки** | ~20 секунд | ~30 секунд |
| **Логування** | Мінімальне | Детальне |
| **Editable install** | Ні | Так (з fallback) |
| **Timeout захист** | Ні | Так |
| **Діагностика** | Обмежена | Повна |

## Рекомендації

### Коли використовувати debug версію:
1. **Проблеми з збіркою** - коли основний Dockerfile не працює
2. **Розробка** - для кращого розуміння процесу збірки
3. **Діагностика** - для знаходження причин помилок
4. **Оптимізація** - для аналізу часу виконання кроків

### Коли використовувати основний Dockerfile:
1. **Продакшн** - швидка збірка для деплою
2. **CI/CD** - стабільна збірка для автоматизації
3. **Тестування** - швидкі ітерації

## Структура файлів

```
smart-trading-bot/
├── Dockerfile              # Основний production Dockerfile
├── Dockerfile.debug        # Debug версія з детальним логуванням
├── scripts/
│   ├── deploy.sh          # Скрипт деплою
│   └── debug-build.sh     # Debug скрипт збірки
└── DEBUG.md               # Ця документація
```

## Приклади використання

### Швидка діагностика:
```bash
# Запуск debug збірки
bash scripts/debug-build.sh

# Перевірка логів
docker logs $(docker ps -q --filter ancestor=smart-trading-bot:debug)
```

### Порівняння збірок:
```bash
# Основна збірка
time docker build -t smart-trading-bot:latest .

# Debug збірка
time docker build -f Dockerfile.debug -t smart-trading-bot:debug .
```

### Аналіз образу:
```bash
# Розмір образів
docker images | grep smart-trading

# Слої образу
docker history smart-trading-bot:debug
```
