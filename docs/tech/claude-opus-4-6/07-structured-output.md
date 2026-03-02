# 07. Structured Output

> [!TIP]
> Верифицировано 2026-02-26. Источники: Context7 (platform.claude.com — structured outputs, citations).

---

## Способы получения структурированного вывода

Claude поддерживает несколько способов получения JSON и других структурированных форматов:

| Способ | Гарантия JSON | Гарантия схемы | Рекомендация |
|--------|:-------------:|:--------------:|-------------|
| `output_config.format` (JSON Schema) | Да | Да | **Рекомендуется** для строгого JSON |
| Tool use (`strict: true`) | Да | Да | Когда нужен вызов функций |
| System prompt + инструкции | Нет | Нет | Простые случаи |
| Prefilled assistant | Нет | Нет | Legacy, несовместим с JSON outputs |

---

## JSON Outputs (output_config.format)

Наиболее надёжный способ — `output_config` с JSON Schema:

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Опиши эмоциональное состояние героя после ссоры"}
    ],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "primary_emotion": {"type": "string"},
                    "intensity": {"type": "number", "minimum": 0, "maximum": 1},
                    "triggers": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "behavioral_response": {"type": "string"}
                },
                "required": ["primary_emotion", "intensity", "triggers", "behavioral_response"],
                "additionalProperties": False
            }
        }
    }
)

import json
result = json.loads(response.content[0].text)
```

### Совместимость

| Фича | Совместимость с JSON outputs |
|------|:----------------------------:|
| Batch API | Да |
| Streaming | Да |
| Token counting | Да |
| Strict tool use | Да (можно совмещать) |
| Citations | **Нет** (400 error) |
| Message Prefilling | **Нет** |

---

## Strict Tool Use

Альтернативный способ — определить "инструмент" с нужной JSON-схемой и заставить Claude его вызвать:

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    tool_choice={"type": "tool", "name": "extract_character_state"},
    tools=[
        {
            "name": "extract_character_state",
            "description": "Извлеки эмоциональное состояние персонажа",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "emotion": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["emotion", "confidence"],
                "additionalProperties": False
            }
        }
    ],
    messages=[
        {"role": "user", "content": "Герой вернулся домой и обнаружил пустую квартиру..."}
    ]
)

# Результат в tool_use content block
tool_input = response.content[0].input  # {"emotion": "тревога", "confidence": 0.85}
```

---

## Комбинирование JSON Outputs + Strict Tools

Можно использовать оба подхода в одном запросе:

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Спланируй следующую сцену"}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "next_steps": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["summary", "next_steps"],
                "additionalProperties": False
            }
        }
    },
    tools=[
        {
            "name": "search_graph",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "depth": {"type": "integer"}
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    ]
)
```

---

## Citations

Citations позволяют Claude ссылаться на конкретные части входных документов. **Несовместимы с `output_config.format`.**

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": "Героя зовут Иван. Ему 34 года. Он работает инженером."
                    },
                    "title": "Профиль героя",
                    "citations": {"enabled": True}
                },
                {
                    "type": "text",
                    "text": "Кто такой герой и чем он занимается?"
                }
            ]
        }
    ]
)

# Ответ содержит citations с ссылками на исходный текст
for block in response.content:
    if hasattr(block, 'citations') and block.citations:
        for cite in block.citations:
            print(f"Cited: {cite.cited_text}")
```

---

## Применение в проекте «Интерпретация»

Агенты проекта интенсивно используют структурированный вывод:

| Агент | Формат вывода | Способ |
|-------|--------------|--------|
| Внутреннее | JSON (эмоции, мысли) | `output_config` JSON Schema |
| Драматург | JSON (оценка, правки) | `output_config` JSON Schema |
| Верификатор | JSON (checklist) | Strict tool use |
| Хронос | JSON (время, события) | `output_config` JSON Schema |
| Летописец | Text + citations | Citations API |
