# Neo4j: Временные графы и хронология

> [!TIP]
> Верифицировано 2026-02-26. Источники: Neo4j Cypher Manual (Cypher 25), Neo4j Operations Manual (2026.01.x).
> Временные типы -- нативная функциональность Neo4j.

---

## 1. Нативные временные типы

Neo4j поддерживает полный набор ISO 8601 временных типов:

| Тип | Описание | Пример |
|-----|----------|--------|
| `Date` | Календарная дата | `date('2026-02-26')` |
| `Time` | Время с часовым поясом | `time('14:30:00+03:00')` |
| `LocalTime` | Время без часового пояса | `localtime('14:30:00')` |
| `DateTime` | Дата + время + часовой пояс | `datetime('2026-02-26T14:30:00+03:00')` |
| `LocalDateTime` | Дата + время без часового пояса | `localdatetime('2026-02-26T14:30:00')` |
| `Duration` | Интервал времени | `duration('P1DT2H30M')` = 1 день 2 часа 30 минут |

### Создание временных значений

```cypher
// Текущий момент
RETURN datetime() AS сейчас

// Из компонентов
RETURN date({year: 2026, month: 2, day: 26}) AS дата

// Из строки ISO 8601
RETURN datetime('2026-02-26T14:30:00+03:00') AS момент

// Duration
RETURN duration({days: 7, hours: 3}) AS неделя_и_три_часа
RETURN duration('P7DT3H') AS то_же_самое
```

### Арифметика с временными типами

```cypher
// Сколько времени прошло с момента
WITH datetime('2026-01-01T00:00:00Z') AS начало
RETURN duration.between(начало, datetime()) AS прошло

// Добавить интервал к дате
RETURN date('2026-02-26') + duration({months: 1}) AS через_месяц

// Разница в днях
WITH datetime('2026-02-20T10:00:00Z') AS a,
     datetime('2026-02-26T14:00:00Z') AS b
RETURN duration.between(a, b) AS разница
// Результат: P6DT4H (6 дней и 4 часа)
```

---

## 2. Стратегии моделирования истории

### Стратегия "Интервалы" (Bi-temporal)

На каждой связи или узле хранятся `valid_from` и `valid_to`. Позволяет делать "срезы" графа на любой момент времени.

```cypher
// Создание связи с интервалом
MATCH (h:Hero {id: $heroId}), (npc:NPC {id: $npcId})
CREATE (h)-[:ЧУВСТВУЕТ_К {
  тип: 'доверие',
  значение: 7,
  valid_from: datetime(),
  valid_to: null
}]->(npc)

// Срез на конкретный момент
MATCH (h:Hero {id: $heroId})-[r:ЧУВСТВУЕТ_К]->(npc:NPC)
WHERE r.valid_from <= $targetDateTime
  AND (r.valid_to IS NULL OR r.valid_to > $targetDateTime)
RETURN npc.name, r.тип, r.значение
```

**Для проекта:** используется для отношений (`FEELS_TOWARD`, `TRUSTS`) и состояний, где нужна полная история.

### Стратегия "Цепочка состояний" (State Chain)

Каждое изменение -- новый узел, связанный с предыдущим:

```cypher
// Создание нового состояния
MATCH (h:Hero {id: $heroId})-[:ТЕКУЩЕЕ_СОСТОЯНИЕ]->(old:Состояние)
CREATE (new:Состояние {
  значение: $newValue,
  timestamp: datetime(),
  причина: $reason
})
CREATE (old)-[:ПРЕДЫДУЩЕЕ]->(new)
// Переключение текущего указателя
DELETE (h)-[:ТЕКУЩЕЕ_СОСТОЯНИЕ]->(old)
CREATE (h)-[:ТЕКУЩЕЕ_СОСТОЯНИЕ]->(new)
CREATE (h)-[:БЫЛО]->(old)
```

| Плюсы | Минусы |
|-------|--------|
| Полный аудит | Удлинение путей |
| Нет блокировок при записи истории | Больше узлов |
| Легко сравнить "было/стало" | Запросы сложнее |

**Для проекта:** используется для Beats (сжатие сцен) и дневных сводок.

### Стратегия "Перезапись + снимки" (Overwrite + Snapshot)

Текущее значение перезаписывается. Периодически создаются снимки (конец дня, конец недели).

```cypher
// Перезапись текущего
MATCH (h:Hero {id: $heroId})-[r:ЧУВСТВУЕТ]->(e:Эмоция {название: 'тревога'})
SET r.интенсивность = $newIntensity, r.updated_at = datetime()

// Снимок на конец дня
MATCH (h:Hero {id: $heroId})-[r:ЧУВСТВУЕТ]->(e:Эмоция)
CREATE (snap:Снимок {
  дата: date(),
  герой: $heroId,
  данные: apoc.convert.toJson(
    collect({эмоция: e.название, интенсивность: r.интенсивность})
  )
})
```

**Для проекта:** основная стратегия для эмоций (меняются каждую сцену, полная история не нужна).

---

## 3. Алгоритмы затухания (Decay Functions)

### Экспоненциальное затухание (воспоминания)

```cypher
// Формула: новое_значение = текущее * exp(-rate * дни_с_последнего_доступа)
MATCH (h:Hero)-[r:ПОМНИТ]->(m:Memory)
WHERE m.last_access IS NOT NULL
WITH m, r, duration.between(m.last_access, datetime()).days AS дней_прошло
SET m.яркость = m.яркость * exp(-0.00033 * дней_прошло)
// -0.00033 дает ~1% потери за месяц для обычных воспоминаний
```

### Линейное затухание (отношения без контакта)

```cypher
// Формула: -2% в неделю для интереса и комфорта
MATCH (h:Hero)-[r:ОТНОСИТСЯ]->(npc:NPC)
WHERE r.последний_контакт IS NOT NULL
WITH r, duration.between(r.последний_контакт, datetime()).days / 7.0 AS недель
SET r.интерес = r.интерес * (1.0 - 0.02 * недель),
    r.комфорт = r.комфорт * (1.0 - 0.02 * недель),
    r.доверие = r.доверие * (1.0 - 0.005 * недель)
// Доверие падает медленнее: -0.5% в неделю
```

### Ступенчатое затухание (мании)

```cypher
// -5% в день без подкрепления
MATCH (h:Hero)-[r:ФИКСИРОВАН]->(m:Мания)
WHERE m.последнее_подкрепление IS NOT NULL
WITH r, m, duration.between(m.последнее_подкрепление, datetime()).days AS дней
SET r.интенсивность = CASE
  WHEN дней < 1 THEN r.интенсивность
  ELSE r.интенсивность * power(0.95, дней)
END
```

### Дрейф эмоций к базовому

```cypher
// Эмоции дрейфуют к базовому уровню ~1/час
MATCH (h:Hero)-[r:ЧУВСТВУЕТ]->(e:Эмоция)
WHERE r.updated_at IS NOT NULL
WITH r, e,
     duration.between(r.updated_at, datetime()).hours AS часов,
     h.базовое_настроение AS базовое
SET r.интенсивность = r.интенсивность + (0 - r.интенсивность) * (1 - exp(-1.0 * часов))
// Дрейф к 0 (нейтрали) с полупериодом ~1 час
```

### Пакетное затухание через APOC

```cypher
// Запуск затухания всех воспоминаний пакетами
CALL apoc.periodic.iterate(
  "MATCH (m:Memory)
   WHERE m.last_access IS NOT NULL
     AND duration.between(m.last_access, datetime()).days > 0
   RETURN m",
  "WITH m
   SET m.яркость = m.яркость * exp(-0.00033 * duration.between(m.last_access, datetime()).days)",
  {batchSize: 5000, parallel: false}
)
```

---

## 4. Порог забывания и архивация

### Архивация низкозначимых узлов

```cypher
// Воспоминания с яркостью ниже 0.5 архивируются в сводку
MATCH (m:Memory)
WHERE m.яркость < 0.5
WITH m, m.описание AS описание
// Создаем сжатую запись
CREATE (s:Сводка {
  период: m.дата,
  содержание: описание,
  archived_at: datetime()
})
DETACH DELETE m
```

### Удаление устаревших Beat-ов

```cypher
// Beat-ы старше 30 сцен сжимаются в дневную сводку
MATCH (b:Beat)
WHERE b.сцена_номер < $currentScene - 30
WITH b, b.сцена_дата AS дата
// Агрегация в дневную сводку (если её ещё нет)
MERGE (ds:Дневная_сводка {дата: date(дата)})
ON CREATE SET ds.события = []
SET ds.события = ds.события + [b.описание]
DETACH DELETE b
```

---

## 5. Событийные графы (Event Sourcing)

### Цепочка сцен

```cypher
(:Сцена {номер: 1})-[:СЛЕДУЮЩАЯ]->(:Сцена {номер: 2})-[:СЛЕДУЮЩАЯ]->(:Сцена {номер: 3})
```

### Привязка моментов к сценам

```cypher
CREATE (moment:Момент {
  timestamp: datetime(),
  описание: $description
})
MATCH (scene:Сцена {номер: $sceneNumber})
CREATE (scene)-[:СОДЕРЖИТ]->(moment)
CREATE (moment)-[:ГЕРОЙ_ЧУВСТВОВАЛ]->(emotion)
CREATE (moment)-[:ПРОИЗОШЛО_В]->(location)
```

### Запрос: "Что герой чувствовал в этот день"

```cypher
MATCH (s:Сцена)-[:СОДЕРЖИТ]->(m:Момент)-[:ГЕРОЙ_ЧУВСТВОВАЛ]->(e:Эмоция)
WHERE date(s.timestamp) = date($targetDate)
RETURN s.номер, m.описание, collect({эмоция: e.название, интенсивность: e.значение})
ORDER BY s.номер
```

---

## 6. Работа с часовыми поясами

### Правило: хранение в UTC, отображение в локальном

```cypher
// Запись в UTC
CREATE (m:Момент {
  timestamp: datetime({timezone: 'UTC'}),
  local_timezone: 'Europe/Moscow'
})

// Чтение с конвертацией
MATCH (m:Момент)
RETURN m.timestamp AS utc,
       datetime({
         datetime: m.timestamp,
         timezone: m.local_timezone
       }) AS локальное_время
```

### Часовой пояс героя (через Хронос)

```cypher
MATCH (h:Hero {id: $heroId})-[:НАХОДИТСЯ_В]->(l:Локация)
RETURN l.timezone AS часовой_пояс
// Хронос использует этот пояс для инициации сцены
```
