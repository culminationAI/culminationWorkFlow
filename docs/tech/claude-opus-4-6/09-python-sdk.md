# 09. Python SDK

> [!TIP]
> Верифицировано 2026-02-26. Источники: Context7 (anthropics/anthropic-sdk-python), PyPI.

---

## Установка

```bash
pip install anthropic
```

Требует Python 3.8+. API-ключ через переменную окружения:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Sync Client

```python
import anthropic

client = anthropic.Anthropic()  # берёт ANTHROPIC_API_KEY из env

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Привет!"}
    ]
)

print(message.content[0].text)
print(f"Tokens: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
```

---

## Async Client

```python
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def main():
    message = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Привет!"}
        ]
    )
    print(message.content[0].text)

asyncio.run(main())
```

---

## Streaming

### Sync streaming

```python
with client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Расскажи историю"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()

message = stream.get_final_message()
```

### Async streaming

```python
async with client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Расскажи историю"}]
) as stream:
    async for text in stream.text_stream:
        print(text, end="", flush=True)
    print()

message = await stream.get_final_message()
```

### Event-based streaming

```python
async with client.messages.stream(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Расскажи историю"}]
) as stream:
    async for event in stream:
        if event.type == "text":
            print(event.text, end="", flush=True)
        elif event.type == "content_block_stop":
            print(f"\n\nBlock finished: {event.content_block}")

accumulated = await stream.get_final_message()
```

---

## Error Handling

```python
import anthropic

client = anthropic.Anthropic()

try:
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}]
    )
except anthropic.APIConnectionError as e:
    print(f"Connection error: {e.__cause__}")
except anthropic.RateLimitError as e:
    print(f"Rate limited (429): {e.response}")
except anthropic.AuthenticationError as e:
    print(f"Authentication failed (401): {e.message}")
except anthropic.BadRequestError as e:
    print(f"Bad request (400): {e.message}")
except anthropic.APIStatusError as e:
    print(f"API error {e.status_code}: {e.message}")
```

### Иерархия исключений

```
anthropic.APIError
├── anthropic.APIConnectionError
└── anthropic.APIStatusError
    ├── anthropic.BadRequestError (400)
    ├── anthropic.AuthenticationError (401)
    ├── anthropic.PermissionDeniedError (403)
    ├── anthropic.NotFoundError (404)
    ├── anthropic.RateLimitError (429)
    └── anthropic.InternalServerError (500+)
```

---

## Retries и Timeouts

```python
import httpx
from anthropic import Anthropic

# Client-level defaults
client = Anthropic(
    max_retries=5,   # default: 2
    timeout=30.0     # default: 600s (10 min)
)

# Fine-grained timeout
client = Anthropic(
    timeout=httpx.Timeout(60.0, read=5.0, write=10.0, connect=2.0)
)

# Per-request override
message = client.with_options(
    max_retries=10,
    timeout=120.0
).messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## Extended Thinking в SDK

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[
        {"role": "user", "content": "Спланируй сцену..."}
    ]
)

for block in response.content:
    if block.type == "thinking":
        print(f"Thinking: {block.thinking[:200]}...")
    elif block.type == "text":
        print(f"Response: {block.text}")
```

---

## Tool Use в SDK

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=[
        {
            "name": "search_graph",
            "description": "Поиск по графу знаний Neo4j",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Cypher-запрос"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        }
    ],
    messages=[{"role": "user", "content": "Найди все связи героя"}]
)

for block in response.content:
    if block.type == "tool_use":
        print(f"Tool: {block.name}, Input: {block.input}")
```

---

## Batch API

Пакетная обработка со скидкой 50%:

```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"scene-{i}",
            "params": {
                "model": "claude-opus-4-6",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": f"Оцени сцену {i}"}]
            }
        }
        for i in range(10)
    ]
)

# Проверка статуса
status = client.messages.batches.retrieve(batch.id)
print(f"Status: {status.processing_status}")
```

---

## Типизация ответов

SDK предоставляет типизированные объекты:

```python
from anthropic.types import Message, TextBlock, ToolUseBlock, ThinkingBlock

message: Message = client.messages.create(...)

# Type narrowing
for block in message.content:
    match block.type:
        case "text":
            text_block: TextBlock = block
            print(text_block.text)
        case "tool_use":
            tool_block: ToolUseBlock = block
            print(tool_block.name, tool_block.input)
        case "thinking":
            think_block: ThinkingBlock = block
            print(think_block.thinking[:100])
```

---

## Паттерн для проекта «Интерпретация»

```python
import anthropic
import json
from typing import Any

client = anthropic.Anthropic()

async def call_agent(
    agent_name: str,
    system_prompt: str,
    context: dict[str, Any],
    output_schema: dict,
    model: str = "claude-opus-4-6",
    use_thinking: bool = False
) -> dict:
    """Унифицированный вызов агента проекта."""

    kwargs = {
        "model": model,
        "max_tokens": 4096,
        "system": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral", "ttl": "1h"}
            }
        ],
        "messages": [
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)}
        ],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": output_schema
            }
        }
    }

    if use_thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": 5000}

    async_client = anthropic.AsyncAnthropic()
    response = await async_client.messages.create(**kwargs)

    return json.loads(response.content[0].text)
```
