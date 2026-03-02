# 10. Интеграция Claude с проектом «Интерпретация»

> [!TIP]
> Верифицировано 2026-02-26. На основе проектной документации: docs/03-agent-hierarchy.md, docs/04-scene-pipeline.md, docs/10-token-and-cost-estimate.md.

---

## Обзор

Проект «Интерпретация» использует Claude как основной LLM-движок для 12 агентов. Каждый агент -- отдельный вызов Claude API с уникальным system prompt, набором инструментов и форматом вывода.

---

## Распределение моделей по агентам

| Слой | Агент | Модель | Обоснование |
|------|-------|--------|-------------|
| **Being** | Внутреннее | Opus 4.6 + thinking | Самый сложный: моделирование сознания |
| **Being** | Мониторинг | Sonnet 4.6 | Обработка эмоциональных векторов |
| **World** | Сеттинг | Sonnet 4.6 | Описание окружения |
| **World** | Популяция | Sonnet 4.6 | NPC, массовые сцены |
| **Encounter** | Связь | Opus 4.6 | Сложная динамика отношений |
| **Encounter** | Действие | Sonnet 4.6 | Механики взаимодействия |
| **Encounter** | Голос | Opus 4.6 + thinking | Уникальный стиль речи каждого персонажа |
| **Action** | Судьба | Opus 4.6 + thinking | Стратегические решения |
| **Action** | Верификатор | Sonnet 4.6 | Проверка consistency |
| **Management** | Драматург | Opus 4.6 + thinking | Нарративная структура |
| **Management** | Хронос | Haiku 4.5 | Простая задача: тики времени |
| **Management** | Режиссёр | Opus 4.6 | Оркестрация сцены |
| **Management** | Летописец | Sonnet 4.6 | Ведение журнала |
| **Management** | Читатель | Sonnet 4.6 | Интерфейс пользователя |

---

## Pipeline сцены: 18-22 LLM-вызова

Одна сцена проходит через 7 фаз (см. [04-scene-pipeline.md](../04-scene-pipeline.md)):

```
Фаза 1: Контекст        → 4 вызова  (Сеттинг, Популяция, Хронос, Мониторинг)
Фаза 2: Внутреннее      → 3 вызова  (Внутреннее, Связь, Голос)
Фаза 3: Действие        → 4 вызова  (Действие, Судьба, Верификатор, Режиссёр)
Фаза 4: Генерация текста → 3 вызова  (Голос, Летописец, Читатель)
Фаза 5: Оценка          → 2 вызова  (Драматург, Верификатор)
Фаза 6: Обновление      → 10 вызовов (обновление графа, памяти)
```

---

## Стоимость на сцену

| Компонент | Токены (input) | Токены (output) | Стоимость |
|-----------|:--------------:|:---------------:|-----------|
| Opus 4.6 вызовы (~10) | ~80K | ~20K | ~$0.90 |
| Sonnet 4.6 вызовы (~14) | ~60K | ~15K | ~$0.30 |
| Haiku 4.5 вызовы (~2) | ~5K | ~2K | ~$0.01 |
| **Итого (без кэша)** | | | **~$1.21** |
| **С prompt caching 30%** | | | **~$0.85** |

**На день (8 сцен):** ~$6.80 с кэшем.

Подробный расчёт: [10-token-and-cost-estimate.md](../10-token-and-cost-estimate.md).

---

## Стратегия Prompt Caching

Для проекта критично кэширование:

### Уровень 1: Static (TTL 1h)
- System prompts всех 12 агентов (~100K токенов суммарно)
- Tool definitions (~20K)
- Базовые правила мира (~10K)

### Уровень 2: Session (TTL 5m)
- Текущее состояние героя (эмоции, цели, контекст) (~5K)
- Контекст текущей сцены (~3K)
- Результат GraphRAG-запроса (~5K)

### Ожидаемая экономия
- Static cache: ~130K tokens x 26 calls → hit rate ~95% → экономия ~$0.30/сцена
- Session cache: ~13K tokens x 26 calls → hit rate ~60% → экономия ~$0.05/сцена

---

## Structured Output по агентам

Все агенты используют JSON Schema для вывода (см. [07-structured-output.md](07-structured-output.md)):

```python
# Пример: output schema для агента "Внутреннее"
inner_state_schema = {
    "type": "object",
    "properties": {
        "dominant_emotion": {"type": "string"},
        "intensity": {"type": "number", "minimum": 0, "maximum": 1},
        "secondary_emotions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "emotion": {"type": "string"},
                    "intensity": {"type": "number"}
                }
            }
        },
        "inner_monologue": {"type": "string"},
        "active_memory": {"type": "string"},
        "behavioral_impulse": {"type": "string"}
    },
    "required": ["dominant_emotion", "intensity", "inner_monologue"],
    "additionalProperties": False
}
```

---

## Extended Thinking -- когда включать

| Агент | Thinking | Budget | Обоснование |
|-------|:--------:|:------:|-------------|
| Внутреннее | Да | 10K | Моделирование сложных эмоций |
| Голос | Да | 5K | Подбор уникального стиля |
| Судьба | Да | 8K | Стратегические последствия |
| Драматург | Да | 10K | Нарративный анализ |
| Остальные | Нет | — | Задачи достаточно прямолинейны |

---

## API Rate Limits и батчинг

Для независимых вызовов в рамках одной фазы используем параллельные запросы:

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def run_phase_1(scene_context: dict):
    """Фаза 1: 4 вызова параллельно."""
    tasks = [
        call_agent("setting", SETTING_PROMPT, scene_context, setting_schema, model="claude-sonnet-4-6"),
        call_agent("population", POPULATION_PROMPT, scene_context, population_schema, model="claude-sonnet-4-6"),
        call_agent("chronos", CHRONOS_PROMPT, scene_context, chronos_schema, model="claude-haiku-4-5-20251001"),
        call_agent("monitoring", MONITORING_PROMPT, scene_context, monitoring_schema, model="claude-sonnet-4-6"),
    ]
    return await asyncio.gather(*tasks)
```

**Rate limits (Opus 4.6):** учитывать при параллелизации. Для 12-агентной системы рекомендуется batch по фазам, а не все 18-22 вызова одновременно.

---

## Связанные документы

- [01-model-overview.md](01-model-overview.md) -- характеристики моделей
- [06-prompt-caching.md](06-prompt-caching.md) -- детали кэширования
- [07-structured-output.md](07-structured-output.md) -- JSON Schema для агентов
- [09-python-sdk.md](09-python-sdk.md) -- SDK для реализации
- [../04-scene-pipeline.md](../04-scene-pipeline.md) -- полный pipeline сцены
- [../10-token-and-cost-estimate.md](../10-token-and-cost-estimate.md) -- расчёт стоимости
- [../12-implementation-plan-mvp-and-scaling.md](../12-implementation-plan-mvp-and-scaling.md) -- план реализации
