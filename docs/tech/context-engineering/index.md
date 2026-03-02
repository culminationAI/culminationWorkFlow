> [!CAUTION]
> Создано Manus/Gemini без верификации. Наиболее ценная коллекция, основана на реальном Google whitepaper (Nov 2025).

# Context Engineering: Sessions & Memory (Ultimate Reference)

Этот многотомный справочник базируется на фундаментальном исследовании Google (Nov 2025) по созданию интеллектуальных, стейтфул (stateful) AI-агентов. Мы декомпозировали 71 страницу технической документации в прикладное руководство для проекта «Интерпретация».

## 🗺 Карта обучения

### 1. Фундамент и Проблематика
- **[01-introduction-and-core-problem.md](01-introduction-and-core-problem.md)**: Почему ванильные LLM — это «золотые рыбки» и что такое Context Rot.
- **[02-sessions-deep-dive.md](02-sessions-deep-dive.md)**: Настоящая рабочая память. История, События и Мультиагентные сессии.

### 2. Управление объемом
- **[03-context-compaction-strategies.md](03-context-compaction-strategies.md)**: Математика сжатия. Суммаризация, Прунинг (обрезка) и Трейд-оффы производительности.

### 3. Анатомия Долгосрочной Памяти
- **[04-memory-taxonomy.md](04-memory-taxonomy.md)**: Классификация памяти (Episodic, Semantic, Procedural, Fact, Experiential).
- **[05-memory-etl-extraction.md](05-memory-etl-extraction.md)**: Процесс извлечения. Как агент «слышит» важное в потоке слов.
- **[06-memory-etl-consolidation.md](06-memory-etl-consolidation.md)**: Консолидация и Происхождение (Provenance). Как очищать и объединять воспоминания.

### 4. Инженерная реализация
- **[07-storage-architectures.md](07-storage-architectures.md)**: Архитектуры хранения. Векторные БД vs Графы Знаний (RAG vs GraphRAG).
- **[08-memory-as-a-tool.md](08-memory-as-a-tool.md)**: Память как инструмент. Самозапускаемый поиск и стратегии инференса.

### 5. Продакшн и Качество
- **[09-testing-and-evaluation.md](09-testing-and-evaluation.md)**: Как измерить «качество воспоминаний» и точность воспроизведения.
- **[10-security-and-production.md](10-security-and-production.md)**: Безопасность данных, PII и масштабирование на миллионы сессий.

### 6. Специфика Проекта
- **[11-project-integration-graph-temporal.md](11-project-integration-graph-temporal.md)**: Практическое внедрение в «Интерпретацию» через Neo4j (Temporal Graph) и Qdrant.

---
*Статус: Ultimate Reference v2.0 (Февраль 2026) — на основе Google Research Whitepaper (71 p.)*
