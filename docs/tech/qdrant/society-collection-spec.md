# Qdrant Collection Spec: `knowledge_society`

> Спецификация коллекции для домена `society` базы знаний проекта «Интерпретация».
> Версия: 1.0 | Дата: 2026-02-26 | Автор: Джордж (george)
>
> Коллекция обслуживает creator agent при семантическом поиске
> знаний о социуме для генерации сцен. Единица индексации — H2-секция (chunk)
> из файлов `docs/knowledge/society/01–12 + index.md`.

---

## 1. Collection DDL (Python Qdrant Client)

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

# --- Создание коллекции ---
# ВАЖНО: recreate_collection() deprecated с v1.10. Используем delete + create.
if client.collection_exists("knowledge_society"):
    client.delete_collection("knowledge_society")

client.create_collection(
    collection_name="knowledge_society",
    vectors_config={
        # Основной dense-вектор: multilingual-e5-large, 1024d, Cosine
        "semantic": models.VectorParams(
            size=1024,
            distance=models.Distance.COSINE,
            # on_disk=True  # включить при объёме > 10K чанков
        ),
    },
    # Квантование: INT8 даёт 4x экономию RAM при ~1% потере точности.
    # Для базы знаний (read-heavy, recall важнее скорости) — оптимальный выбор.
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True,  # квантованные индексы в RAM, сырые на диске
        ),
    ),
    # Payload на диске: база знаний read-heavy, payload большой (text ~1K токенов).
    # Экономит RAM без потери скорости поиска.
    on_disk_payload=True,
    hnsw_config=models.HnswConfigDiff(
        m=16,           # число связей на узел (стандарт для 1024d)
        ef_construct=200,  # точность построения графа (выше = точнее, медленнее build)
        # ef при поиске задаётся в query_points(search_params=...), не здесь
    ),
)

# --- Payload-индексы ---

# 1. domain — keyword, tenant-индекс.
#    Позволяет будущий переход к мультитенантной коллекции knowledge_all.
#    Пока коллекция моно-доменная, но индекс дёшев и полезен для фильтров.
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="domain",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=False,  # True только при мультитенантной схеме
    ),
)

# 2. subdomain — keyword. Фильтр по поддомену (structures, media, ideologies...).
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="subdomain",
    field_schema=models.PayloadSchemaType.KEYWORD,
)

# 3. file_number — integer. Фильтр по порядковому номеру файла (01–12).
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="file_number",
    field_schema=models.PayloadSchemaType.INTEGER,
)

# 4. chunk_index — integer. Порядковый номер чанка внутри файла (0-based).
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="chunk_index",
    field_schema=models.PayloadSchemaType.INTEGER,
)

# 5. keywords — keyword (массив). Поиск чанков по ключевым словам из frontmatter.
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="keywords",
    field_schema=models.PayloadSchemaType.KEYWORD,
)

# 6. chunk_heading — full-text. Полнотекстовый поиск по заголовкам H2-секций.
#    Ускоряет поиск когда creator agent знает точное название концепции.
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="chunk_heading",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.MULTILINGUAL,
        min_token_len=2,
        max_token_len=40,
        lowercase=True,
    ),
)

# 7. ingested_at — datetime. Для инвалидации кэша после переиндексации файлов.
client.create_payload_index(
    collection_name="knowledge_society",
    field_name="ingested_at",
    field_schema=models.PayloadSchemaType.DATETIME,
)
```

---

## 2. Payload Schema

Каждая точка (point) в коллекции соответствует одному H2-чанку из файла домена society.

| Поле | Тип | Индекс | Обязательное | Описание | Пример |
|------|-----|--------|--------------|----------|--------|
| `domain` | `string` | keyword | да | Домен знаний | `"society"` |
| `subdomain` | `string` | keyword | да | Поддомен из YAML frontmatter | `"social-movements"`, `"media"`, `"structures"` |
| `file_number` | `integer` | integer | да | Порядковый номер файла (01–12) | `12` |
| `file_name` | `string` | нет | да | Имя файла без пути | `"12-social-movements-and-change.md"` |
| `chunk_index` | `integer` | integer | да | Порядковый номер чанка в файле (0-based) | `0`, `3`, `7` |
| `chunk_heading` | `string` | full-text | да | Заголовок H2-секции (без `## `) | `"Теория ресурсной мобилизации"` |
| `text` | `string` | нет | да | Полный текст чанка (тело H2-секции) | `"Теория ресурсной мобилизации (Resource Mobilization Theory, RMT)..."` |
| `token_count` | `integer` | нет | нет | Приблизительное число токенов в чанке | `720` |
| `keywords` | `string[]` | keyword | да | Ключевые слова из YAML frontmatter файла | `["социальные движения", "social movements", "революции"]` |
| `related` | `string[]` | нет | нет | Связанные файлы из frontmatter | `["society/03-power-and-inequality.md", "psychology/06-social-psychology.md"]` |
| `sources` | `string[]` | нет | нет | Список источников из frontmatter | `["McCarthy & Zald (1977) American Journal of Sociology"]` |
| `type` | `string` | нет | да | Тип документа (из frontmatter или default) | `"reference"` |
| `level` | `integer` | нет | нет | Таксономический уровень (1=ядро, 2=мир, 3=наука) | `2` |
| `version` | `string` | нет | нет | Версия файла из frontmatter | `"1.0"` |
| `ingested_at` | `datetime` | datetime | да | Время загрузки чанка в Qdrant (UTC ISO 8601) | `"2026-02-26T12:00:00Z"` |

### Заметки по схеме

**Поля с непоследовательным наличием в frontmatter.** Анализ файлов домена выявил несоответствие: `file_number` и `level` присутствуют в `12-social-movements-and-change.md`, но отсутствуют в `01-social-structures.md` и `06-media-and-information.md`. При загрузке loader должен:
- `file_number` — извлекать из имени файла (`int("06-media...".split("-")[0])`) если отсутствует в frontmatter;
- `level` — ставить дефолт `2` (все файлы `society` — уровень 2 по таксономии knowledge base).

**Текст чанка (`text`).** Включает весь контент H2-секции включая таблицы, списки, код. Не включает заголовок (он в `chunk_heading`). Размер: 500–1000 токенов согласно стандарту базы знаний.

**Эмбеддинг.** Модель `multilingual-e5-large` требует префикс `"query: "` для поисковых запросов и `"passage: "` при индексации. Loader добавляет `"passage: "` к `chunk_heading + "\n\n" + text` перед encode.

---

## 3. Индексы — сводная таблица

| Поле | Тип индекса | Зачем |
|------|------------|-------|
| `domain` | keyword | Готовность к мультидоменной коллекции; фильтр `domain=society` |
| `subdomain` | keyword | Фильтр по тематическому блоку (например, только `media` или `ideologies`) |
| `file_number` | integer | Точечная выборка по конкретному файлу; range-запросы |
| `chunk_index` | integer | Восстановление порядка чанков; пагинация по файлу |
| `keywords` | keyword | Фильтр по ключевым словам (массив строк) |
| `chunk_heading` | full-text (multilingual) | Поиск по точному названию концепции без эмбеддинга |
| `ingested_at` | datetime | Инвалидация после переиндексации; audit trail |

**Поля без индекса:** `text`, `related`, `sources`, `version`, `token_count`, `level`, `file_name`, `type`.
Они нужны creator agent'у только в `with_payload=True` ответе, не как фильтры.

---

## 4. Примеры запросов creator agent'а

### Запрос 1. Базовый семантический поиск по теме сцены

Creator agent генерирует сцену с протестом — ищет знания о социальных движениях.

```python
from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(url="http://localhost:6333")

# query_embedding — вектор от multilingual-e5-large с префиксом "query: "
query_embedding = encode("query: коллективное действие протест мобилизация движение")

results = client.query_points(
    collection_name="knowledge_society",
    query=query_embedding,
    using="semantic",
    limit=5,
    with_payload=True,
    search_params=models.SearchParams(
        hnsw_ef=128,
        quantization=models.QuantizationSearchParams(
            rescore=True,       # переоценка сырыми векторами после кандидатов
            oversampling=1.5,   # достаём 1.5x кандидатов для ресcore
        ),
    ),
)

for p in results.points:
    print(f"[{p.score:.3f}] {p.payload['chunk_heading']}")
    print(f"  File: {p.payload['file_name']}, Chunk: {p.payload['chunk_index']}")
```

**Ожидаемый результат:** топ-5 чанков из `12-social-movements-and-change.md` — секции о теории ресурсной мобилизации, коллективном действии, фреймах.

---

### Запрос 2. Фильтр по поддомену + семантика

Creator agent ищет только знания о медиа (для персонажа-журналиста), исключая политические идеологии.

```python
results = client.query_points(
    collection_name="knowledge_society",
    query=encode("query: пропаганда манипуляция информация постправда"),
    using="semantic",
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="subdomain",
                match=models.MatchValue(value="media"),
            ),
        ]
    ),
    limit=4,
    with_payload=True,
)
```

**Ожидаемый результат:** чанки исключительно из `06-media-and-information.md`.

---

### Запрос 3. Фильтр по массиву keywords (MatchAny)

Creator agent знает точную концепцию, которая нужна — ищет чанки с ключевым словом «Бурдьё» для сцены о культурном капитале.

```python
results = client.query_points(
    collection_name="knowledge_society",
    query=encode("query: культурный капитал социальное поле Бурдьё"),
    using="semantic",
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="keywords",
                match=models.MatchAny(any=["Бурдьё", "Bourdieu"]),
            ),
        ]
    ),
    limit=5,
    with_payload=True,
)
```

**Ожидаемый результат:** чанки из `01-social-structures.md`, `02-culture-and-identity.md`, `03-power-and-inequality.md` — все файлы где Бурдьё упомянут в frontmatter keywords.

---

### Запрос 4. Составной фильтр: несколько файлов + семантика + минимальный порог

Creator agent строит исторический контекст персонажа из 1970-х — ищет знания о власти, классах и революциях, но исключает спорт и религию.

```python
results = client.query_points(
    collection_name="knowledge_society",
    query=encode("query: классовая борьба власть государство революция неравенство"),
    using="semantic",
    query_filter=models.Filter(
        must_not=[
            models.FieldCondition(
                key="file_number",
                match=models.MatchAny(any=[10, 11]),  # исключить sport, religion
            ),
        ],
        must=[
            models.FieldCondition(
                key="domain",
                match=models.MatchValue(value="society"),
            ),
        ],
    ),
    score_threshold=0.72,   # отсечь нерелевантные чанки
    limit=6,
    with_payload=["chunk_heading", "file_name", "chunk_index", "text"],
    # with_payload как список — возвращаем только нужные поля, экономим токены
)
```

**Ожидаемый результат:** чанки из файлов 01, 03, 07, 12 — стратификация, власть, идеологии, революции.

---

## 5. Примечания по batch upload

### Объём данных

| Параметр | Оценка |
|---------|--------|
| Файлов в домене | 13 (12 + index.md) |
| Средних H2-секций на файл | ~6–8 |
| Итого чанков | ~80–100 |
| Размер вектора | 1024 float32 = 4 096 байт |
| Суммарный объём векторов | ~400 KB (без квантования) |
| С INT8 квантованием | ~100 KB в RAM |

Домен `society` — небольшой. Весь batch загружается одним вызовом `upsert`.

### Стратегия индексации чанка

```python
# Псевдокод логики разбивки файла на чанки при загрузке.
# Реализацию (loader script) делает Михей по этой спецификации.

import uuid
import re
from datetime import datetime, timezone

def file_to_points(file_path: str, frontmatter: dict, raw_content: str) -> list:
    """
    Разбивает markdown-файл на H2-чанки и формирует payload для Qdrant.
    Правило разбивки: каждый H2-заголовок (## ...) — отдельный чанк.
    Контент index.md индексируется как один чанк (нет H2-секций с контентом).
    """
    # Извлечь file_number из имени файла если нет в frontmatter
    file_number_str = file_path.split("/")[-1].split("-")[0]
    file_number = int(file_number_str) if file_number_str.isdigit() else 0

    # Разбивка по H2-заголовкам
    sections = re.split(r'\n(?=## )', raw_content.strip())
    points = []

    for idx, section in enumerate(sections):
        lines = section.split("\n", 1)
        heading = lines[0].lstrip("# ").strip() if lines else ""
        body = lines[1].strip() if len(lines) > 1 else ""

        if not body:
            continue  # пропускаем пустые секции (например, "Связанные документы")

        # Текст для эмбеддинга: "passage: <заголовок>\n\n<тело>"
        embed_text = f"passage: {heading}\n\n{body}"
        vector = encode(embed_text)  # multilingual-e5-large

        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector={"semantic": vector},
                payload={
                    "domain":         frontmatter.get("domain", "society"),
                    "subdomain":      frontmatter.get("subdomain", "general"),
                    "file_number":    frontmatter.get("file_number", file_number),
                    "file_name":      file_path.split("/")[-1],
                    "chunk_index":    idx,
                    "chunk_heading":  heading,
                    "text":           body,
                    "token_count":    len(body.split()),  # приблизительно
                    "keywords":       frontmatter.get("keywords", []),
                    "related":        frontmatter.get("related", []),
                    "sources":        frontmatter.get("sources", []),
                    "type":           frontmatter.get("type", "reference"),
                    "level":          frontmatter.get("level", 2),
                    "version":        str(frontmatter.get("version", "1.0")),
                    "ingested_at":    datetime.now(timezone.utc).isoformat(),
                },
            )
        )

    return points


# Batch upsert: все ~100 чанков — один вызов (домен небольшой)
all_points = []
for file_path in society_files:
    frontmatter, content = parse_frontmatter(file_path)
    all_points.extend(file_to_points(file_path, frontmatter, content))

# Upsert пакетом
client.upsert(
    collection_name="knowledge_society",
    points=all_points,
    # wait=True — ждём подтверждения записи (важно при первичной загрузке)
    wait=True,
)
```

### Переиндексация (при обновлении файлов)

Стратегия: **full re-upload** (не partial update).

Обоснование: домен `society` мал (~100 чанков), граница изменённых чанков неочевидна при правке H2-секций, full re-upload занимает < 5 секунд. Partial update оправдан только при > 10K чанков.

```python
# Безопасная переиндексация: delete all + re-upload
# (не delete_collection, чтобы не потерять индексы)
client.delete(
    collection_name="knowledge_society",
    points_selector=models.FilterSelector(
        filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="domain",
                    match=models.MatchValue(value="society"),
                ),
            ]
        )
    ),
)
# Затем — upsert всех чанков заново
```

### HNSW ef при поиске

Для базы знаний (recall > latency) рекомендуемые параметры поиска:

| Режим | `hnsw_ef` | `rescore` | Описание |
|-------|-----------|-----------|----------|
| Быстрый (draft) | 64 | False | Черновая генерация, допустима потеря ~2% recall |
| Стандартный | 128 | True | Основной режим creator agent'а |
| Точный (review) | 256 | True | Coherence Review, когда нужна максимальная полнота |

---

## 6. Связанные документы

- [docs/tech/qdrant/01-concepts.md](01-concepts.md) — базовые концепции Qdrant
- [docs/tech/qdrant/02-search-and-filtering.md](02-search-and-filtering.md) — фильтрация и Query API
- [docs/tech/qdrant/03-optimization.md](03-optimization.md) — HNSW и квантование
- [docs/tech/qdrant/06-client-libraries.md](06-client-libraries.md) — Python SDK
- [docs/knowledge/society/index.md](../../knowledge/society/index.md) — карта домена society
