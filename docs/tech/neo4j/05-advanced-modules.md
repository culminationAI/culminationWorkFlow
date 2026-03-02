# Neo4j: APOC и Graph Data Science (GDS)

> [!TIP]
> Верифицировано 2026-02-26. Источники: Neo4j APOC Documentation (current), Neo4j GDS Manual.
> APOC Core включен в Neo4j 5+/2026.01. GDS -- отдельная библиотека (лицензия).

---

## 1. APOC (Awesome Procedures on Cypher)

APOC -- библиотека из 450+ процедур и функций, расширяющих Cypher. С Neo4j 5+ APOC Core входит в дистрибутив. APOC Extended устанавливается отдельно.

### 1.1. Установка и активация

```properties
# neo4j.conf -- для APOC Extended
dbms.security.procedures.unrestricted=apoc.*
dbms.security.procedures.allowlist=apoc.*
```

Для Docker:

```yaml
environment:
  - NEO4J_PLUGINS=["apoc"]
  # Или для Extended:
  - NEO4J_PLUGINS=["apoc", "apoc-extended"]
```

### 1.2. Загрузка данных

#### apoc.load.json -- импорт из JSON

```cypher
CALL apoc.load.json('https://api.example.com/heroes.json')
YIELD value
MERGE (h:Hero {id: value.id})
SET h.name = value.name, h.age = value.age
```

С фильтрацией по JSON path:

```cypher
CALL apoc.load.json('file:///heroes.json', '$.heroes[?(@.age > 25)]')
YIELD value
RETURN value.name, value.age
```

#### apoc.load.csv -- импорт CSV

```cypher
CALL apoc.load.csv('file:///memories.csv', {header: true, sep: ','})
YIELD map
MERGE (m:Memory {id: map.id})
SET m.описание = map.description,
    m.яркость = toFloat(map.brightness)
```

**Важно:** `apoc.import.csv` -- НЕ СУЩЕСТВУЕТ. Правильное имя: `apoc.load.csv`.

#### apoc.load.jdbc -- импорт из реляционных БД

```cypher
CALL apoc.load.jdbc('jdbc:postgresql://host/db', 'SELECT * FROM characters')
YIELD row
MERGE (n:NPC {id: row.id})
SET n.name = row.name
```

### 1.3. Экспорт данных

```cypher
// Экспорт всего графа в JSON
CALL apoc.export.json.all('export.json', {})

// Экспорт результата запроса
CALL apoc.export.json.query(
  "MATCH (h:Hero)-[:ПОМНИТ]->(m:Memory) RETURN h, m",
  'hero_memories.json', {}
)

// Экспорт в CSV
CALL apoc.export.csv.query(
  "MATCH (n:NPC) RETURN n.name, n.age",
  'npcs.csv', {}
)
```

### 1.4. Пакетные операции

#### apoc.periodic.iterate -- основной инструмент для массовых обновлений

```cypher
// Затухание всех воспоминаний
CALL apoc.periodic.iterate(
  "MATCH (m:Memory)
   WHERE m.яркость > 0.1 AND m.last_access IS NOT NULL
   RETURN m",
  "SET m.яркость = m.яркость * 0.999",
  {batchSize: 10000, parallel: false, iterateList: true}
)
YIELD batches, total, timeTaken, errorMessages
```

**Параметры:**

| Параметр | Описание | Рекомендация |
|----------|----------|-------------|
| `batchSize` | Узлов на пакет | 5000-10000 |
| `parallel` | Параллельные пакеты | `false` если пакеты пересекаются |
| `iterateList` | Передавать список, не по одному | `true` для производительности |
| `retries` | Повторы при ошибке | 3 |
| `concurrency` | Потоков при parallel:true | 4 (по умолчанию) |

#### apoc.periodic.commit -- фиксация по условию

```cypher
// Удалять пачками, пока есть что удалять
CALL apoc.periodic.commit(
  "MATCH (m:Memory)
   WHERE m.яркость < 0.01
   WITH m LIMIT $limit
   DETACH DELETE m
   RETURN count(*)",
  {limit: 10000}
)
```

### 1.5. Рефакторинг графа

```cypher
// Объединение дублирующихся узлов
CALL apoc.refactor.mergeNodes(
  [node1, node2],
  {properties: 'combine', mergeRels: true}
)

// Изменение типа связи
CALL apoc.refactor.setType(rel, 'НОВЫЙ_ТИП')

// Перенос свойства из узла в связь
MATCH (h:Hero)-[r:ЧУВСТВУЕТ]->(e:Эмоция)
CALL apoc.refactor.normalizeAsBoolean(r, 'активна', ['да', 'true'], ['нет', 'false'])
YIELD input, output
RETURN count(*)
```

### 1.6. Триггеры (APOC Extended)

```cypher
// Автоматическое обновление timestamp при изменении узла
CALL apoc.trigger.add(
  'update_timestamp',
  "UNWIND $createdNodes AS n
   SET n.updated_at = datetime()",
  {phase: 'afterAsync'}
)

// Список триггеров
CALL apoc.trigger.list()

// Удаление триггера
CALL apoc.trigger.remove('update_timestamp')
```

### 1.7. Утилиты

```cypher
// Конвертация узла в Map
RETURN apoc.convert.toMap(node) AS nodeMap

// Объединение Map-ов
RETURN apoc.map.merge({a: 1}, {b: 2}) AS merged
// {a: 1, b: 2}

// Генерация UUID
RETURN apoc.create.uuid() AS id

// Форматирование дат
RETURN apoc.date.format(timestamp(), 'ms', 'yyyy-MM-dd HH:mm:ss') AS formatted

// Работа с коллекциями
RETURN apoc.coll.flatten([[1,2],[3,4]]) AS flat
// [1, 2, 3, 4]

RETURN apoc.coll.sortNodes([node1, node2], 'name') AS sorted
```

### 1.8. Расширенные пути

```cypher
// apoc.path.expandConfig -- гибкий обход с фильтрацией
MATCH (h:Hero {id: $heroId})
CALL apoc.path.expandConfig(h, {
  relationshipFilter: "ПОМНИТ>|ЧУВСТВУЕТ>|СВЯЗАНО_С>",
  labelFilter: "+Memory|+Эмоция|/NPC",
  minLevel: 1,
  maxLevel: 3,
  limit: 50
})
YIELD path
RETURN path
```

**Синтаксис фильтров:**
- `+Label` -- включить (whitelist)
- `-Label` -- исключить (blacklist)
- `/Label` -- терминальный (конец пути)
- `>` после типа связи -- только исходящие
- `<` -- только входящие

---

## 2. Graph Data Science (GDS)

GDS -- библиотека алгоритмов графовой аналитики. Работает с проекциями графа в памяти для высокой производительности.

### 2.1. Установка

```properties
# neo4j.conf
dbms.security.procedures.unrestricted=gds.*
dbms.security.procedures.allowlist=gds.*
```

Docker:

```yaml
environment:
  - NEO4J_PLUGINS=["graph-data-science"]
```

### 2.2. Проекции графа (Graph Catalog)

**Важно:** `gds.graph.project()` с строковыми параметрами -- deprecated в GDS 2.x. Используйте Cypher-проекции или нативные проекции.

#### Нативная проекция

```cypher
CALL gds.graph.project(
  'social_graph',                    -- имя проекции
  ['Hero', 'NPC'],                   -- метки узлов
  {
    KNOWS: {
      type: 'ЗНАЕТ',
      orientation: 'UNDIRECTED',
      properties: ['duration']
    },
    FEELS: {
      type: 'ЧУВСТВУЕТ_К',
      orientation: 'NATURAL',
      properties: {
        weight: {
          property: 'значение',
          defaultValue: 0.0
        }
      }
    }
  }
)
YIELD graphName, nodeCount, relationshipCount
```

#### Cypher-проекция (более гибкая)

```cypher
CALL gds.graph.project.cypher(
  'hero_memory_graph',
  'MATCH (n) WHERE n:Hero OR n:Memory RETURN id(n) AS id, labels(n) AS labels',
  'MATCH (h:Hero)-[r:ПОМНИТ]->(m:Memory) RETURN id(h) AS source, id(m) AS target, r.яркость AS weight'
)
```

#### Управление каталогом

```cypher
// Список всех проекций
CALL gds.graph.list()

// Удаление проекции (освобождает память)
CALL gds.graph.drop('social_graph')

// Проверка существования
CALL gds.graph.exists('social_graph')
YIELD exists
```

### 2.3. Алгоритмы центральности (Importance)

#### PageRank -- транзитивное влияние

```cypher
CALL gds.pageRank.stream('social_graph', {
  maxIterations: 20,
  dampingFactor: 0.85,
  relationshipWeightProperty: 'weight'
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
RETURN node.name, labels(node), score
ORDER BY score DESC
LIMIT 10
```

**Для проекта:** определение самых влиятельных NPC в жизни героя.

#### Betweenness Centrality -- узлы-мосты

```cypher
CALL gds.betweennessCentrality.stream('social_graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS node, score
WHERE score > 0
RETURN node.name, score
ORDER BY score DESC
```

**Для проекта:** NPC, через которых проходят основные социальные связи героя.

#### Degree Centrality -- количество связей

```cypher
CALL gds.degree.stream('social_graph', {
  orientation: 'UNDIRECTED'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score AS connections
ORDER BY connections DESC
```

### 2.4. Алгоритмы сообществ (Community Detection)

#### Louvain -- обнаружение социальных кластеров

```cypher
CALL gds.louvain.stream('social_graph', {
  relationshipWeightProperty: 'weight'
})
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS node, communityId
RETURN communityId, collect(node.name) AS members
ORDER BY size(collect(node.name)) DESC
```

**Для проекта:** автоматическая группировка NPC в социальные круги (семья, коллеги, друзья).

#### Leiden -- улучшенный Louvain

```cypher
CALL gds.leiden.stream('social_graph', {
  gamma: 1.0,
  theta: 0.01,
  maxLevels: 10
})
YIELD nodeId, communityId
```

#### Weakly Connected Components (WCC)

```cypher
CALL gds.wcc.stream('social_graph')
YIELD nodeId, componentId
// Находит изолированные группы узлов
```

### 2.5. Алгоритмы подобия (Similarity)

#### Node Similarity -- Jaccard/Overlap

```cypher
CALL gds.nodeSimilarity.stream('social_graph', {
  similarityCutoff: 0.3,
  topK: 5
})
YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS a, gds.util.asNode(node2) AS b, similarity
RETURN a.name, b.name, similarity
ORDER BY similarity DESC
```

**Для проекта:** поиск NPC с похожими социальными связями (потенциальные конфликты или союзы).

#### K-Nearest Neighbors (KNN)

```cypher
CALL gds.knn.stream('social_graph', {
  topK: 3,
  nodeProperties: ['weight'],
  sampleRate: 1.0,
  randomSeed: 42
})
YIELD node1, node2, similarity
```

### 2.6. Link Prediction -- предсказание связей

```cypher
CALL gds.linkPrediction.adamicAdar.stream('social_graph', {
  topN: 10
})
YIELD node1, node2, score
WITH gds.util.asNode(node1) AS a, gds.util.asNode(node2) AS b, score
RETURN a.name, b.name, score
ORDER BY score DESC
```

**Для проекта:** предсказание потенциальных новых знакомств или конфликтов.

### 2.7. Режимы выполнения

Каждый алгоритм GDS доступен в 4 режимах:

| Режим | Описание | Пример |
|-------|----------|--------|
| `stream` | Возвращает результат как поток | `gds.pageRank.stream(...)` |
| `stats` | Только статистика (без данных) | `gds.pageRank.stats(...)` |
| `mutate` | Записывает в проекцию (не в БД) | `gds.pageRank.mutate(...)` |
| `write` | Записывает обратно в БД | `gds.pageRank.write(...)` |

```cypher
// Записать PageRank обратно в узлы
CALL gds.pageRank.write('social_graph', {
  writeProperty: 'pagerank',
  maxIterations: 20
})
YIELD nodePropertiesWritten, ranIterations
```

---

## 3. Использование в проекте "Интерпретация"

### APOC: регулярные задачи

| Задача | Процедура |
|--------|-----------|
| Затухание воспоминаний | `apoc.periodic.iterate` + формула decay |
| Затухание отношений | `apoc.periodic.iterate` + линейное снижение |
| Архивация Beat-ов | `apoc.periodic.commit` + DETACH DELETE |
| Экспорт дневных сводок | `apoc.export.json.query` |
| Рефакторинг NPC (слияние дублей) | `apoc.refactor.mergeNodes` |
| Обход подграфа для контекста | `apoc.path.expandConfig` |

### GDS: аналитика для Драматурга и Судьбы

| Задача | Алгоритм |
|--------|----------|
| Социальные кластеры NPC | Louvain / Leiden |
| Самые влиятельные NPC | PageRank |
| NPC-мосты между кругами | Betweenness Centrality |
| Похожие воспоминания | Node Similarity / KNN |
| Предсказание новых связей | Link Prediction |
| Изолированные группы (одинокие NPC) | WCC |
