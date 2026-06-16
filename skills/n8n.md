---
name: n8n
description: Работа с n8n 2.17.7 через REST API (создание, обновление, активация workflow) и помощь с design-паттернами (IF-каскад, Classify, Webhook vs Telegram Trigger, HTTP Request). Применяй когда задача про n8n workflow, Telegram-бота на n8n, ошибки активации, IF/Switch каскады, expressions `={{ }}`, `request/body must NOT have additional properties`, `Missing required credential: telegramApi`. НЕ применять для: research по новым фичам n8n (→ web_search), UI-only операций, простых вопросов без конкретной задачи.
---

# n8n (v2.17.7) — opinionated skill

## Концепция

**Скилл — это процедура. Источник правды — в memory и wiki.**

Этот скилл **не пересказывает** грабли и паттерны. Вместо этого:
- `memory_topic_read('n8n-api-quirks')` — **13 конкретных REST API граблей** (source of truth)
- `llm_manifest/ENVIRONMENT.md §4` — **proven design-паттерны** (архитектура, IF-каскад, inline buttons, активация)
- `llm_manifest/MISTAKES.md §3 + §4` — **исторические баги** (всё что уже было сломано)

Скилл нужен только чтобы знать **когда** и **как** всё это применять.

## Когда применять (триггеры)

Ключевые слова в запросе:
- «n8n», «workflow», «HTTP Request node», «Webhook node», «Telegram Trigger», «Classify», «IF-каскад», «Switch-узел»
- «`request/body must NOT have additional properties`», «`Missing required credential: telegramApi`», «`Workflow activation failed validation`»
- «`$('node_name')`», «expression», «`={{ }}`», «jsonBody», «JSON.stringify»
- «inline keyboard», «callback_data», «reply_markup», «sendMessage», «setWebhook»
- «`activeVersionId`», «`parentFolder`», «`webhookId`», «`isArchived`», «PUT workflow», «POST workflows»

**НЕ применять** на:
- «что нового в n8n 2.18» (research → web_search)
- «как установить n8n локально» (docs → не моя задача)
- опечатки в JSON / одиночные curl

## Алгоритм

### Шаг 1. Прочитай source of truth

```bash
# 1. Грабли (ОБЯЗАТЕЛЬНО, 13 пунктов, ~10 KB)
memory_topic_read('n8n-api-quirks')

# 2. Паттерны (релевантные подсекции ENVIRONMENT §4)
grep -A 20 "^### 4\." /workspace/llm_manifest/ENVIRONMENT.md

# 3. Исторические баги (если задача про ошибку)
grep -A 10 "^### 3\." /workspace/llm_manifest/MISTAKES.md | head -80
```

**Не** копируй 140 KB текста в свой ответ. **Фильтруй** по релевантной подсекции.

### Шаг 2. Определи тип задачи

| Задача | Что делать | Где смотреть |
|---|---|---|
| **Создать workflow** | минимальный body (5 полей), без `tags/id/active` | n8n-api-quirks §1, §2 |
| **Обновить workflow (PUT)** | strip `active/isArchived/parentFolder/tags`, добавить credentials | n8n-api-quirks §4-§8, §10 |
| **Активировать workflow** | `POST /activate`, проверить missing credentials | MISTAKES §3.2, n8n-api-quirks §6 |
| **Webhook не работает** | deactivate → PUT → activate (cycle) | MISTAKES §3.2 |
| **Telegram Trigger теряет credentials** | добавить credentials в КАЖДЫЙ telegram-узел (включая Trigger) | n8n-api-quirks §6, §10 |
| **Inline-кнопки не рендерятся** | проверить `reply_markup` — должен быть ОБЪЕКТ, не строка | n8n-api-quirks §9, ENVIRONMENT §4.7 |
| **`={{ }}` показывается как текст** | добавить префикс `=` в начале поля | n8n-api-quirks §11, ENVIRONMENT §4.6 |
| **Передать объект в jsonBody** | Code-узел → `JSON.stringify(...)` → `jsonBody: "={{ JSON.stringify($('fmt').first().json.body) }}"` | n8n-api-quirks §11 |
| **`$env.X` = null** | hardcode токен в URL или настроить env в docker-compose | n8n-api-quirks §13 |
| **Design на 5+ команд** | IF-каскад (НЕ Switch — баг в 2.17.7) | ENVIRONMENT §4.5, MISTAKES §3.8 |
| **Switch редактируется через API** | не работает в 2.17.7, использовать IF-каскад | MISTAKES §3.8 |

### Шаг 3. Генерируй код/команду

**Минимальный CREATE body** (из n8n-api-quirks):
```json
{
  "name": "My Workflow",
  "description": "Some description",
  "nodes": [...],
  "connections": {...},
  "settings": {"executionOrder": "v1"}
}
```

**Минимальный UPDATE body (PUT)**: то же + `credentials` в каждом telegram-узле.

**Активация**:
```bash
curl -X POST "https://<n8n>/api/v1/workflows/<id>/activate" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
# 200 = OK, 400 = missing credentials (в ответе — каких)
```

### Шаг 4. После активации — верифицируй

```bash
# 1. Проверить execution
curl "https://<n8n>/api/v1/executions?workflowId=<id>&limit=5" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# 2. Проверить webhook registered
curl "https://<n8n>/api/v1/workflows/<id>" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.webhookId, .active'
```

Если webhook unregistered → ещё раз deactivate → activate.

## Анти-паттерны (что НЕ делать)

- ❌ **Использовать Switch-узел** — баг в n8n 2.17.7, conditions теряются при PUT. IF-каскад всегда.
- ❌ **Telegram Trigger для нового workflow** — credentials не привязываются через API. Используй Webhook node + `setWebhook`.
- ❌ **Связывать reply→reply** — Telegram reply-узлы = terminal, нет outgoing connections.
- ❌ **2 telegram-ноды на одного бота** — глюки с credentials. Один Trigger.
- ❌ **HTTP-узел с 2+ outgoing connections** — n8n берёт только index 0. Для shared backend — дублируй HTTP-узел.
- ❌ **`parentFolder / isArchived / active / versionId` в PUT body** — read-only, ошибка 400.
- ❌ **Telegram node v1 для inline-кнопок** — баг с `reply_markup`. Используй HTTP Request напрямую к Telegram API.
- ❌ **expression без `=` префикса** — `{{ }}` покажется как текст, не вычислится.
- ❌ **jsonBody строкой с expression** — не вычисляется. Code-узел → объект → `JSON.stringify(...)` → expression.
- ❌ **Переименовывать ноду без обновления connections** — connections ломаются, `$('name')` падает.
- ❌ **Использовать id в `$('...')`** — `$('name')` использует `node.name` (display name), не `node.id`.
- ❌ **`pkill -9 -f n8n`** — убивает все процессы, включая свои. Лучше: `docker stop` (если Docker) или systemd.
- ❌ **Hardcode bot token в `additionalFields`** — используй `$env.TELEGRAM_BOT_TOKEN` или credentials.

## Smoke test (как понять, что скилл отработал)

В правильном ответе ты увидишь **хотя бы 3 из 5**:

1. ✅ **Ссылка на конкретный quirk** — `[n8n-api-quirks §11]`, `[MISTAKES.md §3.8]`, `[ENVIRONMENT.md §4.5]`
2. ✅ **Конкретный код/команда** — готовый curl, JSON body, или bash скрипт
3. ✅ **Предупреждение об анти-паттерне** — «не используй Switch, в 2.17.7 баг», «не включай `active` в body»
4. ✅ **Чёткое opinionated действие** — «сделай X, потому что Y», не «можно A или B»
5. ✅ **Верификация после** — что проверить, чтобы убедиться что работает

## Связь с другими skill'ами

- **`wiki-loader`** — этот скилл узко про n8n; `wiki-loader` шире (вся среда). При задачах только про n8n — **этот скилл первичен**.
- **`wiki-curator`** — если нашёл новый quirk которого нет в `n8n-api-quirks` → после фикса обнови memory topic (а лучше — `MISTAKES.md §3` для версионирования через git).
- **`gstack-team`** — если задача «спроектируй систему из 5+ n8n workflow'ов с общими паттернами» → это уже архитектура, передать в gstack-team Phase 2.

## Если source of truth пустой

`memory_topic_read('n8n-api-quirks')` → 404 или пусто.

**Решение:**
1. Скажи юзеру: «не вижу n8n-api-quirks в memory, нужно инициализировать»
2. Если он скажет «да» — fetch с GitHub:
   ```bash
   curl -sL https://raw.githubusercontent.com/swzhukov/llm_manifest/main/llm_manifest/memory/n8n-api-quirks.md \
     -o /tmp/n8n-api-quirks.md
   # и показать путь
   ```
3. Или работай по ENVIRONMENT.md §4 + MISTAKES.md §3-4 (там 80% покрыто).
