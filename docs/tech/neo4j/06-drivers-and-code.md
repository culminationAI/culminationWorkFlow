# Neo4j: Python-драйвер и интеграция

> [!TIP]
> Верифицировано 2026-02-26. Источники: Neo4j Python Driver Documentation, Neo4j Operations Manual (2026.01.x).
> Актуальная версия драйвера: `neo4j` 5.x (PyPI).

---

## 1. Установка

```bash
pip install neo4j
```

---

## 2. Подключение

### Синхронный драйвер

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

# Проверка соединения
driver.verify_connectivity()
```

### Асинхронный драйвер

```python
from neo4j import AsyncGraphDatabase

async_driver = AsyncGraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

# Проверка соединения
await async_driver.verify_connectivity()
```

**Важно:** Для async используется `AsyncGraphDatabase.driver()`, а не `GraphDatabase.driver()`. Синхронный `GraphDatabase` не поддерживает `async with`.

### Схемы URI

| URI | Описание |
|-----|----------|
| `bolt://host:7687` | Прямое соединение, один сервер |
| `neo4j://host:7687` | Маршрутизация (routing), кластер |
| `bolt+s://host:7687` | Bolt + TLS шифрование |
| `neo4j+s://host:7687` | Routing + TLS |

### Параметры подключения

```python
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password"),
    max_connection_pool_size=50,       # Размер пула (по умолчанию 100)
    connection_acquisition_timeout=60,  # Тайм-аут получения соединения (сек)
    max_transaction_retry_time=30,      # Макс. время повторов транзакции (сек)
    database="neo4j"                    # БД по умолчанию
)
```

---

## 3. Сессии и транзакции

### Жизненный цикл

```
Driver (один на приложение)
  └── Session (легковесная, короткоживущая)
        └── Transaction (атомарная единица работы)
              └── Query (один Cypher-запрос)
```

**Правила:**
- Один `Driver` на всё приложение. Не создавайте новый для каждого запроса.
- `Session` -- короткоживущая. Закрывайте после использования (context manager).
- `Transaction` -- атомарная. Либо вся проходит, либо вся откатывается.

### Transaction Functions (рекомендованный паттерн)

Transaction Functions обеспечивают автоматический retry при transient-ошибках (дедлоки, перебалансировка кластера):

```python
def get_hero_emotions(tx, hero_id):
    result = tx.run("""
        MATCH (h:Hero {id: $hero_id})-[r:ЧУВСТВУЕТ]->(e:Эмоция)
        WHERE r.интенсивность > 3
        RETURN e.название AS эмоция, r.интенсивность AS интенсивность
        ORDER BY r.интенсивность DESC
    """, hero_id=hero_id)
    return [record.data() for record in result]


def update_emotion(tx, hero_id, emotion, intensity):
    tx.run("""
        MATCH (h:Hero {id: $hero_id})
        MERGE (e:Эмоция {название: $emotion})
        MERGE (h)-[r:ЧУВСТВУЕТ]->(e)
        SET r.интенсивность = $intensity,
            r.updated_at = datetime()
    """, hero_id=hero_id, emotion=emotion, intensity=intensity)


# Использование
with driver.session(database="neo4j") as session:
    # Чтение
    emotions = session.execute_read(get_hero_emotions, "hero-1")

    # Запись
    session.execute_write(update_emotion, "hero-1", "тревога", 7)
```

### Async Transaction Functions

```python
async def get_hero_emotions(tx, hero_id):
    result = await tx.run("""
        MATCH (h:Hero {id: $hero_id})-[r:ЧУВСТВУЕТ]->(e:Эмоция)
        WHERE r.интенсивность > 3
        RETURN e.название AS эмоция, r.интенсивность AS интенсивность
        ORDER BY r.интенсивность DESC
    """, hero_id=hero_id)
    return [record.data() async for record in result]


async def main():
    async with AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "password")
    ) as driver:
        async with driver.session(database="neo4j") as session:
            emotions = await session.execute_read(
                get_hero_emotions, "hero-1"
            )
            print(emotions)
```

---

## 4. Обработка результатов

### Record API

```python
result = tx.run("MATCH (h:Hero) RETURN h.name AS name, h.age AS age")

for record in result:
    # По ключу
    name = record["name"]

    # По индексу
    name = record[0]

    # Как словарь
    data = record.data()  # {"name": "Алексей", "age": 28}

    # Все ключи
    keys = record.keys()  # ["name", "age"]
```

### Получение всех записей сразу

```python
result = tx.run("MATCH (h:Hero) RETURN h.name LIMIT 100")

# Список записей
records = list(result)

# Только значения одного поля
names = [record["h.name"] for record in result]

# Одна запись
single = result.single()  # Ошибка если 0 или >1 записей

# Первая запись (или None)
first = result.peek()
```

### Работа с узлами и связями

```python
result = tx.run("MATCH (h:Hero)-[r:ЧУВСТВУЕТ]->(e:Эмоция) RETURN h, r, e")

for record in result:
    hero = record["h"]
    rel = record["r"]
    emotion = record["e"]

    # Свойства узла
    hero_name = hero["name"]      # или hero.get("name")
    hero_labels = hero.labels     # frozenset({'Hero'})
    hero_id = hero.element_id     # строковый ID

    # Свойства связи
    intensity = rel["интенсивность"]
    rel_type = rel.type           # 'ЧУВСТВУЕТ'
    rel_id = rel.element_id

    # Начальный и конечный узлы связи
    start_id = rel.start_node.element_id
    end_id = rel.end_node.element_id
```

---

## 5. Паттерны для проекта "Интерпретация"

### Загрузка контекста героя для сцены

```python
def load_hero_context(tx, hero_id, scene_context_vector):
    """Загрузка полного контекста героя для сцены."""

    # 1. Базовые данные героя
    hero_result = tx.run("""
        MATCH (h:Hero {id: $hero_id})
        OPTIONAL MATCH (h)-[:ИМЕЕТ_ТЕЛО]->(body:Тело)
        OPTIONAL MATCH (h)-[r_role:ИГРАЕТ]->(role:Роль)
        RETURN h, body, role, r_role.расхождение AS расхождение_роли
    """, hero_id=hero_id)
    hero_data = hero_result.single().data()

    # 2. Активные эмоции (выше порога)
    emotions_result = tx.run("""
        MATCH (h:Hero {id: $hero_id})-[r:ЧУВСТВУЕТ]->(e:Эмоция)
        WHERE abs(r.интенсивность) > 2
        RETURN e.название AS эмоция,
               r.интенсивность AS интенсивность
        ORDER BY abs(r.интенсивность) DESC
        LIMIT 10
    """, hero_id=hero_id)
    emotions = [r.data() for r in emotions_result]

    # 3. Активные планы
    plans_result = tx.run("""
        MATCH (h:Hero {id: $hero_id})-[r:ИМЕЕТ_ПЛАН]->(p:План)
        WHERE p.статус = 'активный'
        RETURN p.содержание AS план,
               r.уверенность AS уверенность,
               r.мотивация AS мотивация
        ORDER BY r.мотивация DESC
    """, hero_id=hero_id)
    plans = [r.data() for r in plans_result]

    # 4. Релевантные воспоминания (векторный поиск)
    memories_result = tx.run("""
        CALL db.index.vector.queryNodes(
            'memory_embeddings', 5, $vector
        )
        YIELD node AS memory, score
        WHERE score > 0.6
        MATCH (:Hero {id: $hero_id})-[:ПОМНИТ]->(memory)
        RETURN memory.описание AS описание,
               memory.яркость AS яркость,
               score AS релевантность
        ORDER BY score DESC
    """, hero_id=hero_id, vector=scene_context_vector)
    memories = [r.data() for r in memories_result]

    return {
        "hero": hero_data,
        "emotions": emotions,
        "plans": plans,
        "memories": memories
    }


# Использование
with driver.session() as session:
    context = session.execute_read(
        load_hero_context, "hero-1", query_vector
    )
```

### Запись результатов сцены

```python
def save_scene_results(tx, scene_data):
    """Сохранение результатов сцены: Beat, изменения эмоций, новые связи."""

    # 1. Создание Beat
    tx.run("""
        MATCH (s:Сцена {номер: $scene_number})
        CREATE (b:Beat {
            описание: $description,
            timestamp: datetime(),
            значимость: $significance
        })
        CREATE (s)-[:СОДЕРЖИТ]->(b)
    """,
        scene_number=scene_data["scene_number"],
        description=scene_data["beat_description"],
        significance=scene_data["significance"]
    )

    # 2. Обновление эмоций (пакетно через UNWIND)
    if scene_data.get("emotion_changes"):
        tx.run("""
            UNWIND $changes AS change
            MATCH (h:Hero {id: $hero_id})
            MERGE (e:Эмоция {название: change.emotion})
            MERGE (h)-[r:ЧУВСТВУЕТ]->(e)
            SET r.интенсивность = change.intensity,
                r.updated_at = datetime()
        """,
            hero_id=scene_data["hero_id"],
            changes=scene_data["emotion_changes"]
        )

    # 3. Новые воспоминания
    if scene_data.get("new_memories"):
        tx.run("""
            UNWIND $memories AS mem
            MATCH (h:Hero {id: $hero_id})
            CREATE (m:Memory {
                id: randomUUID(),
                описание: mem.description,
                яркость: mem.brightness,
                заряд: mem.charge,
                дата: datetime(),
                last_access: datetime()
            })
            CREATE (h)-[:ПОМНИТ {яркость: mem.brightness}]->(m)
        """,
            hero_id=scene_data["hero_id"],
            memories=scene_data["new_memories"]
        )


# Использование
with driver.session() as session:
    session.execute_write(save_scene_results, {
        "hero_id": "hero-1",
        "scene_number": 42,
        "beat_description": "Герой встретил старого друга в кафе",
        "significance": 7,
        "emotion_changes": [
            {"emotion": "ностальгия", "intensity": 8},
            {"emotion": "радость", "intensity": 6}
        ],
        "new_memories": [
            {
                "description": "Встреча с Димой в кафе на Арбате",
                "brightness": 9,
                "charge": 7
            }
        ]
    })
```

### Пакетное затухание (cron job)

```python
async def run_decay(driver):
    """Запуск всех функций затухания. Вызывается между сценами."""

    async with driver.session() as session:
        # Затухание воспоминаний
        await session.run("""
            CALL apoc.periodic.iterate(
                "MATCH (m:Memory)
                 WHERE m.last_access IS NOT NULL
                   AND m.яркость > 0.1
                 RETURN m",
                "WITH m, duration.between(m.last_access, datetime()).days AS d
                 SET m.яркость = CASE
                   WHEN m.заряд > 7 THEN m.яркость * exp(-0.000033 * d)
                   ELSE m.яркость * exp(-0.00033 * d)
                 END",
                {batchSize: 5000, parallel: false}
            )
        """)

        # Затухание отношений без контакта
        await session.run("""
            CALL apoc.periodic.iterate(
                "MATCH (h:Hero)-[r:ОТНОСИТСЯ]->(npc:NPC)
                 WHERE r.последний_контакт IS NOT NULL
                 RETURN r",
                "WITH r, duration.between(r.последний_контакт, datetime()).days / 7.0 AS w
                 SET r.интерес = r.интерес * (1.0 - 0.02 * w),
                     r.комфорт = r.комфорт * (1.0 - 0.02 * w),
                     r.доверие = r.доверие * (1.0 - 0.005 * w)",
                {batchSize: 1000, parallel: false}
            )
        """)

        # Дрейф эмоций к нейтрали
        await session.run("""
            CALL apoc.periodic.iterate(
                "MATCH (h:Hero)-[r:ЧУВСТВУЕТ]->(e:Эмоция)
                 WHERE r.updated_at IS NOT NULL
                 RETURN r",
                "WITH r, duration.between(r.updated_at, datetime()).hours AS h
                 SET r.интенсивность = r.интенсивность * exp(-1.0 * h)",
                {batchSize: 1000, parallel: false}
            )
        """)
```

---

## 6. Конфигурация сервера (neo4j.conf)

### Основные параметры

```properties
# Аутентификация
server.security.auth_enabled=true

# Bolt listener
server.bolt.listen_address=0.0.0.0:7687

# HTTP listener (Neo4j Browser)
server.http.listen_address=0.0.0.0:7474

# Память
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1g
server.memory.pagecache.size=2g

# Transaction logs
db.tx_log.rotation.retention_policy=2 days
db.tx_log.rotation.size=256m

# APOC
dbms.security.procedures.unrestricted=apoc.*,gds.*
dbms.security.procedures.allowlist=apoc.*,gds.*
```

**Deprecated конфигурация:**

| Deprecated | Актуально |
|-----------|-----------|
| `dbms.tx_log.rotation.retention_policy` | `db.tx_log.rotation.retention_policy` |
| `dbms.security.auth_enabled` | `server.security.auth_enabled` |
| `dbms.default_listen_address` | `server.default_listen_address` |
| `dbms.connector.bolt.listen_address` | `server.bolt.listen_address` |

---

## 7. OGM (Object Graph Mappers)

Для сложных приложений можно использовать OGM-библиотеки:

| Библиотека | Язык | Описание |
|-----------|------|----------|
| `neomodel` | Python | Декларативные модели, валидация, миграции |
| `neode` | Node.js | OGM для JavaScript |
| Spring Data Neo4j | Java | Стандарт для Spring-экосистемы |

**Для проекта:** рекомендуется использовать чистый драйвер `neo4j` без OGM -- более точный контроль запросов и производительности.

---

## 8. Чек-лист интеграции

| Проверка | Статус |
|----------|--------|
| Один Driver на приложение | |
| Async для asyncio-приложений (AsyncGraphDatabase) | |
| Transaction Functions для retry | |
| Параметризация всех запросов ($param) | |
| Закрытие сессий через context manager | |
| driver.close() при завершении | |
| URI: `neo4j://` для кластера, `bolt://` для одного сервера | |
