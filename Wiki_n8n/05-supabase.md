# 05 — Supabase (Postgres + Auth + Storage)

> Основано на уроках 7 (установка) + 8 (векторная память) курса George Erman + живые Q&A.

## 5.1 Что даёт Supabase в n8n-стеке

- **Postgres** — основная БД для n8n (вместо SQLite, который был в старых версиях).
- **Supabase Storage** — S3-совместимое хранилище файлов.
- **Vector Store** — расширение pgvector для RAG.
- **Auth** — готовая авторизация (UI, OAuth, magic links).
- **REST API** — автогенерируемый API к таблицам.

## 5.2 Создание таблиц

### Через Supabase UI

```
Supabase → Table Editor → New table → заполнить поля → Save
```

### Через SQL Editor (рекомендую для RAG)

```
Supabase → SQL Editor → New query → вставить SQL → Run
```

Пример (для чат-бота с историей):

```sql
CREATE TABLE chat_history (
  id BIGSERIAL PRIMARY KEY,
  chat_id BIGINT NOT NULL,
  role TEXT NOT NULL,            -- 'user' | 'assistant' | 'system'
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chat_history_chat_id ON chat_history(chat_id);
```

Пример (для хранения состояния между запусками):

```sql
CREATE TABLE user_state (
  chat_id BIGINT PRIMARY KEY,
  current_step TEXT,
  context JSONB,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

## 5.3 Включение векторного расширения (pgvector)

Из урока 8:

```sql
-- Включить расширение
CREATE EXTENSION IF NOT EXISTS vector;

-- Создать таблицу документов с векторным столбцом
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536)  -- 1536 = размерность OpenAI text-embedding-3-small
);

-- Создать функцию поиска по вектору
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  metadata JSONB,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

⚠️ **Из чата (`342d8f51`, март 2026):** «Через Supabase UI почему-то SQL не выдал, а через ноду Postgres в n8n — сразу прошло». Если UI не срабатывает, выполняй SQL прямо из n8n через Postgres-ноду.

## 5.4 Нода Postgres vs Supabase в n8n

| | Postgres (сырая) | Supabase (с UI) |
|---|---|---|
| Подключение | host / port / db / user / password | URL + service_role_key |
| Что умеет | SELECT / INSERT / UPDATE / DELETE / любой SQL | SELECT / INSERT / UPDATE / DELETE / Storage / Auth |
| Vector Store | через `embedding <=> query_embedding` | через Supabase Vector Store node (готовая обёртка) |
| Когда использовать | сложные SQL, миграции, нестандартные запросы | 95% задач (рекомендую для начинающих) |

## 5.5 Где взять доступы

После установки через `n8n-installer`:

```bash
# Зайти на сервер
cd /root/n8n-installer
cat .env | grep -E "SUPABASE|POSTGRES|SERVICE_ROLE"
```

```env
# Пример:
POSTGRES_PASSWORD=...
POSTGRES_HOST=postgres   # в docker-сети, не localhost
POSTGRES_PORT=5432
POSTGRES_DB=supabase
SUPABASE_URL=https://supabase.yourdomain.ru
SERVICE_ROLE_KEY=eyJhbGciOi...   # ← длинный JWT, для Vector Store
ANON_KEY=eyJhbGciOi...
```

⚠️ **Не путай:**
- **SERVICE_ROLE_KEY** — для n8n-нод (полный доступ к БД)
- **ANON_KEY** — для клиентского кода в браузере (RLS работает)
- **FOLDER_ID** — это для YandexGPT, **не для Supabase** (частая ошибка)

## 5.6 Подключение из n8n

### Supabase credentials

```
Type: Supabase API
Host: https://supabase.yourdomain.ru
Service Role Key: eyJhbGciOi...   # из .env
```

### Postgres credentials (для ноды Postgres)

```
Type: Postgres
Host: postgres              # имя контейнера в Docker-сети
Database: supabase
User: postgres
Password: ...               # из .env
Port: 5432
SSL: disable (для docker-сети)
```

⚠️ **Не используй `localhost`** в Postgres credentials, если n8n и Postgres в одном docker-compose. Имя сервиса = имя контейнера = `postgres`.

## 5.7 Supabase Vector Store в n8n

Это **отдельная нода** (не просто SQL). Что она делает:

1. Получает текст (из Google Drive / Upload / etc.)
2. Режет на чанки (text splitter)
3. Через embedding-модель (OpenAI text-embedding-3-small по умолчанию) превращает каждый чанк в вектор
4. Записывает в таблицу `documents` (или указанную)

Из урока 8: «Supabase Vector Store использует дополнительный инструмент — Default Data Loader. Он и есть загрузчик. А у него есть Text Splitter, который режет массив текста на чанки».

Подробнее про чанки и embedding — [06-vector-memory-rag.md](06-vector-memory-rag.md).

## 5.8 Паттерн «загрузить документ в RAG»

```
Google Drive Trigger
  (watch folder /knowledge-base/)
    ↓
Google Drive → Download File
    ↓
Extract from File (PDF / DOCX / TXT)
    ↓
Default Data Loader
  - Text Splitter: Recursive Character (chunk_size: 1000, overlap: 200)
    ↓
Supabase Vector Store
  - Mode: Insert
  - Table: documents
  - Embedding Model: OpenAI text-embedding-3-small
    ↓
(No output — это endpoint)
```

## 5.9 Паттерн «запрос к RAG»

```
Telegram Trigger
    ↓
AI Agent
  ├─ Chat Model: OpenAI GPT-4.1 (или YandexGPT)
  ├─ System Message: "Ты специалист техподдержки..."
  ├─ Memory: Window Buffer Memory (chat_history table)
  └─ Tool: Supabase Vector Store
        - Table: documents
        - Metadata Filter: { type: "info_hub_docs" }
        - Embedding Model: OpenAI text-embedding-3-small
    ↓
Telegram → Send Message
```

## 5.10 Типичные ошибки

| Симптом | Причина | Решение |
|---|---|---|
| `extension "vector" is not available` | pgvector не установлен | проверить, что в docker-compose есть образ `pgvector/pgvector` |
| 401 Unauthorized | неправильный SERVICE_ROLE_KEY | пересохранить из .env |
| Cannot connect to postgres | использовал localhost | заменить на `postgres` (имя контейнера) |
| «Function match_documents not found» | не выполнил CREATE FUNCTION | см. §5.3 |
| SQL в UI не срабатывает | кэш UI | через Postgres-ноду в n8n |
| «permission denied for table» | RLS включён, anon key | использовать SERVICE_ROLE_KEY |
