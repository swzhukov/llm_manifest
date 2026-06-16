# n8n Wiki — README

## Что это

База знаний по **n8n**, собранная из 10 тредов форума `n8node` (Q3 2025 — Q1 2026) и расширенная структурированным изложением.

**Источник:** практические уроки George Erman + живое обсуждение в чате (~30 активных участников).

**Объём:** 14 файлов, ~60 KB markdown.

## Для кого

- **Ты учишь n8n с нуля** — [index.md](index.md) → последовательно 01 → 09.
- **Ты делаешь конкретную задачу** — [index-by-task.md](index-by-task.md) — поиск по типу.
- **Ты — Mavis / LLM-агент** — [alignment-with-skill-loader.md](alignment-with-skill-loader.md) — оценка применимости к wiki-loader skill.
- **Ты преподаёшь n8n** — материал готов к адаптации (структура, цитаты из уроков с явной отметкой источника).

## Структура

```
wiki/
├── index.md                         # Оглавление
├── index-by-task.md                 # Оглавление по типу задачи
├── README.md                        # Этот файл
├── alignment-with-skill-loader.md   # Cross-reference с SKILL.md
├── 00-quick-reference.md            # Шпаргалка (начни здесь)
├── 01-installation.md               # Установка, обновление, .env
├── 02-interface-and-nodes.md        # UI, ноды, триггеры
├── 03-workflow-settings.md          # Settings, экономия диска
├── 04-error-handling.md             # Error workflow, retry
├── 05-supabase.md                   # Postgres + Vector + Auth
├── 06-vector-memory-rag.md          # RAG, чанки, embeddings
├── 07-telegram-bots.md              # Telegram: боты, кнопки, polling
├── 08-yandex-gpt.md                 # Yandex Cloud, OpenAI-совместимый
├── 09-ai-agents.md                  # AI Agent: tools, temperature, costs
├── 10-common-errors.md              # 20+ типичных ошибок с корнями
├── 11-best-practices.md             # Best practices, антипаттерны
├── 12-system-prompts.md             # Готовые промпты (SEO, RAG, support)
└── archive/
    └── forum-threads-map.md         # Карта исходных 10 CSV
```

## Конвенции

- **«Из урока N»** — цитата из курса George Erman (главный курс в `631396a6__...csv`).
- **«Из чата»** — наблюдение из живого обсуждения.
- **«⚠️ Подводный камень»** — то, что сожрёт время, если не знать.
- **«✅ Best practice»** — отработанное решение, рекомендуемое сообществом.
- **Ссылки `[ENVIRONMENT.md §X.Y]`** — указывают на репо `swzhukov/llm_manifest` (подтягиваются через `wiki-loader` skill).

## Ограничения

- Wiki собрана из **конкретного форума** (n8node). Не претендует на «всё про n8n».
- **Не покрывает:** Flask, ssh/bash-нюансы, конкретные секреты твоего сервера.
- **Частично покрывает:** Bot Menu (есть memory topic `telegram-bot-menu` с подробностями).
- **Конкретно не выдумывает:** если чего-то нет в тредах — пишет «не покрыто».

## Когда обновлять

- После каждого нового урока в курсе George Erman.
- После каждой найденной ошибки (в чате или в проде).
- После изменения в n8n API / n8n-installer / Supabase API.
- Раз в квартал — ревизия устаревших утверждений (n8n быстро развивается).

## Благодарности

- George Erman (@ermangeorge) — преподаватель курса, источник 80% знаний.
- Анастасия Горбач — активный студент, помогает новичкам.
- Aleksius Intelligence, Патрик Бэйтс, Roman Bulgakov — техэкспертиза в чате.
- Участники форума n8node — за живые кейсы и фидбэк.

## Лицензия

Внутренний документ. Не публиковать без согласия Сергея.
