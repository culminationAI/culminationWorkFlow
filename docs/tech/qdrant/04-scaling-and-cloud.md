# Qdrant: Масштабирование, кластер и мультитенантность

> [!TIP]
> **Версия:** Qdrant v1.17.0 (февраль 2026). Разделы по шардированию, репликации и мультитенантности верифицированы.

---

## 1. Распределённая архитектура

Qdrant поддерживает распределённый режим: несколько узлов образуют кластер через протокол **Raft** для консенсуса.

### Компоненты кластера

| Компонент | Описание |
|-----------|----------|
| **Node** | Экземпляр Qdrant с собственным хранилищем |
| **Shard** | Горизонтальная часть коллекции (часть данных) |
| **Replica** | Копия шарда на другом узле (отказоустойчивость) |

### Запуск кластера

```bash
# Первый узел (bootstrap)
docker run -p 6333:6333 -p 6334:6334 -p 6335:6335 \
  qdrant/qdrant:v1.17.0 \
  --cluster --bootstrap http://node1:6335

# Последующие узлы
docker run -p 6333:6333 -p 6334:6334 -p 6335:6335 \
  qdrant/qdrant:v1.17.0 \
  --cluster --bootstrap http://node1:6335
```

Порты:
- `6333` -- REST API
- `6334` -- gRPC API
- `6335` -- Internal cluster communication (Raft)

---

## 2. Шардирование (Sharding)

### Автоматическое шардирование

При создании коллекции задаётся число шардов:

```python
client.create_collection(
    collection_name="hero_memories",
    vectors_config=models.VectorParams(
        size=1024,
        distance=models.Distance.COSINE,
    ),
    shard_number=4,            # Распределить по 4 шардам
    replication_factor=2,      # 2 копии каждого шарда
)
```

### Динамический реширдинг

Qdrant поддерживает изменение числа шардов без остановки:

```bash
# Добавить шарды к существующей коллекции (REST API)
POST /collections/hero_memories/cluster
{
    "move_shard": {
        "shard_id": 0,
        "from_peer_id": 1,
        "to_peer_id": 2
    }
}
```

### Custom Sharding

Позволяет размещать данные на конкретных шардах (привязка по shard_key):

```python
# Создание коллекции с custom sharding
client.create_collection(
    collection_name="hero_memories",
    vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
    sharding_method=models.ShardingMethod.CUSTOM,
)

# Создание shard key
client.create_shard_key(
    collection_name="hero_memories",
    shard_key="hero_001",
    shards_number=1,
    replication_factor=1,
)

# Upsert с привязкой к shard_key
client.upsert(
    collection_name="hero_memories",
    points=[...],
    shard_key_selector="hero_001",
)

# Поиск только по конкретному шарду
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    shard_key_selector="hero_001",
    limit=10,
)
```

---

## 3. Репликация

### Consistency levels

| Уровень | Описание | Когда |
|---------|----------|-------|
| `1` (или не указан) | Запрос к одной реплике | Максимальная скорость |
| `majority` | Большинство реплик подтвердили | Баланс скорости и надёжности |
| `quorum` | Более половины реплик | Строгая консистентность |
| `all` | Все реплики подтвердили | Максимальная надёжность |

```python
# Запись с гарантией consistency
client.upsert(
    collection_name="hero_memories",
    points=[...],
    ordering=models.WriteOrdering.STRONG,  # ждёт подтверждения от всех реплик
)
```

---

## 4. Мультитенантность

### Стратегии

#### 1. Одна коллекция + Payload-фильтр (рекомендуемый)

Самый простой и масштабируемый подход. Все герои в одной коллекции, разделение через фильтр:

```python
# Создать tenant-индекс для hero_id
client.create_payload_index(
    collection_name="hero_memories",
    field_name="hero_id",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True,
    ),
)

# Поиск по конкретному герою
results = client.query_points(
    collection_name="hero_memories",
    query=[0.1, 0.2, ...],
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="hero_id",
                match=models.MatchValue(value="hero_001"),
            )
        ]
    ),
    limit=10,
)
```

**Плюсы:** один индекс, простое управление, горизонтальное масштабирование.
**Минусы:** данные разных тенантов физически рядом, нет изоляции.

#### 2. Custom Sharding по тенанту

Каждый тенант -- свой shard_key. Физическая изоляция данных:

```python
# Каждый герой = отдельный shard key
client.create_shard_key(
    collection_name="hero_memories",
    shard_key="hero_001",
)
```

**Плюсы:** физическая изоляция, поиск только по нужному шарду.
**Минусы:** накладные расходы на управление шардами.

#### 3. Отдельная коллекция на тенанта

```python
client.create_collection(
    collection_name=f"memories_{hero_id}",
    vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
)
```

**Плюсы:** полная изоляция, независимые настройки.
**Минусы:** накладные расходы на индексы, дескрипторы, оптимизатор для каждой коллекции.

### Рекомендация для "Интерпретации"

**MVP:** одна коллекция + payload-фильтр по `hero_id` (подход 1).
**Scale:** custom sharding по `hero_id` (подход 2) при росте до 100+ героев.

---

## 5. Снапшоты и бэкапы

### Создание снапшота

```bash
# Снапшот одной коллекции
POST /collections/hero_memories/snapshots

# Снапшот всей инстанции
POST /snapshots
```

```python
# Python SDK
client.create_snapshot(collection_name="hero_memories")
```

### Восстановление из снапшота

```bash
# Загрузить снапшот в коллекцию
PUT /collections/hero_memories/snapshots/upload
Content-Type: multipart/form-data
```

### Свойства снапшотов

- Создаются **без блокировки** записи
- Переносимы между инстансами Qdrant
- Содержат все данные коллекции: точки, индексы, конфигурацию
- Совместимы между minor-версиями Qdrant

---

## 6. Qdrant Cloud

Managed-сервис от Qdrant:

| Функция | Описание |
|---------|----------|
| **Auto-scaling** | Автоматическое масштабирование узлов |
| **Managed backups** | Автоматические снапшоты |
| **Cloud Inference** | Встроенная векторизация (отправляешь текст -- получаешь результат) |
| **Monitoring** | Встроенные дашборды |

### Cloud Inference

Позволяет отправлять текст напрямую в Qdrant -- база сама вызывает модель эмбеддингов:

```python
# Пример (Qdrant Cloud с Server-Side Inference)
results = client.query_points(
    collection_name="hero_memories",
    query="воспоминание о первой встрече",  # Текст вместо вектора
    limit=5,
)
```

> **Примечание:** Cloud Inference доступен только в Qdrant Cloud. Для self-hosted -- генерация эмбеддингов на стороне приложения.
