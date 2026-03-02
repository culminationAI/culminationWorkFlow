# Claude Opus 4.6 -- Справочник

> [!TIP]
> Верифицировано 2026-02-26. Источники: официальная документация Anthropic (docs.anthropic.com), WebSearch, знания модели Claude Opus 4.6 о собственном API. Выдуманные термины отсутствуют.

---

## О справочнике

Этот справочник создан для проекта «Интерпретация» и содержит только верифицированную информацию о Claude Opus 4.6 и связанных моделях Anthropic. Предыдущая версия (Manus) была удалена из-за 10+ выдуманных терминов и некорректных API-параметров.

**Модель:** Claude Opus 4.6 (`claude-opus-4-6`), выпущена 5 февраля 2026 года.

---

## Карта обучения

### Основы

| # | Файл | Содержание |
|---|------|-----------|
| 01 | [01-model-overview.md](01-model-overview.md) | Семейство моделей, характеристики, pricing, сравнение |
| 02 | [02-api-reference.md](02-api-reference.md) | Messages API, параметры, streaming, аутентификация |

### Ключевые возможности

| # | Файл | Содержание |
|---|------|-----------|
| 03 | [03-extended-thinking.md](03-extended-thinking.md) | Extended thinking, budget tokens, adaptive thinking (effort 1-5) |
| 04 | [04-tool-use.md](04-tool-use.md) | Tool use, tool_choice, parallel calls, tool search |
| 05 | [05-vision-multimodal.md](05-vision-multimodal.md) | Vision, изображения, PDF, подсчет токенов |
| 06 | [06-prompt-caching.md](06-prompt-caching.md) | Prompt caching, TTL, экономия |
| 07 | [07-structured-output.md](07-structured-output.md) | Структурированный вывод, JSON, citations |

### Практика

| # | Файл | Содержание |
|---|------|-----------|
| 08 | [08-prompt-engineering.md](08-prompt-engineering.md) | Промпт-инженерия для Claude, XML-теги, chain of thought |
| 09 | [09-python-sdk.md](09-python-sdk.md) | Python SDK: sync, async, streaming, error handling |

### Проект

| # | Файл | Содержание |
|---|------|-----------|
| 10 | [10-project-integration.md](10-project-integration.md) | Интеграция Claude с проектом «Интерпретация» |

### Оптимизация

| # | Файл | Содержание |
|---|------|-----------|
| 11 | [11-context-window-optimization.md](11-context-window-optimization.md) | Контекстное окно, usage/length лимиты, оптимизация расхода токенов |
| 12 | [12-query-optimization-protocol.md](12-query-optimization-protocol.md) | Протокол диспетчеризации: tier-система, маршрутизация моделей |

### Экосистема

| # | Файл | Содержание |
|---|------|-----------|
| 13 | [13-claude-code-skills-ecosystem.md](13-claude-code-skills-ecosystem.md) | Каталог скиллов, агентов, плагинов сообщества. 8 репозиториев, 55+ скиллов, бандлы по ролям |

---

## Быстрый старт

```python
import anthropic

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY из env

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Привет, Claude!"}
    ]
)

print(message.content[0].text)
```

---

## Ключевые характеристики Claude Opus 4.6

| Параметр | Значение |
|----------|----------|
| Model ID | `claude-opus-4-6` |
| Контекст (стандартный) | 200K tokens |
| Контекст (beta) | до 1M tokens |
| Максимальный выход | до 128K tokens |
| Input pricing (200K) | $5.00 / 1M tokens |
| Output pricing (200K) | $25.00 / 1M tokens |
| Input pricing (1M beta) | $10.00 / 1M tokens |
| Output pricing (1M beta) | $37.50 / 1M tokens |
| Дата выпуска | 5 февраля 2026 |

---

## Связанные документы проекта

- [10-token-and-cost-estimate.md](../10-token-and-cost-estimate.md) -- расчет стоимости на день симуляции
- [12-implementation-plan-mvp-and-scaling.md](../12-implementation-plan-mvp-and-scaling.md) -- план реализации MVP
- [15-agents_creation.md](../15-agents_creation.md) -- порядок создания агентов
