# Neo4j: GraphRAG и векторный поиск

> [!TIP]
> Верифицировано 2026-02-26. Источники: Neo4j Cypher Manual (Cypher 25), Neo4j Operations Manual (2026.01.x).
> Векторный индекс -- нативная функциональность Neo4j с версии 5.11+.

---

## 1. Концепция GraphRAG

GraphRAG объединяет две модальности поиска:
- **Векторный поиск** -- семантическая близость (что похоже по смыслу)
- **Графовый обход** -- структурная связность (что связано по отношениям)

Результат: контекст для LLM, который содержит и семантически релевантные, и структурно связанные данные.

### Архитектура для проекта "Интерпретация"

```
Запрос сцены
    |
    v
[Векторный поиск] --> Top-K узлов по семантической близости
    |
    v
[Графовый обход] --> Связанные узлы (NPC, эмоции, планы)
    |
    v
[Реранкинг] --> Приоритизация по весам + релевантности
    |
    v
[Контекст для LLM] --> Минимальный, но достаточный набор данных
```

---

## 2. Нативный векторный индекс Neo4j

### Создание индекса

```cypher
CREATE VECTOR INDEX memory_embeddings IF NOT EXISTS
FOR (m:Memory) ON (m.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1024,
  `vector.similarity_function`: 'cosine'
}}
```

**Параметры:**
- `vector.dimensions` -- размерность вектора (1024 для multilingual-e5-large)
- `vector.similarity_function` -- функция близости: `cosine`, `euclidean`, `dot_product` (для нашего проекта нужно `cosine` -- это стандарт)

### Запись эмбеддинга

```cypher
MATCH (m:Memory {id: $memoryId})
CALL db.create.setNodeVectorProperty(m, 'embedding', $vector)
```

Или напрямую через SET:

```cypher
MATCH (m:Memory {id: $memoryId})
SET m.embedding = $vector
```

### Векторный поиск (Cypher 25)

```cypher
-- Поиск 10 ближайших воспоминаний
CALL db.index.vector.queryNodes('memory_embeddings', 10, $queryVector)
YIELD node AS memory, score
RETURN memory.описание, memory.яркость, score
ORDER BY score DESC
```

**Возвращаемые поля:**
- `node` -- найденный узел
- `score` -- оценка близости (0.0 -- 1.0 для cosine)

---

## 3. Паттерны GraphRAG-запросов

### Паттерн 1: Семантическая точка входа + обход

Находим семантически близкие узлы, затем обходим их окрестность:

```cypher
-- Шаг 1: Векторный поиск -- семантическая точка входа
CALL db.index.vector.queryNodes('memory_embeddings', 5, $queryVector)
YIELD node AS memory, score
WHERE score > 0.7

-- Шаг 2: Графовый обход -- контекст вокруг найденного
MATCH (memory)-[:СВЯЗАНО_С]->(entity)
OPTIONAL MATCH (memory)<-[:ПОМНИТ]-(h:Hero)
OPTIONAL MATCH (memory)-[:ТРИГГЕРИТСЯ]->(trigger)

RETURN memory.описание AS описание,
       memory.яркость AS яркость,
       score AS семантическая_близость,
       collect(DISTINCT entity) AS связанные_сущности,
       collect(DISTINCT trigger) AS триггеры
ORDER BY score DESC
```

### Паттерн 2: Мультимодальный контекст сцены

Комбинированный запрос для загрузки контекста сцены:

```cypher
// Текущие эмоции героя (графовый обход)
MATCH (h:Hero {id: $heroId})-[r:ЧУВСТВУЕТ]->(e:Эмоция)
WHERE r.интенсивность > 3
WITH h, collect({эмоция: e.название, интенсивность: r.интенсивность}) AS эмоции

// Активные планы (графовый обход)
OPTIONAL MATCH (h)-[rp:ИМЕЕТ_ПЛАН]->(p:План)
WHERE p.статус = 'активный'
WITH h, эмоции, collect({план: p.содержание, уверенность: rp.уверенность}) AS планы

// Релевантные воспоминания (векторный поиск)
CALL db.index.vector.queryNodes('memory_embeddings', 5, $sceneContextVector)
YIELD node AS memory, score
WHERE score > 0.6
MATCH (h)-[:ПОМНИТ]->(memory)

RETURN эмоции, планы,
       collect({
         описание: memory.описание,
         яркость: memory.яркость,
         релевантность: score
       }) AS воспоминания
```

### Паттерн 3: Поиск кратчайшего пути для объяснения связи

```cypher
CALL db.index.vector.queryNodes('memory_embeddings', 1, $queryVector)
YIELD node AS startNode, score

MATCH path = shortestPath(
  (startNode)-[*1..5]-(target:NPC {id: $npcId})
)
RETURN [n IN nodes(path) | labels(n)[0] + ': ' + coalesce(n.название, n.name, n.описание)] AS цепочка,
       length(path) AS расстояние
```

---

## 4. Взвешенный RAG

Для LLM важна не просто выборка, а приоритизация. Используем веса связей:

```cypher
MATCH (h:Hero {id: $heroId})-[r]->(n)
WHERE r.weight IS NOT NULL AND r.weight > $threshold
WITH n, r,
     CASE type(r)
       WHEN 'ПОМНИТ' THEN r.weight * 1.5      // воспоминания важнее
       WHEN 'ЧУВСТВУЕТ' THEN r.weight * 2.0    // эмоции -- приоритет
       WHEN 'ЗНАЕТ' THEN r.weight * 0.8        // знакомства -- ниже
       ELSE r.weight
     END AS priority
RETURN n, type(r) AS тип, r.weight AS вес, priority AS приоритет
ORDER BY priority DESC
LIMIT 20
```

---

## 5. Стратегия двухэтапного поиска (Retrieve + Rerank)

### Этап 1: Извлечение (Neo4j + Qdrant)

```
Neo4j: граф-запрос → структурно связанные узлы (NPC, локации, планы)
Qdrant: векторный поиск → семантически близкие чанки (описания, диалоги)
```

### Этап 2: Реранкинг (bge-reranker-v2-m3)

Объединенный набор кандидатов ранжируется моделью Cross-Encoder:

```python
# Псевдокод
candidates = neo4j_results + qdrant_results
reranked = reranker.rank(query=scene_context, documents=candidates)
context = reranked[:top_k]  # Только top_k попадает в промпт LLM
```

### Балансировка источников

| Тип контекста | Источник | Доля в промпте |
|--------------|----------|----------------|
| Текущее состояние героя | Neo4j (граф) | ~30% |
| Релевантные воспоминания | Qdrant (вектор) | ~25% |
| NPC и отношения | Neo4j (граф) | ~20% |
| Сеттинг и обстоятельства | Qdrant (вектор) | ~15% |
| Метаданные сцены | Neo4j (граф) | ~10% |

---

## 6. Кэширование подграфов

### Что кэшировать

- **Ядро героя** -- стабильные узлы (личность, ценности, страхи) -- меняются редко
- **Активное состояние** -- эмоции, ресурсы -- обновлять каждую сцену
- **NPC ближнего круга** -- профили и отношения -- обновлять при встрече

### Стратегия инвалидации

```
Сцена завершена → Летописец записал изменения →
  Если изменились веса: инвалидировать кэш затронутых подграфов
  Если появились новые узлы: добавить в кэш
  Если ничего не изменилось: кэш валиден
```

### TTL по типам

| Подграф | TTL | Причина |
|---------|-----|---------|
| Личность героя | 1 день (8 сцен) | Меняется медленно |
| Эмоции | 1 сцена | Меняются каждую сцену |
| NPC ядра | 1 сцена | Отношения обновляются при контакте |
| Локации | Без TTL | Статичны до изменения Драматургом |
