# 02. API Reference -- Messages API

> [!TIP]
> Верифицировано 2026-02-26. Источники: официальная документация Anthropic (docs.anthropic.com/en/api/messages), WebSearch.

---

## Endpoint

```
POST https://api.anthropic.com/v1/messages
```

---

## Аутентификация

Все запросы требуют HTTP-заголовок:

```
x-api-key: YOUR_API_KEY
anthropic-version: 2023-06-01
```

API-ключ создается в [Anthropic Console](https://console.anthropic.com/).

Переменная окружения для Python SDK:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Параметры запроса

### Обязательные

| Параметр | Тип | Описание |
|----------|-----|----------|
| `model` | string | Model ID: `claude-opus-4-6`, `claude-sonnet-4-6` и др. |
| `max_tokens` | integer | Максимальное количество выходных токенов. Opus 4.6: до 128K. |
| `messages` | array | Массив сообщений в формате `{"role": "user"|"assistant", "content": ...}` |

### Опциональные

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `system` | string или array | -- | Системный промпт. Может быть строкой или массивом блоков (для prompt caching). |
| `temperature` | float | 1.0 | Случайность генерации. Диапазон: 0.0-1.0. Для детерминированных задач -- 0.0. |
| `top_p` | float | -- | Nucleus sampling. Альтернатива temperature. Не рекомендуется использовать одновременно с temperature. |
| `top_k` | integer | -- | Ограничивает выборку top-K токенов. |
| `stop_sequences` | array[string] | -- | Последовательности, при которых генерация останавливается. |
| `stream` | boolean | false | Включает потоковую передачу ответа через Server-Sent Events. |
| `metadata` | object | -- | Метаданные запроса (например, `user_id` для отслеживания). |
| `tools` | array | -- | Определения инструментов для tool use. См. [04-tool-use.md](04-tool-use.md). |
| `tool_choice` | object | -- | Управление выбором инструментов: `auto`, `any`, `tool`, `none`. |
| `thinking` | object | -- | Конфигурация extended thinking. См. [03-extended-thinking.md](03-extended-thinking.md). |

---

## Формат сообщений

### Текстовое сообщение

```json
{
  "role": "user",
  "content": "Объясни концепцию GraphRAG"
}
```

### Сообщение с несколькими блоками контента

```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "Что изображено на этой картинке?"
    },
    {
      "type": "image",
      "source": {
        "type": "base64",
        "media_type": "image/jpeg",
        "data": "<base64_encoded_image>"
      }
    }
  ]
}
```

### Предзаполненный ответ ассистента (prefilled response)

```json
{
  "role": "assistant",
  "content": "{"name": ""
}
```

Используется для управления форматом вывода (например, начать JSON-ответ).

---

## Формат ответа

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "GraphRAG -- это подход..."
    }
  ],
  "model": "claude-opus-4-6",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 25,
    "output_tokens": 150,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0
  }
}
```

### Поля usage

| Поле | Описание |
|------|----------|
| `input_tokens` | Количество входных токенов (без кэша) |
| `output_tokens` | Количество выходных токенов |
| `cache_creation_input_tokens` | Токены, записанные в кэш (первый вызов) |
| `cache_read_input_tokens` | Токены, прочитанные из кэша |

### stop_reason

| Значение | Описание |
|----------|----------|
| `end_turn` | Модель завершила ответ естественным образом |
| `max_tokens` | Достигнут лимит `max_tokens` |
| `stop_sequence` | Встречена одна из `stop_sequences` |
| `tool_use` | Модель запрашивает вызов инструмента |

---

## Streaming

При `"stream": true` ответ передается через Server-Sent Events (SSE).

### Типы событий

| Событие | Описание |
|---------|----------|
| `message_start` | Начало сообщения, содержит метаданные |
| `content_block_start` | Начало блока контента (text или tool_use) |
| `content_block_delta` | Инкрементальное обновление текста (`text_delta`) или thinking (`thinking_delta`) |
| `content_block_stop` | Завершение блока контента |
| `message_delta` | Обновление метаданных сообщения (stop_reason, usage) |
| `message_stop` | Конец сообщения |
| `ping` | Keepalive-сигнал |

### Пример SSE-потока

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_...","type":"message","role":"assistant","content":[],"model":"claude-opus-4-6",...}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"GraphRAG"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" -- это"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":150}}

event: message_stop
data: {"type":"message_stop"}
```

---

## Batch API

Для массовых запросов Anthropic предоставляет Message Batches API, позволяющий отправить до 100,000 запросов за раз со скидкой 50% на pricing.

```
POST https://api.anthropic.com/v1/messages/batches
```

**Ключевые характеристики:**
- Обработка в течение 24 часов
- Скидка 50% на input и output tokens
- Каждый запрос в батче -- самостоятельный Messages API запрос
- Результаты доступны после завершения всего батча

### Пример

```json
{
  "requests": [
    {
      "custom_id": "request-1",
      "params": {
        "model": "claude-opus-4-6",
        "max_tokens": 1024,
        "messages": [
          {"role": "user", "content": "Опиши локацию: парк утром"}
        ]
      }
    },
    {
      "custom_id": "request-2",
      "params": {
        "model": "claude-opus-4-6",
        "max_tokens": 1024,
        "messages": [
          {"role": "user", "content": "Опиши локацию: офис днем"}
        ]
      }
    }
  ]
}
```

---

## Rate Limits

Rate limits зависят от тарифного плана и уровня использования (Usage Tier).

| Tier | Requests/min | Input tokens/min | Output tokens/min |
|------|-------------|-------------------|-------------------|
| Tier 1 | 50 | 40,000 | 8,000 |
| Tier 2 | 1,000 | 80,000 | 16,000 |
| Tier 3 | 2,000 | 160,000 | 32,000 |
| Tier 4 | 4,000 | 400,000 | 80,000 |

**Примечание:** точные значения tier limits могут отличаться. Актуальные лимиты доступны через заголовки ответа: `anthropic-ratelimit-requests-limit`, `anthropic-ratelimit-tokens-limit`.

### Заголовки rate limit в ответе

```
anthropic-ratelimit-requests-limit: 1000
anthropic-ratelimit-requests-remaining: 999
anthropic-ratelimit-requests-reset: 2026-02-26T12:00:00Z
anthropic-ratelimit-tokens-limit: 80000
anthropic-ratelimit-tokens-remaining: 79500
anthropic-ratelimit-tokens-reset: 2026-02-26T12:00:00Z
```

---

## Коды ошибок

| HTTP код | Тип | Описание |
|----------|-----|----------|
| 400 | `invalid_request_error` | Некорректный запрос (пропущены обязательные поля, неверный формат) |
| 401 | `authentication_error` | Невалидный API-ключ |
| 403 | `permission_error` | Нет доступа к ресурсу |
| 404 | `not_found_error` | Ресурс не найден |
| 429 | `rate_limit_error` | Превышен rate limit. Заголовок `retry-after` содержит время ожидания. |
| 500 | `api_error` | Внутренняя ошибка сервера |
| 529 | `overloaded_error` | API перегружен. Повторить позже. |

---

## Пример полного запроса (curl)

```bash
curl https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-opus-4-6",
    "max_tokens": 1024,
    "system": "Ты -- ассистент для анализа литературных произведений.",
    "messages": [
      {
        "role": "user",
        "content": "Проанализируй тему одиночества в романе \"Мастер и Маргарита\"."
      }
    ],
    "temperature": 0.7
  }'
```

---

## Ссылки

- [Messages API](https://docs.anthropic.com/en/api/messages)
- [Message Batches](https://docs.anthropic.com/en/api/creating-message-batches)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [Errors](https://docs.anthropic.com/en/api/errors)
