# 06. Prompt Caching

> [!TIP]
> Верифицировано 2026-02-26. Источники: Context7 (platform.claude.com), Anthropic SDK Python.

---

## Что такое Prompt Caching

Prompt caching позволяет кэшировать часто используемые фрагменты промптов (system prompt, определения инструментов, документы) и переиспользовать их в последующих запросах без повторной обработки. Экономия до 90% на input-токенах.

---

## Как работает

1. В первом запросе вы помечаете блоки контента маркером `cache_control`
2. Anthropic кэширует эти блоки на стороне сервера
3. В последующих запросах кэшированные блоки не пересчитываются

**Важно:** кэширование происходит автоматически на основе точного совпадения контента. Если хотя бы один символ изменился -- кэш не используется.

---

## Cache Control Breakpoints

```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 1024,
  "system": [
    {
      "type": "text",
      "text": "Ты -- агент проекта Интерпретация. Твоя роль: Драматург...",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "messages": [
    {"role": "user", "content": "Создай сцену встречи героев"}
  ]
}
```

### Параметры cache_control

| Параметр | Тип | Описание |
|----------|-----|----------|
| `type` | string | Всегда `"ephemeral"` |
| `ttl` | string | Время жизни: `"5m"` (по умолчанию) или `"1h"` |

```json
"cache_control": {"type": "ephemeral", "ttl": "1h"}
```

---

## TTL (Time-To-Live)

| TTL | Стоимость записи | Когда использовать |
|-----|-------------------|-------------------|
| `"5m"` (default) | 25% сверх base input | Часто меняющийся контент |
| `"1h"` | Выше, чем 5m | Стабильные system prompts, определения инструментов |

---

## Pricing

| Операция | Стоимость (Opus 4.6) |
|----------|---------------------|
| Cache write | 125% от base input ($6.25/1M) |
| Cache read | 10% от base input ($0.50/1M) |
| Base input (uncached) | $5.00/1M |

**Экономия:** при 10 запросах с одинаковым system prompt в 50K токенов:
- Без кэша: 10 x 50K x $5/1M = $2.50
- С кэшем: 1 write ($0.3125) + 9 reads ($0.225) = $0.54
- **Экономия: 78%**

---

## Что можно кэшировать

1. **System prompts** -- идеально для агентов с фиксированными инструкциями
2. **Tool definitions** -- определения инструментов (tools array)
3. **Документы в messages** -- большие контексты, вставленные в user messages
4. **Prefill** -- assistant prefill content

### Множественные breakpoints

Можно ставить несколько `cache_control` в одном запросе:

```json
{
  "system": [
    {
      "type": "text",
      "text": "Базовые инструкции агента...",
      "cache_control": {"type": "ephemeral", "ttl": "1h"}
    }
  ],
  "tools": [
    {
      "name": "search_graph",
      "description": "Поиск по графу знаний",
      "input_schema": {"type": "object", "properties": {}},
      "cache_control": {"type": "ephemeral", "ttl": "1h"}
    }
  ]
}
```

**Стоимость breakpoints:** сами breakpoints бесплатны. Стоимость определяется только объёмом кэшированного контента.

---

## Python SDK

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "Ты -- Драматург проекта Интерпретация...",
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        }
    ],
    messages=[
        {"role": "user", "content": "Оцени драматическую структуру сцены"}
    ]
)

# Проверка использования кэша
print(f"Input tokens: {response.usage.input_tokens}")
print(f"Cache creation: {response.usage.cache_creation_input_tokens}")
print(f"Cache read: {response.usage.cache_read_input_tokens}")
```

---

## Применение в проекте «Интерпретация»

12 агентов проекта имеют фиксированные system prompts (5-20K токенов каждый). При 18-22 LLM-вызовах на тик prompt caching критичен:

| Что кэшировать | TTL | Обоснование |
|----------------|-----|-------------|
| System prompts агентов | `"1h"` | Меняются только при деплое |
| Tool definitions | `"1h"` | Фиксированный набор инструментов |
| Контекст графа (GraphRAG) | `"5m"` | Меняется между сценами |
| Описание текущей сцены | `"5m"` | Уникально для каждой сцены |

**Ожидаемая экономия:** 30-40% от общей стоимости input-токенов (см. [10-token-and-cost-estimate.md](../10-token-and-cost-estimate.md)).
