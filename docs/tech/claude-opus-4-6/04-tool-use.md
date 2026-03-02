# 04. Tool Use (Function Calling)

> [!TIP]
> Верифицировано 2026-02-26. Источники: официальная документация Anthropic, WebSearch.

---

## Концепция

Tool use позволяет Claude вызывать внешние функции (инструменты) для получения информации или выполнения действий. Модель не вызывает функции напрямую -- она генерирует запрос на вызов, а ваш код выполняет вызов и возвращает результат.

### Цикл взаимодействия

1. **Вы** отправляете запрос с определениями инструментов и сообщением пользователя
2. **Claude** анализирует запрос и решает, нужен ли инструмент
3. **Claude** возвращает `tool_use` блок с именем инструмента и параметрами
4. **Вы** выполняете функцию и возвращаете результат как `tool_result`
5. **Claude** формирует финальный ответ на основе результата

---

## Определение инструментов

```json
{
  "tools": [
    {
      "name": "get_hero_state",
      "description": "Получает текущее эмоциональное и физическое состояние героя из графа Neo4j. Вызывайте перед генерацией действий или реплик.",
      "input_schema": {
        "type": "object",
        "properties": {
          "hero_id": {
            "type": "string",
            "description": "Уникальный идентификатор героя в графе"
          },
          "state_types": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Типы состояний: emotions, physical, cognitive, social, will"
          }
        },
        "required": ["hero_id"]
      }
    }
  ]
}
```

### Поля определения

| Поле | Тип | Обязательно | Описание |
|------|-----|------------|----------|
| `name` | string | Да | Имя инструмента. Латиница, цифры, подчеркивания. Макс. 64 символа. |
| `description` | string | Да | Описание: что делает, когда вызывать. Чем подробнее -- тем лучше модель определяет, когда использовать. |
| `input_schema` | object | Да | JSON Schema параметров инструмента. |

**Важно для описания:** включайте в description не только "что делает", но и "когда вызывать" и "что не делает". Это существенно влияет на точность вызовов.

---

## tool_choice

Управляет поведением выбора инструментов:

| Значение | Описание |
|----------|----------|
| `{"type": "auto"}` | Модель сама решает, использовать ли инструмент (по умолчанию) |
| `{"type": "any"}` | Модель обязана использовать хотя бы один инструмент |
| `{"type": "tool", "name": "get_hero_state"}` | Модель обязана использовать указанный инструмент |
| `{"type": "none"}` | Модель не может использовать инструменты (даже если они определены) |

---

## Формат ответа с tool_use

Когда Claude решает использовать инструмент, `stop_reason` будет `"tool_use"`:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Мне нужно проверить состояние героя."
    },
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lqs136",
      "name": "get_hero_state",
      "input": {
        "hero_id": "hero_venus",
        "state_types": ["emotions", "physical"]
      }
    }
  ],
  "stop_reason": "tool_use"
}
```

### Возврат результата

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lqs136",
      "content": "Эмоции: тревожность 7/10, грусть 4/10. Физическое: усталость 6/10, голод 3/10."
    }
  ]
}
```

### Ошибка инструмента

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01A09q90qw90lq917835lqs136",
  "is_error": true,
  "content": "Герой с id 'hero_venus' не найден в графе."
}
```

---

## Параллельные вызовы инструментов

Claude может возвращать несколько `tool_use` блоков в одном ответе:

```json
{
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01...",
      "name": "get_hero_state",
      "input": {"hero_id": "hero_venus"}
    },
    {
      "type": "tool_use",
      "id": "toolu_02...",
      "name": "get_location",
      "input": {"location_id": "loc_apartment"}
    }
  ],
  "stop_reason": "tool_use"
}
```

В этом случае нужно вернуть результаты для всех вызовов:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01...",
      "content": "Состояние героя: ..."
    },
    {
      "type": "tool_result",
      "tool_use_id": "toolu_02...",
      "content": "Локация: квартира, утро, тишина..."
    }
  ]
}
```

---

## Tool Search

При большом количестве инструментов (десятки или сотни) передача всех определений в каждом запросе расходует значительную часть контекста. Tool search позволяет Claude самостоятельно искать нужный инструмент из большого каталога.

**Экономия:** до ~191K tokens при наличии сотен инструментов.

**Примечание:** конкретный API tool search требует уточнения по официальной документации Anthropic. На момент написания этот функционал доступен как beta-фича.

---

## Computer Use

Claude может взаимодействовать с компьютером через набор специальных инструментов:

- `computer` -- скриншот, клик, ввод текста
- `text_editor` -- редактирование файлов
- `bash` -- выполнение команд

**Примечание:** Computer use -- beta-фича, актуальные параметры уточняйте по официальной документации.

---

## Пример на Python

```python
import anthropic
import json

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_graph",
        "description": "Выполняет Cypher-запрос к графу Neo4j и возвращает результат. Используйте для получения данных о герое, NPC, локациях и их связях.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Cypher-запрос к Neo4j"
                },
                "params": {
                    "type": "object",
                    "description": "Параметры запроса (для параметризованных запросов)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "update_emotion",
        "description": "Обновляет вес эмоционального ребра героя в графе. Вызывайте когда действие или событие изменяет эмоциональное состояние.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hero_id": {"type": "string"},
                "emotion": {"type": "string"},
                "weight": {
                    "type": "number",
                    "minimum": -10,
                    "maximum": 10
                }
            },
            "required": ["hero_id", "emotion", "weight"]
        }
    }
]

# Первый вызов
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "Определи, как Венера реагирует на звонок будильника. Сначала проверь её состояние."
        }
    ]
)

# Обработка tool_use
if message.stop_reason == "tool_use":
    tool_use_block = next(b for b in message.content if b.type == "tool_use")

    # Выполнение инструмента (здесь -- заглушка)
    tool_result = execute_tool(tool_use_block.name, tool_use_block.input)

    # Отправка результата обратно
    follow_up = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        tools=tools,
        messages=[
            {"role": "user", "content": "Определи, как Венера реагирует на звонок будильника."},
            {"role": "assistant", "content": message.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": json.dumps(tool_result)
                    }
                ]
            }
        ]
    )

    print(follow_up.content[0].text)
```

---

## Best Practices

1. **Описания инструментов.** Пишите подробные description: что делает, когда вызывать, что НЕ делает. Модель использует description как основной сигнал для выбора.

2. **Типизация параметров.** Используйте JSON Schema полностью: enum, minimum/maximum, pattern. Чем строже схема -- тем точнее вызовы.

3. **Обработка ошибок.** Всегда возвращайте `tool_result`, даже при ошибке (используйте `is_error: true`). Если не вернуть результат -- API вернет ошибку.

4. **Количество инструментов.** До ~20 инструментов модель справляется хорошо. При 50+ рассмотрите tool search или группировку по контексту.

5. **tool_choice.** Используйте `{"type": "tool", "name": "..."}` когда точно знаете, какой инструмент нужен. Это экономит токены (модель не тратит время на "размышление о выборе").

---

## Применение в проекте «Интерпретация»

Каждый агент использует свой набор инструментов:

| Агент | Инструменты |
|-------|------------|
| Внутреннее | `query_graph` (подграф героя), `load_memories` |
| Мониторинг | `get_states`, `update_emotion`, `update_physical` |
| Сеттинг | `get_location`, `get_objects` |
| Население | `get_npcs`, `get_npc_profile` |
| Действие | `query_graph`, `update_emotion`, `create_node` |
| Летописец | `write_beat`, `write_scene_text` |

Общие инструменты: `query_graph` (чтение графа), `search_vectors` (поиск в Qdrant).

---

## Ссылки

- [Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Computer Use](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)
