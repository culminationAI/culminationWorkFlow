# Neo4j: Концепции и моделирование данных

> [!TIP]
> Верифицировано 2026-02-26. Источники: Neo4j Cypher Manual (Cypher 25), Neo4j Operations Manual (2026.01.x).
> Актуальная версия: **Neo4j 2026.01.4** (Calendar Versioning, миграция с 5.26 LTS).

---

## 1. Модель Labeled Property Graph (LPG)

Neo4j использует модель LPG -- стандарт де-факто для графовых баз данных. В отличие от RDF/триплетов, LPG позволяет хранить произвольные свойства как на узлах, так и на связях.

### Ключевые компоненты

| Компонент | Описание |
|-----------|----------|
| **Узлы (Nodes)** | Представляют сущности. Могут иметь 0+ меток (Labels). Каждый узел имеет уникальный внутренний `elementId()`. |
| **Связи (Relationships)** | Всегда направлены, всегда имеют ровно один тип. Могут содержать свойства (веса, даты, заряды). |
| **Метки (Labels)** | Классифицируют узлы. Узел может иметь несколько меток: `(:Hero:Person)`. Используются для индексации и ограничений. |
| **Свойства (Properties)** | Пары ключ-значение на узлах и связях. |

### Поддерживаемые типы свойств

```
String, Integer, Float, Boolean
Point (географические координаты)
Date, Time, LocalTime, DateTime, LocalDateTime, Duration
Списки (массивы) перечисленных типов
```

**Важно:** Свойства не могут быть вложенными объектами (map). Для сложных структур используйте JSON-строки или вынесение в отдельные узлы.

### elementId() вместо id()

```cypher
-- DEPRECATED (удалено в 2026.01):
-- MATCH (n) WHERE id(n) = 42 RETURN n

-- АКТУАЛЬНО:
MATCH (n) WHERE elementId(n) = '4:abc:123' RETURN n
```

`elementId()` возвращает строку, уникальную в рамках СУБД. Функция `id()` удалена начиная с Neo4j 5.x+ и недоступна в 2026.01.

---

## 2. Стратегии моделирования

### Когда атрибут выносить в узел

Свойство становится отдельным узлом, когда:
- Оно имеет собственные связи (эмоция связана с воспоминанием и триггером)
- Оно меняется со временем и нужна история изменений
- По нему нужна навигация (обход графа через это свойство)
- Оно разделяется между сущностями (локация посещается многими героями)

```
-- Плохо: свойство на узле
(:Hero {current_emotion: "тревога", emotion_intensity: 7})

-- Хорошо: отдельный узел
(:Hero)-[:ЧУВСТВУЕТ {интенсивность: 7}]->(:Эмоция {название: "тревога"})
```

### Гиперребра через промежуточные узлы

Для связей между 3+ сущностями используется промежуточный узел:

```cypher
CREATE (e:Encounter {timestamp: datetime(), description: "встреча в кафе"})
CREATE (hero)-[:УЧАСТВУЕТ]->(e)
CREATE (npc)-[:УЧАСТВУЕТ]->(e)
CREATE (e)-[:ПРОИСХОДИТ_В]->(location)
```

### Суперузлы (Dense Nodes)

Узлы с тысячами связей замедляют обходы. Решения:
- **Фильтрация по типу связи:** используйте специфичные типы вместо общих
- **Партиционирование по времени:** `FEELS_TOWARD_2026_01` вместо одного типа
- **Индексирование:** Range-индексы на свойствах связей для фильтрации

---

## 3. Индексы

Neo4j 2026.01 поддерживает следующие типы индексов:

### Range Index (по умолчанию)

Для точного совпадения, диапазонов, сортировки. Работает со всеми типами свойств.

```cypher
CREATE INDEX hero_name_range FOR (h:Hero) ON (h.name)
```

### Composite Index

Индекс по нескольким свойствам одной метки:

```cypher
CREATE INDEX memory_composite FOR (m:Memory) ON (m.hero_id, m.created_at)
```

### Text Index

Оптимизирован для строковых операций: `CONTAINS`, `STARTS WITH`, `ENDS WITH`.

```cypher
CREATE TEXT INDEX description_text FOR (m:Memory) ON (m.description)
```

Использование:
```cypher
MATCH (m:Memory)
WHERE m.description CONTAINS 'кафе'
RETURN m
```

### Point Index

Для географических запросов с типом `Point`:

```cypher
CREATE POINT INDEX location_point FOR (l:Location) ON (l.coordinates)
```

### Token Lookup Index

Системный индекс для быстрого поиска по меткам узлов и типам связей. Создается автоматически. Используется планировщиком при `MATCH (n:Label)`.

### Full-text Index

Основан на Apache Lucene. Поддерживает полнотекстовый поиск с релевантностью, нечеткий поиск, стемминг.

```cypher
CREATE FULLTEXT INDEX memory_fulltext
FOR (m:Memory)
ON EACH [m.description, m.context]

-- Запрос:
CALL db.index.fulltext.queryNodes('memory_fulltext', 'кафе встреча')
YIELD node, score
RETURN node.description, score
ORDER BY score DESC
```

### Vector Index

Нативный векторный индекс (подробнее в 03-graphrag.md):

```cypher
CREATE VECTOR INDEX memory_embeddings
FOR (m:Memory) ON (m.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1024,
  `vector.similarity_function`: 'cosine'
}}
```

---

## 4. Ограничения (Constraints)

Constraints обеспечивают целостность данных и автоматически создают индексы.

### Уникальность

```cypher
CREATE CONSTRAINT hero_id_unique FOR (h:Hero) REQUIRE h.id IS UNIQUE
```

### Обязательность свойства (Node Property Existence)

```cypher
-- АКТУАЛЬНО (Cypher 25):
CREATE CONSTRAINT hero_name_exists FOR (h:Hero) REQUIRE h.name IS NOT NULL

-- DEPRECATED:
-- CREATE CONSTRAINT ... REQUIRE exists(h.name)
```

**Важно:** `exists()` как предикат в constraints -- deprecated. Используйте `IS NOT NULL`.

### Обязательность свойства связи

```cypher
CREATE CONSTRAINT feels_weight_exists
FOR ()-[r:FEELS_TOWARD]-() REQUIRE r.weight IS NOT NULL
```

### Уникальность узла по комбинации свойств (Node Key)

```cypher
CREATE CONSTRAINT memory_key
FOR (m:Memory) REQUIRE (m.hero_id, m.created_at) IS NODE KEY
```

Node Key = уникальность + обязательность для всех свойств в комбинации.

### Типизация свойств (Property Type)

Доступно в Neo4j 5.11+ / 2026.01:

```cypher
CREATE CONSTRAINT hero_age_type
FOR (h:Hero) REQUIRE h.age IS :: INTEGER
```

---

## 5. Специфика Neo4j 2026.01

### Calendar Versioning

С версии 2026.01 Neo4j перешел на календарное версионирование (ранее 5.x). Миграция с 5.26 LTS поддерживается штатно.

### Ключевые deprecated

| Deprecated | Замена | С версии |
|-----------|--------|----------|
| `id()` | `elementId()` | 5.0 |
| `exists()` в constraints | `IS NOT NULL` | 5.0 |
| `dbms.tx_log.*` конфигурация | `db.tx_log.*` | 5.0 |
| `dbms.security.auth_enabled` | `server.security.auth_enabled` | 5.0 |

### Улучшения 2026.01

- Оптимизация очистки пространства при удалении больших свойств
- Улучшенное отслеживание дедлоков через метрики реального времени
- Нативные векторные индексы как first-class citizens в Cypher 25
- Property Type Constraints для строгой типизации
