# Qdrant: Основные концепции

> [!TIP]
> **Версия:** Qdrant v1.17.0 (февраль 2026). Верифицировано через официальную документацию.

---

## 1. Точки (Points)

Точка (Point) -- атомарная единица данных в Qdrant. Каждая точка содержит три компонента:

### Структура точки

| Компонент | Описание | Тип |
|-----------|----------|-----|
| **ID** | Уникальный идентификатор | `UUID` или `unsigned 64-bit integer` |
| **Vector(s)** | Один или несколько именованных векторов | `float32[]`, `float16[]`, `uint8[]` |
| **Payload** | Произвольные метаданные | JSON-объект |

### Множественные векторы (Named Vectors)

Одна точка может хранить несколько именованных векторов разной размерности. Применение:

- `semantic` -- эмбеддинг смысла текста (multilingual-e5-large, 1024d)
- `header` -- эмбеддинг заголовка (384d)
- `image` -- эмбеддинг изображения (512d)

```python
# Пример: точка с несколькими именованными векторами
models.PointStruct(
    id="550e8400-e29b-41d4-a716-446655440000",
    vector={
        "semantic": [0.1, 0.2, ...],  # 1024d
        "header": [0.3, 0.4, ...],     # 384d
    },
    payload={
        "hero_id": "hero_001",
        "type": "memory",
        "importance": 8
    }
)
```

### Sparse Vectors

Помимо плотных (dense) векторов, Qdrant поддерживает разреженные (sparse) векторы для гибридного поиска:

```python
models.SparseVector(
    indices=[10, 42, 1337],
    values=[0.5, 0.3, 0.8]
)
```

Sparse-векторы используются для BM25-подобного лексического поиска в комбинации с dense-векторами для семантического.

---

## 2. Коллекции (Collections)

Коллекция -- контейнер для точек с единой конфигурацией векторов.

### Параметры создания коллекции

| Параметр | Описание | Значения |
|----------|----------|----------|
| `vectors_config` | Конфигурация векторов | `VectorParams` или `dict` именованных векторов |
| `sparse_vectors_config` | Конфигурация sparse-векторов | `SparseVectorParams` |
| `shard_number` | Количество шардов | По умолчанию: 1 |
| `replication_factor` | Фактор репликации | По умолчанию: 1 |
| `on_disk_payload` | Payload на диске (экономия RAM) | `true` / `false` |

### Метрики расстояния

| Метрика | Формула | Когда использовать |
|---------|---------|-------------------|
| **Cosine** | 1 - cos(a, b) | Нормализованные эмбеддинги (e5-large, OpenAI) |
| **Dot** | -dot(a, b) | Когда длина вектора значима |
| **Euclid** | L2(a, b) | Геометрические данные, координаты |
| **Manhattan** | L1(a, b) | Дискретные / разреженные данные |

**Для проекта "Интерпретация":** используем `Cosine` -- стандарт для multilingual-e5-large.

### Создание коллекции (актуальный API v1.17)

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

# Создание коллекции с dense + sparse векторами
client.create_collection(
    collection_name="hero_memories",
    vectors_config={
        "semantic": models.VectorParams(
            size=1024,
            distance=models.Distance.COSINE,
            on_disk=True,
        ),
    },
    sparse_vectors_config={
        "lexical": models.SparseVectorParams(),
    },
)
```

> **Важно:** Метод `recreate_collection()` deprecated с v1.10. Используйте `delete_collection()` + `create_collection()`.

---

## 3. Типы данных Payload и индексация

### Поддерживаемые типы

| Тип | Назначение | Доступные операции |
|-----|------------|-------------------|
| **Keyword** | Метки, категории, ID | Exact match, TextAny (v1.17) |
| **Text** | Описания, полнотекстовый поиск | Full-text search (токенизация) |
| **Integer** | Счётчики, версии, количества | Range, Match |
| **Float** | Веса, координаты, коэффициенты | Range |
| **Bool** | Флаги | Match |
| **Geo** | Геолокация (lat, lon) | Geo bounding box, Radius |
| **Datetime** | Метки времени | Range, Period |
| **UUID** | Уникальные идентификаторы | Exact match |

### Создание Payload-индекса

```python
client.create_payload_index(
    collection_name="hero_memories",
    field_name="hero_id",
    field_schema=models.PayloadSchemaType.KEYWORD,
)

client.create_payload_index(
    collection_name="hero_memories",
    field_name="importance",
    field_schema=models.PayloadSchemaType.INTEGER,
)
```

### Полнотекстовая индексация

```python
client.create_payload_index(
    collection_name="hero_memories",
    field_name="description",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        min_token_len=2,
        max_token_len=20,
        lowercase=True,
    ),
)
```

Поддерживаемые токенизаторы:
- `word` -- разбиение по пробелам и знакам пунктуации
- `multilingual` -- поддержка языков без явных границ слов (CJK)
- `prefix` -- префиксная токенизация для автодополнения

---

## 4. Сегменты и оптимизация

Внутри каждого шарда данные организованы в **сегменты**:

- **Appendable segment** -- принимает новые данные, не индексирован HNSW
- **Sealed segment** -- закрытый, с построенным HNSW-индексом, оптимальный для поиска

Фоновый оптимизатор Qdrant периодически:
1. Объединяет мелкие сегменты в крупные (merge)
2. Строит HNSW-индексы для sealed-сегментов
3. Выполняет vacuuming -- освобождение места от удалённых точек

### Пороги оптимизатора

```json
{
  "optimizer_config": {
    "indexing_threshold": 20000,
    "memmap_threshold": 50000,
    "flush_interval_sec": 5,
    "max_optimization_threads": 2
  }
}
```

| Параметр | Описание | По умолчанию |
|----------|----------|-------------|
| `indexing_threshold` | Мин. число точек для построения HNSW | 20000 |
| `memmap_threshold` | Мин. число точек для перехода на mmap | 50000 |
| `flush_interval_sec` | Интервал сброса WAL на диск | 5 |
| `max_optimization_threads` | Макс. потоков оптимизации | 1 |

---

## 5. Write-Ahead Log (WAL)

WAL обеспечивает сохранность данных при сбоях:

- Каждая операция записи сначала попадает в WAL
- Периодически WAL сбрасывается на диск (flush)
- При перезапуске -- восстановление из WAL

---

## 6. Типы хранения (Storage)

| Тип | Описание | Когда использовать |
|-----|----------|-------------------|
| **In-Memory** | Все данные в RAM | Максимальная скорость, малые коллекции |
| **Mmap** | Данные на диске, OS кеширует в RAM | Коллекции больше RAM |
| **On-Disk** | Векторы и индекс на диске | Экономия RAM, большие архивы |

Настройка хранения при создании коллекции:

```python
client.create_collection(
    collection_name="archive_memories",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
        on_disk=True,  # Векторы на диске
    ),
    on_disk_payload=True,  # Payload на диске
    hnsw_config=models.HnswConfigDiff(
        on_disk=True,  # HNSW-индекс на диске
    ),
)
```
