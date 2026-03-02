# Qdrant: Поиск, фильтрация и Query API

> [!TIP]
> **Версия:** Qdrant v1.17.0 (февраль 2026). Query API -- единая точка входа для всех типов поиска.

---

## 1. Query API (универсальный поиск)

Начиная с v1.10, Qdrant предоставляет единый метод `query_points()` для всех типов запросов. Это заменяет отдельные deprecated-методы (`search`, `recommend`, `discover`).

### Типы запросов через Query API

| Тип | Описание | Параметр `query` |
|-----|----------|-----------------|
| **Nearest** | Поиск ближайших по вектору | Вектор (список float) или ID точки |
| **Recommend** | Поиск похожих на positive, непохожих на negative | `RecommendInput(positive=[], negative=[])` |
| **Discover** | Поиск с контекстными парами (target + context) | `DiscoverInput(target=, context=[])` |
| **Context** | Поиск по набору контекстных пар | `ContextInput(pairs=[])` |
| **Fusion** | Объединение результатов нескольких запросов | Используется в `query_points` с `prefetch` |
| **Order By** | Сортировка по payload-полю (без вектора) | `OrderByInput(key=, direction=)` |

### Пример: семантический поиск

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

# Поиск ближайших точек (замена deprecated client.search())
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, 0.3, ...],  # вектор запроса
    limit=10,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="hero_id",
                match=models.MatchValue(value="hero_001"),
            )
        ]
    ),
    with_payload=True,
    with_vectors=False,
)

for point in results.points:
    print(f"ID: {point.id}, Score: {point.score}")
    print(f"Payload: {point.payload}")
```

> **Важно:** Метод `client.search()` deprecated. Используйте `client.query_points()`.

### Пример: рекомендации

```python
# Найти воспоминания, похожие на конкретные (positive),
# и непохожие на другие (negative)
results = client.query_points(
    collection_name="hero_memories",
    query=models.RecommendInput(
        positive=["memory_001", "memory_005"],   # ID похожих
        negative=["memory_010"],                  # ID непохожих
    ),
    using="semantic",  # имя вектора
    limit=5,
)
```

### Пример: Discover (поиск с контекстом)

```python
# Discover: ищет точки, близкие к target,
# с учётом контекстных пар (positive/negative)
results = client.query_points(
    collection_name="hero_memories",
    query=models.DiscoverInput(
        target="memory_001",
        context=[
            models.ContextPair(
                positive="memory_005",
                negative="memory_010",
            )
        ],
    ),
    limit=5,
)
```

---

## 2. Гибридный поиск (Dense + Sparse)

Гибридный поиск объединяет семантический (dense) и лексический (sparse) поиск через механизм `prefetch` + fusion.

### Reciprocal Rank Fusion (RRF)

RRF объединяет результаты нескольких поисков по формуле:

```
score(d) = SUM(1 / (k + rank_i(d)))
```

где `k` -- параметр сглаживания (по умолчанию 60).

### Параметризованный RRF (v1.17)

В v1.17.0 добавлена возможность задать **вес** каждого prefetch-запроса в RRF:

```python
results = client.query_points(
    collection_name="hero_memories",
    prefetch=[
        # Семантический поиск (dense)
        models.Prefetch(
            query=[0.1, 0.2, ...],
            using="semantic",
            limit=20,
        ),
        # Лексический поиск (sparse)
        models.Prefetch(
            query=models.SparseVector(
                indices=[10, 42, 1337],
                values=[0.5, 0.3, 0.8],
            ),
            using="lexical",
            limit=20,
        ),
    ],
    query=models.FusionQuery(
        fusion=models.Fusion.RRF,
    ),
    limit=10,
)
```

---

## 3. Фильтрация

### Логические операторы

| Оператор | Описание |
|----------|----------|
| `must` | Все условия должны выполняться (AND) |
| `should` | Хотя бы одно условие (OR) |
| `must_not` | Ни одно условие не должно выполняться (NOT) |
| `min_should` | Минимум N из условий `should` |

### Типы условий фильтрации

```python
# Exact match (keyword)
models.FieldCondition(
    key="type",
    match=models.MatchValue(value="memory"),
)

# TextAny (v1.17): match любому из списка значений
models.FieldCondition(
    key="tags",
    match=models.MatchAny(any=["important", "emotional", "trigger"]),
)

# Range (integer/float)
models.FieldCondition(
    key="importance",
    range=models.Range(gte=7, lte=10),
)

# Datetime range
models.FieldCondition(
    key="created_at",
    range=models.DatetimeRange(
        gte="2026-01-01T00:00:00Z",
        lt="2026-03-01T00:00:00Z",
    ),
)

# Geo bounding box
models.FieldCondition(
    key="location",
    geo_bounding_box=models.GeoBoundingBox(
        top_left=models.GeoPoint(lat=55.8, lon=37.4),
        bottom_right=models.GeoPoint(lat=55.6, lon=37.8),
    ),
)

# Nested filter (вложенные объекты в payload)
models.NestedCondition(
    nested=models.Nested(
        key="emotions",
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="name",
                    match=models.MatchValue(value="sadness"),
                ),
                models.FieldCondition(
                    key="intensity",
                    range=models.Range(gte=5),
                ),
            ]
        ),
    ),
)

# Has ID (поиск по конкретным ID)
models.HasIdCondition(
    has_id=["id_001", "id_002", "id_003"],
)

# Is Empty / Is Null
models.IsEmptyCondition(is_empty=models.PayloadField(key="description"))
models.IsNullCondition(is_null=models.PayloadField(key="deleted_at"))
```

### Стратегия фильтрации (планировщик)

Qdrant автоматически выбирает стратегию:

1. **Строгий фильтр** (мало точек проходит) -- сначала фильтрация, потом поиск по вектору среди отфильтрованных
2. **Мягкий фильтр** -- обход HNSW-графа с проверкой условий payload "на лету"
3. **Средний** -- комбинированная стратегия с адаптивным порогом

---

## 4. Relevance Feedback (v1.17)

Полноценная фича в v1.17.0. Позволяет передавать в запрос примеры релевантных и нерелевантных результатов, чтобы поисковик корректировал ранжирование.

**Механизм:** передача `positive` и `negative` примеров (ID точек) в запрос Recommend или Discover. Qdrant вычисляет скорректированный вектор запроса, учитывая направления к positive и от negative.

Это **не "самообучение в сессии"** (как описывалось ранее), а передача явных сигналов в каждом запросе:

```python
# Relevance Feedback через Recommend
results = client.query_points(
    collection_name="hero_memories",
    query=models.RecommendInput(
        positive=["relevant_memory_1", "relevant_memory_2"],
        negative=["irrelevant_memory_1"],
        strategy=models.RecommendStrategy.BEST_SCORE,
    ),
    limit=10,
)
```

**Стратегии:**
- `AVERAGE_VECTOR` -- усреднение positive/negative в один вектор (по умолчанию)
- `BEST_SCORE` -- максимум из scores к каждому positive минус максимум к negative

---

## 5. Группировка результатов (Search Groups)

Предотвращает ситуацию, когда топ-N -- чанки одного документа:

```python
results = client.query_points_groups(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    group_by="document_id",
    group_size=2,     # результатов из каждой группы
    limit=5,          # групп
)
```

---

## 6. Scroll (итерация по коллекции)

Для перебора всех точек без векторного поиска:

```python
records, next_offset = client.scroll(
    collection_name="hero_memories",
    scroll_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="hero_id",
                match=models.MatchValue(value="hero_001"),
            )
        ]
    ),
    limit=100,
    offset=None,  # или предыдущий next_offset
    with_payload=True,
    with_vectors=False,
)
```

---

## 7. Count (подсчёт точек)

```python
count = client.count(
    collection_name="hero_memories",
    count_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="type",
                match=models.MatchValue(value="emotion"),
            )
        ]
    ),
    exact=True,  # точный подсчёт (медленнее)
)
print(f"Эмоциональных воспоминаний: {count.count}")
```
