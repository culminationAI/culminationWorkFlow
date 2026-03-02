# Qdrant: Python SDK и примеры кода

> [!TIP]
> **Версия:** qdrant-client для Qdrant v1.17.0. Все deprecated-методы заменены на актуальные.
> `recreate_collection()` -> `delete_collection()` + `create_collection()`.
> `client.search()` -> `client.query_points()`.

---

## 1. Официальные SDK

| Язык | Пакет | Установка |
|------|-------|-----------|
| **Python** | `qdrant-client` | `pip install qdrant-client` |
| **JavaScript/TypeScript** | `@qdrant/js-client-rest` | `npm install @qdrant/js-client-rest` |
| **Rust** | `qdrant-client` | `cargo add qdrant-client` |
| **Go** | `github.com/qdrant/go-client` | `go get` |
| **Java** | `io.qdrant:client` | Maven/Gradle |
| **.NET** | `Qdrant.Client` | NuGet |

---

## 2. Python: инициализация клиента

### Синхронный клиент

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Локальный инстанс
client = QdrantClient(url="http://localhost:6333")

# Qdrant Cloud
client = QdrantClient(
    url="https://your-cluster.cloud.qdrant.io:6333",
    api_key="your-api-key",
)

# gRPC (быстрее для больших объёмов)
client = QdrantClient(
    url="http://localhost:6334",
    prefer_grpc=True,
)

# In-memory (для тестов, без сервера)
client = QdrantClient(":memory:")

# Локальный файл (для тестов, без сервера)
client = QdrantClient(path="./local_qdrant_data")
```

### Асинхронный клиент

```python
from qdrant_client import AsyncQdrantClient

async_client = AsyncQdrantClient(url="http://localhost:6333")

# Все методы -- async
results = await async_client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    limit=10,
)
```

---

## 3. Полный цикл: создание коллекции, вставка, поиск

### Шаг 1: Создание коллекции

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

# ВАЖНО: recreate_collection() deprecated.
# Используйте delete + create:
if client.collection_exists("hero_memories"):
    client.delete_collection("hero_memories")

client.create_collection(
    collection_name="hero_memories",
    vectors_config={
        "semantic": models.VectorParams(
            size=1024,
            distance=models.Distance.COSINE,
        ),
    },
    sparse_vectors_config={
        "lexical": models.SparseVectorParams(),
    },
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,
        ),
    ),
)
```

### Шаг 2: Создание Payload-индексов

```python
# Keyword-индекс для мультитенантности
client.create_payload_index(
    collection_name="hero_memories",
    field_name="hero_id",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True,
    ),
)

# Integer-индекс для фильтрации по важности
client.create_payload_index(
    collection_name="hero_memories",
    field_name="importance",
    field_schema=models.PayloadSchemaType.INTEGER,
)

# Datetime-индекс для фильтрации по времени
client.create_payload_index(
    collection_name="hero_memories",
    field_name="created_at",
    field_schema=models.PayloadSchemaType.DATETIME,
)
```

### Шаг 3: Вставка данных (Upsert)

```python
import uuid
from datetime import datetime, timezone

# Предполагаем, что embedding_model -- уже настроенная модель
# (например, multilingual-e5-large)
def get_embedding(text: str) -> list[float]:
    """Получить эмбеддинг текста (1024d)."""
    # ... вызов модели ...
    pass

def get_sparse_embedding(text: str) -> models.SparseVector:
    """Получить sparse-эмбеддинг для лексического поиска."""
    # ... BM25 или SPLADE ...
    pass

# Пакетная вставка
points = []
memories = [
    {
        "text": "Первая встреча с Алисой в парке. Шёл дождь.",
        "hero_id": "hero_001",
        "type": "memory",
        "importance": 9,
        "emotion_charge": 7.5,
        "triggers": ["дождь", "парк", "Алиса"],
    },
    {
        "text": "Рабочий день в офисе. Ничего особенного.",
        "hero_id": "hero_001",
        "type": "memory",
        "importance": 2,
        "emotion_charge": 0.0,
        "triggers": [],
    },
]

for memory in memories:
    point_id = str(uuid.uuid4())
    text = memory["text"]

    points.append(
        models.PointStruct(
            id=point_id,
            vector={
                "semantic": get_embedding(text),
                "lexical": get_sparse_embedding(text),
            },
            payload={
                **memory,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    )

# Batch upsert (всегда используйте batch вместо поштучной вставки)
client.upsert(
    collection_name="hero_memories",
    points=points,
)
```

### Шаг 4: Поиск (Query API)

```python
# Семантический поиск (замена deprecated client.search())
query_text = "встреча под дождём"
query_vector = get_embedding(query_text)

results = client.query_points(
    collection_name="hero_memories",
    query=query_vector,
    using="semantic",
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="hero_id",
                match=models.MatchValue(value="hero_001"),
            ),
            models.FieldCondition(
                key="importance",
                range=models.Range(gte=5),
            ),
        ]
    ),
    search_params=models.SearchParams(
        hnsw_ef=128,
        quantization=models.QuantizationSearchParams(
            rescore=True,
            oversampling=1.5,
        ),
    ),
    limit=5,
    with_payload=True,
)

for point in results.points:
    print(f"Score: {point.score:.4f} | {point.payload['text']}")
```

### Шаг 5: Гибридный поиск (Dense + Sparse)

```python
# Fusion: семантический + лексический поиск
results = client.query_points(
    collection_name="hero_memories",
    prefetch=[
        models.Prefetch(
            query=get_embedding("встреча под дождём"),
            using="semantic",
            limit=20,
        ),
        models.Prefetch(
            query=get_sparse_embedding("встреча дождь парк"),
            using="lexical",
            limit=20,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="hero_id",
                match=models.MatchValue(value="hero_001"),
            ),
        ]
    ),
    limit=10,
)
```

### Шаг 6: Рекомендации (Recommend)

```python
# Найти воспоминания, похожие на заданные (positive),
# непохожие на другие (negative)
results = client.query_points(
    collection_name="hero_memories",
    query=models.RecommendInput(
        positive=["memory_id_001", "memory_id_005"],
        negative=["memory_id_010"],
        strategy=models.RecommendStrategy.BEST_SCORE,
    ),
    using="semantic",
    limit=5,
)
```

---

## 4. Управление данными

### Обновление Payload

```python
# Установить значение payload-поля
client.set_payload(
    collection_name="hero_memories",
    payload={"importance": 10, "reviewed": True},
    points=["point_id_001"],
)

# Перезаписать весь payload
client.overwrite_payload(
    collection_name="hero_memories",
    payload={"hero_id": "hero_001", "type": "memory", "importance": 10},
    points=["point_id_001"],
)

# Удалить поле из payload
client.delete_payload(
    collection_name="hero_memories",
    keys=["reviewed"],
    points=["point_id_001"],
)
```

### Удаление точек

```python
# По ID
client.delete(
    collection_name="hero_memories",
    points_selector=models.PointIdsList(
        points=["point_id_001", "point_id_002"],
    ),
)

# По фильтру
client.delete(
    collection_name="hero_memories",
    points_selector=models.FilterSelector(
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="importance",
                    range=models.Range(lt=2),
                ),
            ]
        ),
    ),
)
```

### Получение точек по ID

```python
points = client.get_points(
    collection_name="hero_memories",
    ids=["point_id_001", "point_id_002"],
    with_payload=True,
    with_vectors=False,
)
```

### Scroll (итерация)

```python
all_points = []
offset = None

while True:
    records, next_offset = client.scroll(
        collection_name="hero_memories",
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="hero_id",
                    match=models.MatchValue(value="hero_001"),
                ),
            ]
        ),
        limit=100,
        offset=offset,
        with_payload=True,
    )
    all_points.extend(records)
    if next_offset is None:
        break
    offset = next_offset
```

---

## 5. Информация о коллекции

```python
# Проверка существования
exists = client.collection_exists("hero_memories")

# Информация о коллекции
info = client.get_collection("hero_memories")
print(f"Точек: {info.points_count}")
print(f"Статус: {info.status}")
print(f"Конфигурация: {info.config}")

# Список коллекций
collections = client.get_collections()
for c in collections.collections:
    print(c.name)
```

---

## 6. Best Practices

### Производительность

| Рекомендация | Деталь |
|-------------|--------|
| **Batch upsert** | Всегда вставляйте пакетами (100-1000 точек) |
| **gRPC** | Используйте `prefer_grpc=True` для больших объёмов |
| **Payload-индексы** | Создавайте индексы для часто фильтруемых полей |
| **Tenant index** | `is_tenant=True` для поля разделения (hero_id) |
| **Квантование** | SQ (int8) по умолчанию -- 4x экономия при ~1% потере |

### Надёжность

| Рекомендация | Деталь |
|-------------|--------|
| **Consistency** | Для критичных записей: `ordering=WriteOrdering.STRONG` |
| **Snapshot** | Регулярные снапшоты перед массовыми операциями |
| **Collection exists** | Проверяйте `collection_exists()` перед `delete_collection()` |
| **WAL** | Не уменьшайте `flush_interval_sec` без необходимости |

### Безопасность

| Рекомендация | Деталь |
|-------------|--------|
| **API Key** | Используйте API-ключ в продакшне |
| **TLS** | Включайте TLS для удалённых подключений |
| **Network** | Ограничьте доступ к портам 6333/6334/6335 |

---

## 7. Интеграция с RAG-фреймворками

| Фреймворк | Компонент Qdrant | Примечание |
|-----------|-----------------|-----------|
| **LangChain** | `QdrantVectorStore` | Полная поддержка Query API |
| **LlamaIndex** | `QdrantVectorStore` | Поддержка гибридного поиска |
| **Haystack** | `QdrantDocumentStore` | Document-oriented API |
| **Semantic Kernel** | `QdrantMemoryStore` | .NET экосистема |
| **CrewAI** | Через LangChain adapter | Мультиагентные системы |

### Пример: LangChain + Qdrant

```python
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")

vector_store = QdrantVectorStore.from_existing_collection(
    embedding=embeddings,
    collection_name="hero_memories",
    url="http://localhost:6333",
)

# Поиск
docs = vector_store.similarity_search(
    query="воспоминание о дожде",
    k=5,
    filter={"hero_id": "hero_001"},
)
```

---

## 8. Deprecated API (миграция)

### Что заменено

| Deprecated | Актуальная замена | Версия |
|-----------|------------------|--------|
| `recreate_collection()` | `delete_collection()` + `create_collection()` | Deprecated с v1.10 |
| `client.search()` | `client.query_points()` | Deprecated с v1.10 (Query API) |
| `client.recommend()` | `client.query_points(query=RecommendInput(...))` | Deprecated с v1.10 |
| `client.discover()` | `client.query_points(query=DiscoverInput(...))` | Deprecated с v1.10 |

### Пример миграции

```python
# DEPRECATED:
# results = client.search(
#     collection_name="hero_memories",
#     query_vector=[0.1, 0.2, ...],
#     limit=5,
# )

# АКТУАЛЬНО:
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    limit=5,
)
```
