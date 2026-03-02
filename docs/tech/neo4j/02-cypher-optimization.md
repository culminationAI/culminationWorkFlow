# Neo4j: Оптимизация Cypher-запросов

> [!TIP]
> Верифицировано 2026-02-26. Источники: Neo4j Cypher Manual (Cypher 25), Neo4j Operations Manual (2026.01.x).

---

## 1. Анализ запросов: EXPLAIN и PROFILE

### EXPLAIN

Показывает план выполнения **без выполнения** запроса. Используется для проверки, какие индексы задействованы.

```cypher
EXPLAIN
MATCH (h:Hero)-[:ЧУВСТВУЕТ]->(e:Эмоция)
WHERE h.id = $heroId
RETURN e.название, e.интенсивность
```

Ключевые операторы в плане:
- `NodeByLabelScan` -- полный скан по метке (плохо для больших графов)
- `NodeIndexSeek` -- использование индекса (хорошо)
- `NodeUniqueIndexSeek` -- поиск по уникальному индексу (оптимально)
- `Expand(All)` -- обход связей
- `Filter` -- фильтрация после получения данных (может указывать на отсутствие индекса)

### PROFILE

Выполняет запрос и показывает **реальную** статистику: количество обращений к хранилищу (db hits), число строк на каждом шаге.

```cypher
PROFILE
MATCH (h:Hero {id: $heroId})-[:ПОМНИТ]->(m:Memory)
WHERE m.яркость > 5
RETURN m.описание, m.яркость
ORDER BY m.яркость DESC
LIMIT 10
```

**Цель оптимизации:** минимизировать `db hits` и количество промежуточных строк (`rows`).

---

## 2. Параметризация запросов

Параметризация обязательна. Это позволяет Neo4j кэшировать план выполнения (Query Plan Cache) и переиспользовать его.

```cypher
-- ПЛОХО: конкатенация строк, план не кэшируется
MATCH (h:Hero {name: 'Алексей'}) RETURN h

-- ХОРОШО: параметр, план кэшируется
MATCH (h:Hero {name: $name}) RETURN h
```

---

## 3. Hint-ы планировщика

Если Cost-Based Optimizer (CBO) выбирает неоптимальный план, можно подсказать:

```cypher
MATCH (h:Hero {id: $heroId})
USING INDEX h:Hero(id)
RETURN h
```

**Осторожно:** hint-ы привязывают к конкретной стратегии. При изменении данных hint может стать контрпродуктивным. Используйте только после PROFILE.

---

## 4. Пакетная обработка (Batching)

### UNWIND для массовых операций

Вместо 1000 отдельных транзакций -- одна с массивом параметров:

```cypher
UNWIND $emotions AS emotion
MATCH (h:Hero {id: $heroId})
MERGE (e:Эмоция {название: emotion.название})
MERGE (h)-[r:ЧУВСТВУЕТ]->(e)
SET r.интенсивность = emotion.интенсивность,
    r.updated_at = datetime()
```

### apoc.periodic.iterate для миллионов узлов

```cypher
CALL apoc.periodic.iterate(
  "MATCH (m:Memory) WHERE m.яркость < 0.1 RETURN m",
  "DETACH DELETE m",
  {batchSize: 10000, parallel: false}
)
```

**Параметры:**
- `batchSize` -- размер пакета (10000 -- хороший дефолт)
- `parallel` -- параллельное выполнение пакетов. **Осторожно:** `true` безопасно только когда пакеты не модифицируют одни и те же узлы

---

## 5. Оптимизация обходов графа

### Ограничение глубины

```cypher
-- ПЛОХО: неограниченная глубина, может обойти весь граф
MATCH path = (h:Hero)-[*]-(target)

-- ХОРОШО: явное ограничение
MATCH path = (h:Hero)-[*1..3]-(target)
```

### Фильтрация по типу связи

```cypher
-- МЕДЛЕННО: проверка всех типов связей
MATCH (h:Hero)-[r]-(n) WHERE type(r) = 'ПОМНИТ'

-- БЫСТРО: явное указание типа
MATCH (h:Hero)-[:ПОМНИТ]->(m:Memory)
```

### Направленность связей

Указание направления ускоряет обход в 2 раза, так как Neo4j проверяет только исходящие/входящие, а не обе стороны:

```cypher
-- МЕДЛЕННЕЕ: проверяет оба направления
MATCH (h:Hero)-[:ЗНАЕТ]-(npc:NPC)

-- БЫСТРЕЕ: конкретное направление
MATCH (h:Hero)-[:ЗНАЕТ]->(npc:NPC)
```

---

## 6. Оптимизация WHERE

### Раннее сужение выборки

```cypher
-- ПЛОХО: сначала обход, потом фильтрация
MATCH (h:Hero)-[:ЧУВСТВУЕТ]->(e:Эмоция)-[:СВЯЗАНО_С]->(m:Memory)
WHERE h.id = $heroId AND e.интенсивность > 5

-- ХОРОШО: фильтрация в паттерне, раннее сужение
MATCH (h:Hero {id: $heroId})-[:ЧУВСТВУЕТ]->(e:Эмоция)
WHERE e.интенсивность > 5
MATCH (e)-[:СВЯЗАНО_С]->(m:Memory)
RETURN m
```

### IS NOT NULL вместо exists()

```cypher
-- DEPRECATED:
-- WHERE exists(n.embedding)

-- АКТУАЛЬНО (Cypher 25):
WHERE n.embedding IS NOT NULL
```

---

## 7. Настройка памяти

### Конфигурация (neo4j.conf)

```properties
# JVM Heap -- для выполнения запросов и транзакций
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1g

# Page Cache -- кэш данных с диска
# Рекомендуется: до 50% доступной RAM (но не больше размера данных на диске)
server.memory.pagecache.size=2g

# Transaction logs -- ротация и хранение
db.tx_log.rotation.retention_policy=2 days
db.tx_log.rotation.size=256m
```

**Важно:** Конфигурация `dbms.tx_log.*` -- deprecated. Используйте `db.tx_log.*`.

### Диагностика

```cypher
-- Статистика использования памяти
CALL dbms.listConfig()
YIELD name, value
WHERE name CONTAINS 'memory'
RETURN name, value
```

---

## 8. Транзакции и блокировки

### Write Locks

Neo4j блокирует узлы и связи при записи. Два параллельных запроса, обновляющих одни и те же узлы в разном порядке, могут создать дедлок.

**Решение -- сортировка ID перед обновлением:**

```cypher
UNWIND $updates AS update
WITH update ORDER BY update.nodeId
MATCH (n) WHERE elementId(n) = update.nodeId
SET n.value = update.value
```

### Transaction Functions (рекомендованный паттерн)

Transaction Functions обеспечивают автоматический retry при transient-ошибках (дедлоки, сетевые проблемы):

```python
def update_emotion(tx, hero_id, emotion, intensity):
    tx.run("""
        MATCH (h:Hero {id: $hero_id})
        MERGE (e:Эмоция {название: $emotion})
        MERGE (h)-[r:ЧУВСТВУЕТ]->(e)
        SET r.интенсивность = $intensity,
            r.updated_at = datetime()
    """, hero_id=hero_id, emotion=emotion, intensity=intensity)

with driver.session() as session:
    session.execute_write(update_emotion, "hero-1", "тревога", 7)
```

---

## 9. Чек-лист оптимизации для проекта

| Проверка | Команда |
|----------|---------|
| Индексы используются? | `EXPLAIN` -- ищи `NodeIndexSeek` |
| Параметры, не литералы? | Все значения через `$param` |
| Глубина обхода ограничена? | `[*1..N]`, не `[*]` |
| Направление указано? | `-[:TYPE]->`, не `-[:TYPE]-` |
| Пакетная обработка? | `UNWIND` или `apoc.periodic.iterate` |
| db hits приемлемы? | `PROFILE` -- минимизировать db hits |
| Ранняя фильтрация? | WHERE максимально близко к MATCH |
| Page Cache достаточен? | `server.memory.pagecache.size` >= размер данных |
