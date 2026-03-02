# Qdrant: Оптимизация и производительность

> [!TIP]
> **Версия:** Qdrant v1.17.0 (февраль 2026). Параметры HNSW и квантования верифицированы.

---

## 1. HNSW-индекс (Hierarchical Navigable Small World)

Основной индекс для приближённого поиска ближайших соседей (ANN). Многослойный граф, где верхние слои обеспечивают быструю навигацию, нижние -- точность.

### Параметры конфигурации

| Параметр | Описание | Диапазон | По умолчанию |
|----------|----------|----------|-------------|
| `m` | Макс. число связей на узел | 4-64 | 16 |
| `ef_construct` | Размер списка кандидатов при построении | 4-1000 | 100 |
| `full_scan_threshold` | Порог перехода на полный перебор | 1-100000 | 10000 |
| `on_disk` | Хранение графа на диске | true/false | false |

### Влияние параметров на производительность

| Параметр | Увеличение | Скорость поиска | Точность (Recall) | Память | Скорость индексации |
|----------|-----------|----------------|-------------------|--------|-------------------|
| `m` | 16 -> 32 | Без изменений / немного медленнее | Выше | x2 | Медленнее |
| `m` | 16 -> 64 | Медленнее | Значительно выше | x4 | Значительно медленнее |
| `ef_construct` | 100 -> 300 | Без изменений | Выше | Без изменений | Медленнее |
| `ef_construct` | 100 -> 500 | Без изменений | Ещё выше | Без изменений | Значительно медленнее |

### Рекомендации по настройке

**Для проекта "Интерпретация" (100K-1M точек):**
```python
hnsw_config = models.HnswConfigDiff(
    m=16,                    # Стандарт -- хороший баланс
    ef_construct=128,        # Чуть выше дефолта для лучшего recall
    full_scan_threshold=10000,
    on_disk=False,           # В RAM для скорости
)
```

**Для архивных коллекций (1M+ точек):**
```python
hnsw_config = models.HnswConfigDiff(
    m=32,                    # Выше точность
    ef_construct=200,        # Качественный граф
    on_disk=True,            # Экономия RAM
)
```

### `ef` при запросе (Search Accuracy)

Параметр `ef` задаётся при каждом запросе и контролирует баланс скорость/точность:

```python
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    search_params=models.SearchParams(
        hnsw_ef=128,         # Больше = точнее, но медленнее
        exact=False,         # True = brute-force (точный, но медленный)
    ),
    limit=10,
)
```

| `hnsw_ef` | Recall | Latency |
|-----------|--------|---------|
| 64 | ~95% | Быстро |
| 128 | ~98% | Средне |
| 256 | ~99.5% | Медленно |
| 512 | ~99.9% | Очень медленно |

### ACORN (v1.17)

Новый алгоритм обхода HNSW-графа, оптимизированный для запросов с фильтрами. Стандартный HNSW плохо работает, когда фильтр отсекает большую часть точек. ACORN адаптирует стратегию обхода с учётом фильтра, значительно улучшая recall при жёстких фильтрах.

---

## 2. Квантование (обзор)

Подробнее о каждом типе -- в `05-quantization-and-storage.md`. Здесь -- краткое сравнение.

| Тип | Сжатие | Скорость | Потеря точности | Когда использовать |
|-----|--------|----------|----------------|-------------------|
| **Scalar (SQ)** | 4x | 2x | ~1% | По умолчанию для большинства случаев |
| **Binary (BQ)** | 32x | 40x | 5-30% (нужен rescore) | Высокоразмерные векторы (1024+) |
| **Product (PQ)** | 64x | Зависит от настроек | Значительная | Архивы, ограниченная RAM |

### Быстрое включение SQ

```python
client.update_collection(
    collection_name="hero_memories",
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,
        ),
    ),
)
```

---

## 3. Payload-индексы

### Типы и применение

| Тип индекса | Payload-тип | Операции |
|-------------|-------------|----------|
| Keyword index | keyword, uuid | Match, MatchAny, MatchExcept |
| Integer index | integer | Range, Match |
| Float index | float | Range |
| Bool index | bool | Match |
| Geo index | geo | Bounding box, Radius |
| Datetime index | datetime | Range |
| Text index | text | Full-text search |

### Tenant-индекс (оптимизация мультитенантности)

Для полей, по которым идёт фильтрация в каждом запросе (например, `hero_id`), рекомендуется создать **tenant index**:

```python
client.create_payload_index(
    collection_name="hero_memories",
    field_name="hero_id",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True,  # Оптимизация для мультитенантности
    ),
)
```

---

## 4. Управление ресурсами

### Memory-mapped storage (mmap)

Qdrant использует `mmap` для работы с данными, превышающими RAM.

**Linux:** обязательная настройка:
```bash
# Увеличить лимит mmap
sudo sysctl -w vm.max_map_count=1048576
# Для постоянного применения:
echo "vm.max_map_count=1048576" | sudo tee -a /etc/sysctl.conf
```

### Многопоточный поиск

```python
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    search_params=models.SearchParams(
        hnsw_ef=128,
    ),
    limit=10,
    # Qdrant автоматически параллелит поиск по сегментам
)
```

### WAL (Write-Ahead Log) настройка

```yaml
# config.yaml
storage:
  wal:
    wal_capacity_mb: 32      # Размер WAL-файла
    wal_segments_ahead: 0    # Предзаполнение сегментов
```

---

## 5. Бенчмарки и мониторинг

### Метрики через Prometheus

Qdrant экспортирует метрики на порт `:6333/metrics`:

- `qdrant_grpc_responses_total` -- количество gRPC-ответов
- `qdrant_rest_responses_total` -- количество REST-ответов
- `qdrant_search_latency_seconds` -- латентность поиска
- `qdrant_upsert_latency_seconds` -- латентность вставки

### Telemetry API

```bash
curl http://localhost:6333/telemetry
```

Возвращает информацию о коллекциях, индексах, использовании памяти и производительности.

---

## 6. Практические рекомендации

### Для проекта "Интерпретация"

| Аспект | Рекомендация |
|--------|-------------|
| **Размерность** | 1024 (multilingual-e5-large) |
| **Метрика** | Cosine (e5 нормализует векторы) |
| **HNSW m** | 16 (стандарт, достаточно для 100K-1M) |
| **HNSW ef_construct** | 128 |
| **Квантование** | SQ (int8) -- 4x сжатие при минимальной потере |
| **Payload на диске** | Да, для экономии RAM |
| **Фильтрация** | Keyword-индекс на `hero_id` (tenant), Integer на `importance` |
