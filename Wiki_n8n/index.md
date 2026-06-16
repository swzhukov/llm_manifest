# n8n Wiki — База знаний по n8n

> Собрано из 10 тредов форума (Q3 2025 — Q1 2026) и расширено. Источник — практические уроки и живое обсуждение в чате `n8node` под руководством George Erman (Георгий Эрман).

## Как пользоваться

1. **Ты учишься n8n с нуля** — иди в [00-quick-reference.md](00-quick-reference.md), потом [01-installation.md](01-installation.md) → [02-interface-and-nodes.md](02-interface-and-nodes.md).
2. **Ты делаешь конкретную задачу** — посмотри [index-by-task.md](index-by-task.md) (оглавление по типу задачи).
3. **У тебя упало / не работает** — иди в [10-common-errors.md](10-common-errors.md).
4. **Ты — Mavis / LLM-агент** — прочитай [alignment-with-skill-loader.md](alignment-with-skill-loader.md) — там разбор применимости к [wiki-loader SKILL.md](https://github.com/swzhukov/llm_manifest/blob/main/skills/wiki-loader/SKILL.md).

## Оглавление

### Основы

- [00-quick-reference.md](00-quick-reference.md) — шпаргалка по нодам, триггерам, типичным схемам
- [01-installation.md](01-installation.md) — установка n8n через `n8n-installer` (Юрий Косаковский), обновление, .env, нюансы
- [02-interface-and-nodes.md](02-interface-and-nodes.md) — UI, холст, ноды, триггеры vs экшены, стикеры
- [03-workflow-settings.md](03-workflow-settings.md) — Settings workflow: Execution Order, error workflow, очистка execution, timezone
- [04-error-handling.md](04-error-handling.md) — error workflow, error trigger, retry-паттерны, нюанс «chat not found»

### Хранилища и память

- [05-supabase.md](05-supabase.md) — установка рядом с n8n, SQL-схемы, секреты, фильтрация
- [06-vector-memory-rag.md](06-vector-memory-rag.md) — векторная память, RAG, эмбеддинги, чанки, overlap, метаданные

### Интеграции

- [07-telegram-bots.md](07-telegram-bots.md) — Telegram Trigger, inline-кнопки, callback_data, user-bots, polling vs webhook
- [08-yandex-gpt.md](08-yandex-gpt.md) — Yandex Cloud, сервисный аккаунт, OpenAI-совместимый endpoint, экономика
- [09-ai-agents.md](09-ai-agents.md) — AI Agent, temperature для RAG, инструменты, каскад IF, токены и расходы

### Снапшоты знаний

- [10-common-errors.md](10-common-errors.md) — 20+ задокументированных ошибок из чата с корневыми причинами
- [11-best-practices.md](11-best-practices.md) — проверенные паттерны, анти-паттерны, экономия места
- [12-system-prompts.md](12-system-prompts.md) — реальные промпты из уроков: SEO-копирайтер, техподдержка RAG
- [alignment-with-skill-loader.md](alignment-with-skill-loader.md) — cross-reference с wiki-loader SKILL.md + MISTAKES/ENVIRONMENT

### Архив

- [archive/forum-threads-map.md](archive/forum-threads-map.md) — карта 10 CSV-тредов: кто, когда, про что

## Конвенции wiki

- **«Из урока N»** — цитата из курса George Erman (главный курс в `631396a6__...csv`).
- **«Из чата»** — наблюдение из живого обсуждения (`040508f4`, `0c07158d`, `671fdf61` и т. д.).
- **«⚠️ Подводный камень»** — то, что ровно сожрёт тебе время, если заранее не знать.
- **«✅ Best practice»** — отработанное решение, рекомендуемое сообществом.
- Ссылки `[ENVIRONMENT.md §X.Y]` и `[MISTAKES.md §X.Y]` указывают на `swzhukov/llm_manifest` — wiki-loader автоматически подтягивает их в контекст.

## Источники

| CSV | Что внутри | Период |
|---|---|---|
| `631396a6__...csv` | Основной курс «Для начинающих» + Supabase + RAG | 09.2025 – 10.2025 |
| `040508f4__...csv` | Живая установка n8n+Supabase+YandexGPT на Beget | 10.2025 |
| `317ec5bc__...csv` | Telegram: голосовой ввод и др. | 10.2025 – 11.2025 |
| `3afa20f4__...csv` | Расширенный курс, узлы | 11.2025 |
| `b72279d5__...csv` | Продвинутые темы, Web scraping | 11.2025 – 12.2025 |
| `0c07158d__...csv` | Промпт-инжиниринг, ElevenLabs, парсинг | 12.2025 – 01.2026 |
| `7968d170__...csv` | 17 МБ workflow-JSON-шерингов, Telegram-кнопки | 01.2026 |
| `4125b7ab__...csv` | «Курс 2.0», Telegram-кнопки, кейсы клиентов | 01.2026 – 02.2026 |
| `342d8f51__...csv` | RAG-бот в Telegram, токены, расходы | 02.2026 |
| `671fdf61__...csv` | Актуальные вопросы: rate limit, polling, обновление 2.0→2.1.5 | 02.2026 – 04.2026 |
