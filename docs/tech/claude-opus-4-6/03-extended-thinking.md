# 03. Extended Thinking

> [!TIP]
> Верифицировано 2026-02-26. Источники: официальная документация Anthropic, WebSearch.

---

## Что такое Extended Thinking

Extended thinking -- режим работы Claude, при котором модель выполняет внутреннюю цепочку рассуждений ("thinking") перед генерацией финального ответа. Thinking-блоки видны в ответе API, но не отображаются конечному пользователю по умолчанию.

**Зачем:** сложные задачи (математика, код, многошаговый анализ, планирование) выигрывают от того, что модель "думает" перед ответом. Extended thinking значительно повышает качество на таких задачах.

---

## Активация

Extended thinking активируется параметром `thinking` в запросе:

```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 16000,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 10000
  },
  "messages": [
    {"role": "user", "content": "Реши эту задачу..."}
  ]
}
```

### Параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `thinking.type` | string | `"enabled"` для включения extended thinking |
| `thinking.budget_tokens` | integer | Максимальное количество токенов на thinking. Минимум: 1024. |

**Важно:** `budget_tokens` входит в общий `max_tokens`. Например, если `max_tokens=16000` и `budget_tokens=10000`, то на финальный ответ остается до 6000 токенов.

---

## Budget Tokens -- рекомендации

| Сложность задачи | Рекомендуемый budget | Пример |
|-----------------|---------------------|---------|
| Простая | 1024-2048 | Классификация, форматирование |
| Средняя | 4000-8000 | Анализ текста, рефакторинг кода |
| Сложная | 10000-20000 | Математические доказательства, архитектурные решения |
| Очень сложная | 20000-50000 | Многошаговые исследования, сложный дебаг |

**Правило:** модель может использовать меньше токенов, чем выделено. Budget -- это верхняя граница, а не фиксированное количество.

---

## Формат ответа с thinking

При включенном thinking ответ содержит блоки двух типов:

```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Мне нужно проанализировать эту задачу пошагово...\n\n1. Сначала определю входные данные...\n2. Затем применю алгоритм..."
    },
    {
      "type": "text",
      "text": "Решение задачи: ..."
    }
  ]
}
```

### Порядок блоков

1. Один или несколько `thinking` блоков
2. Финальный `text` блок (или `tool_use` блок)

Thinking-блоки всегда идут перед финальным ответом.

---

## Streaming thinking

При streaming thinking-блоки передаются через `thinking_delta`:

```
event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"thinking","thinking":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"Рассмотрим "}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"задачу..."}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: content_block_start
data: {"type":"content_block_start","index":1,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":1,"delta":{"type":"text_delta","text":"Ответ: ..."}}
```

---

## Adaptive Thinking (effort levels)

Adaptive thinking позволяет управлять глубиной рассуждений через параметр `effort`:

```json
{
  "model": "claude-opus-4-6",
  "max_tokens": 16000,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 10000,
    "effort": "high"
  },
  "messages": [...]
}
```

### Уровни effort

| Уровень | Значение | Описание | Когда использовать |
|---------|----------|----------|-------------------|
| 1 | `"low"` | Минимальное рассуждение | Простые задачи, форматирование |
| 2 | `"medium_low"` | Легкое рассуждение | Классификация, извлечение данных |
| 3 | `"medium"` | Стандартное рассуждение | Анализ, суммаризация |
| 4 | `"high"` | Глубокое рассуждение | Кодирование, сложный анализ |
| 5 | `"max"` | Максимальное рассуждение | Математика, исследования |

**Как работает:** при низком effort модель использует меньше thinking-токенов, отвечает быстрее и дешевле. При высоком -- исследует задачу тщательнее.

---

## Ограничения

1. **Не все модели поддерживают thinking.** Extended thinking доступен для Opus 4.6 и Sonnet 4.6. Для Haiku 4.5 -- нет.

2. **Temperature с thinking.** При включенном thinking значение `temperature` должно быть 1.0 (значение по умолчанию). Изменение temperature при включенном thinking может вызвать ошибку.

3. **Thinking-блоки нельзя передать обратно.** В отличие от текстовых блоков assistant, thinking-блоки не должны включаться в следующие сообщения conversation.

4. **Prompt caching и thinking.** System prompt и tools кэшируются как обычно. Thinking-токены не кэшируются.

---

## Когда использовать

**Используйте extended thinking для:**
- Математических задач и логических головоломок
- Сложного кода и дебага
- Многошагового анализа документов
- Планирования архитектуры
- Задач с неочевидным решением

**Не используйте для:**
- Простых ответов на вопросы
- Форматирования и переформатирования текста
- Извлечения данных из структурированного текста
- Задач, где скорость ответа критична

---

## Пример на Python

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[
        {
            "role": "user",
            "content": "Спроектируй оптимальную схему Neo4j для хранения эмоциональных состояний персонажа с 38 типами эмоций и затуханием весов."
        }
    ]
)

for block in message.content:
    if block.type == "thinking":
        print(f"[THINKING]\n{block.thinking}\n")
    elif block.type == "text":
        print(f"[ANSWER]\n{block.text}")
```

---

## Применение в проекте «Интерпретация»

| Агент | Extended thinking | Effort | Обоснование |
|-------|------------------|--------|-------------|
| Драматург | Да | high | Сложное планирование нарратива |
| Внутреннее | Да | high | Глубокий анализ психологии персонажа |
| Судьба | Да | medium | Выбор интеррапта требует анализа |
| Действие | Да | medium | Определение инициатора и цепочки |
| Верификатор | Нет | -- | Проверка по чеклисту, не рассуждение |
| Хронос | Нет | -- | Простое объявление времени |
| Летописец | Опционально | medium_low | Генерация текста, не анализ |

**Экономия:** отключение thinking для простых агентов экономит ~30% токенов на сцену.

---

## Ссылки

- [Extended Thinking](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)
