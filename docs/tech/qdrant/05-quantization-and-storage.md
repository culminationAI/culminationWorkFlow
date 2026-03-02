# Qdrant: Квантование и управление хранением

> [!TIP]
> **Версия:** Qdrant v1.17.0 (февраль 2026). Параметры SQ, BQ, PQ верифицированы по официальной документации.

---

## 1. Scalar Quantization (SQ)

Преобразует `float32` компоненты вектора в `int8`. Самый универсальный и безопасный метод сжатия.

### Характеристики

| Параметр | Значение |
|----------|----------|
| Сжатие памяти | 4x (с 4 байт до 1 байт на компоненту) |
| Ускорение поиска | До 2x |
| Потеря точности | Минимальная (>99% recall) |
| Совместимость | Любые модели эмбеддингов |

### Конфигурация

```python
from qdrant_client.http import models

# При создании коллекции
client.create_collection(
    collection_name="hero_memories",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
    ),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,       # Отсекает выбросы (top/bottom 0.5%)
            always_ram=True,     # Квантованные вектора всегда в RAM
        ),
    ),
)
```

### Параметры

| Параметр | Описание | По умолчанию |
|----------|----------|-------------|
| `type` | Тип квантования | `int8` (единственный) |
| `quantile` | Квантиль для определения диапазона значений | 0.99 |
| `always_ram` | Хранить квантованные вектора в RAM | true |

### Как работает

1. Для каждой компоненты вектора определяется диапазон [min, max] на основе `quantile`
2. Значения линейно масштабируются в диапазон [0, 255] (int8)
3. При поиске расстояние вычисляется по квантованным значениям
4. Опционально: rescore по оригинальным float32 для топ-N кандидатов

### Rescoring (oversampling)

```python
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    search_params=models.SearchParams(
        quantization=models.QuantizationSearchParams(
            rescore=True,         # Переоценка по оригиналам
            oversampling=2.0,     # Извлечь 2x кандидатов перед rescoring
        ),
    ),
    limit=10,
)
```

---

## 2. Binary Quantization (BQ)

Каждая компонента вектора преобразуется в 1 бит (0 или 1 в зависимости от знака).

### Характеристики

| Параметр | Значение |
|----------|----------|
| Сжатие памяти | 32x |
| Ускорение поиска | До 40x (Hamming distance) |
| Потеря точности | Значительная (5-30%) -- **обязателен rescoring** |
| Совместимость | Лучше всего для высокоразмерных моделей (1024+) |

### Конфигурация

```python
client.create_collection(
    collection_name="hero_archive",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
    ),
    quantization_config=models.BinaryQuantization(
        binary=models.BinaryQuantizationConfig(
            always_ram=True,
        ),
    ),
)
```

### Обязательный Rescoring

BQ без rescoring даёт неприемлемо низкий recall. Рекомендуемая настройка:

```python
results = client.query_points(
    collection_name="hero_archive",
    query=[0.1, 0.2, ...],
    search_params=models.SearchParams(
        quantization=models.QuantizationSearchParams(
            rescore=True,
            oversampling=3.0,   # 3x oversampling для BQ (больше, чем для SQ)
        ),
    ),
    limit=10,
)
```

### Когда использовать BQ

- Коллекции с 1M+ точек, где важна скорость первичного отсева
- Модели с размерностью 1024+ (OpenAI ada-002, e5-large)
- В комбинации с обязательным rescoring по float32

### Когда НЕ использовать BQ

- Низкоразмерные вектора (<256)
- Когда нет возможности хранить оригиналы для rescoring
- Модели с неравномерным распределением значений компонент

---

## 3. Product Quantization (PQ)

Вектор делится на подвекторы, каждый из которых кодируется индексом из обучаемого словаря (codebook).

### Характеристики

| Параметр | Значение |
|----------|----------|
| Сжатие памяти | До 64x |
| Ускорение поиска | Зависит от настроек |
| Потеря точности | Значительная (зависит от сжатия) |
| Обучение | Требует обучающей выборки |

### Конфигурация

```python
client.create_collection(
    collection_name="hero_deep_archive",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
    ),
    quantization_config=models.ProductQuantization(
        product=models.ProductQuantizationConfig(
            compression=models.CompressionRatio.X16,  # x4, x8, x16, x32, x64
            always_ram=True,
        ),
    ),
)
```

### Уровни сжатия

| Compression | Байт на вектор (1024d) | Потеря recall |
|-------------|----------------------|---------------|
| x4 | 1024 | Минимальная |
| x8 | 512 | Низкая |
| x16 | 256 | Средняя |
| x32 | 128 | Существенная |
| x64 | 64 | Значительная |

### Когда использовать PQ

- Архивные коллекции с миллионами точек
- RAM-ограниченные окружения
- Комбинация с rescoring для восстановления точности

---

## 4. Сравнение методов квантования

| Метод | Сжатие | Скорость | Recall без rescoring | Recall с rescoring | Сложность настройки |
|-------|--------|----------|---------------------|-------------------|-------------------|
| **Нет** | 1x | Базовая | 100% | -- | -- |
| **SQ** | 4x | 2x | ~99% | ~99.5% | Минимальная |
| **BQ** | 32x | 40x | ~70-95% | ~98% | Средняя |
| **PQ** | 4-64x | Зависит | ~80-95% | ~97% | Высокая |

### Рекомендация для "Интерпретации"

| Коллекция | Метод | Обоснование |
|-----------|-------|-------------|
| Активные воспоминания | SQ (int8) | Баланс скорости и точности |
| Архив (старые сцены) | PQ (x16) | Экономия памяти |
| Быстрый предфильтр | BQ + rescore | 40x ускорение первичного отсева |

---

## 5. Типы хранения (Storage)

### Конфигурация по уровням

| Уровень | Компонент | Хранение | Настройка |
|---------|-----------|----------|-----------|
| Векторы | Оригиналы | RAM или Disk | `on_disk` в `VectorParams` |
| Векторы | Квантованные | RAM (рекомендуемо) | `always_ram` в quantization |
| HNSW-граф | Связи | RAM или Disk | `on_disk` в `HnswConfigDiff` |
| Payload | JSON-данные | RAM или Disk | `on_disk_payload` в коллекции |

### Стратегии хранения

#### Полностью в RAM (максимальная скорость)

```python
client.create_collection(
    collection_name="active_data",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
        on_disk=False,
    ),
    on_disk_payload=False,
    hnsw_config=models.HnswConfigDiff(on_disk=False),
)
```

Потребление RAM: ~6 KB на точку (1024d float32 + payload + HNSW-связи).

#### Гибрид (квантованные в RAM, оригиналы на диске)

```python
client.create_collection(
    collection_name="balanced_data",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
        on_disk=True,           # Оригиналы на диске
    ),
    on_disk_payload=True,        # Payload на диске
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,     # Квантованные в RAM
        ),
    ),
)
```

Потребление RAM: ~1.5 KB на точку (квантованные + HNSW-связи).

#### Полностью на диске (минимальная RAM)

```python
client.create_collection(
    collection_name="archive_data",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
        on_disk=True,
    ),
    on_disk_payload=True,
    hnsw_config=models.HnswConfigDiff(on_disk=True),
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=False,   # Даже квантованные на диске (через mmap)
        ),
    ),
)
```

---

## 6. Оптимизатор (фоновые процессы)

### Конфигурация оптимизатора

```python
client.update_collection(
    collection_name="hero_memories",
    optimizer_config=models.OptimizersConfigDiff(
        indexing_threshold=20000,         # Мин. точек для HNSW
        memmap_threshold=50000,           # Мин. точек для mmap
        default_segment_number=2,         # Сегментов на шард
        max_optimization_threads=2,       # Потоков оптимизатора
        flush_interval_sec=5,             # Интервал flush WAL
    ),
)
```

### Процессы оптимизатора

1. **Merge** -- объединение мелких сегментов
2. **Index build** -- построение HNSW для sealed-сегментов
3. **Vacuum** -- очистка удалённых точек
4. **Quantization rebuild** -- перестройка квантованных индексов при обновлении данных

> **Совет:** Для batch-загрузки данных рекомендуется временно отключить индексирование (`indexing_threshold=0`), загрузить данные, затем включить обратно.
