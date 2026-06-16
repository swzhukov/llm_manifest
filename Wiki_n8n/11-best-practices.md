# 11 — Best Practices

> Собрано из уроков + 30+ сообщений в чате.

## 11.1 Экономия диска

> Из урока 5: «Катастрофическое переполнение жёсткого диска... основная трата — каждое выполнение записывается. Управляем этим: сейв error / don't save success».

### Минимум настроек

```
Settings:
  Save Error Success:        Save       ← иначе не увидишь ошибки
  Save Execution Success:    Don't Save ← диск не пухнет
  Save Manual Executions:    Don't Save ← ручные тесты не копятся
```

### Дополнительно: чистка через API

```bash
curl -X DELETE 'https://n8n.yourdomain.ru/api/v1/executions?deleteBefore=2026-01-01' \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

### Глобальная чистка через cron

Создай **отдельный workflow**:
```
Schedule Trigger (раз в неделю)
    ↓
HTTP Request
  DELETE /api/v1/executions?deleteBefore={{DateTime.now().minus({days: 30}).toISO()}}
```

## 11.2 Retry на внешних API

Все внешние вызовы (Telegram, OpenAI, Yandex, любой HTTP) ставь с **Retry on Fail**:

| Параметр | Значение |
|---|---|
| Retry on Fail | ✅ |
| Max Retries | 3 |
| Wait Between Retries | 5000 мс |

Почему: 90% ошибок 5xx — это временный сбой на стороне сервиса, через 5 сек всё работает.

## 11.3 Организация workflow

### Папки и теги

Из урока 4: «Папки и теги — это очень удобная вещь, замечательно работает на моменте фильтрации».

**Рекомендуемая структура:**

```
📁 /Clients
   ├── /Client_A
   │   ├── workflow1
   │   ├── workflow2
   │   └── [error-handler]
   └── /Client_B
📁 /Internal
   ├── /Production
   │   ├── telegram-bot-v2
   │   └── data-sync
   └── /Sandbox
       ├── tests
       └── experiments
📁 /Templates
   ├── rag-bot-template
   └── webhook-handler-template
```

**Теги для каждого workflow:**

- `production` / `dev`
- `client:Acme` / `client:Globex`
- `domain:HR` / `domain:Finance`
- `tech:rag` / `tech:webhook` / `tech:cron`
- `cost:high` (если LLM-запросы) / `cost:low`

## 11.4 Naming convention

### Workflow

- `domain-action-purpose` (kebab-case)
- Примеры: `telegram-hr-bot`, `crm-leads-sync`, `email-triage`

### Nodes (внутри workflow)

- `Verb Object` (PascalCase)
- Примеры: `Telegram Trigger`, `HTTP Request`, `Set Order Status`, `IF Is Premium`

✅ **Best practice:** называй ноды по **действию**, а не по типу. Не `Code1`, а `Format Date to ISO`. Не `HTTP Request`, а `Get Weather by City`.

## 11.5 Sticky Notes — стандарт

В каждый нетривиальный workflow в самом верху:

```markdown
# Workflow: [название]

**Назначение:** что делает в одном предложении
**Зависит от:** [другие workflow, внешние сервисы]
**Обновляет:** [таблицы, файлы, каналы]
**Автор:** [ник / email]
**Последнее обновление:** 2026-01-15
**Версия:** 1.4.2
```

## 11.6 Error handling по умолчанию

Каждый продакшн-workflow:

1. **Error Workflow** = `error-handler` (свой workflow, см. [04-error-handling.md](04-error-handling.md)).
2. **Retry on Fail = true** на внешних нодах.
3. **Логирует в Supabase** ключевые шаги (chat_id, status, error).
4. **Не падает молча** — error handler шлёт сообщение.

## 11.7 Версионирование

Храни **JSON-экспорт workflow** в git:

```
/workflows/
  ├── prod/
  │   ├── telegram-hr-bot.json
  │   └── crm-leads-sync.json
  ├── staging/
  └── README.md
```

```bash
# Перед изменением:
n8n export:workflow --id=abc123 > workflows/prod/telegram-hr-bot.json
git commit -m "before refactor: telegram-hr-bot v1.4.2"
```

✅ **Best practice:** не редактируй продакшн напрямую. Сначала **Duplicate**, изменения, тест, потом — **импорт JSON** в основной.

## 11.8 Credentials — правила гигиены

1. **Никогда** не пиши API-ключи в ноде руками — только через Credentials.
2. **Backup credentials** через n8n UI (Settings → Usage → Export).
3. **Ротация:** раз в 90 дней для продакшн-ключей.
4. **Service Role** (Supabase) — только в n8n, **никогда** в браузерном коде.
5. **FOLDER_ID / IAM token** (YandexGPT) — без срока действия, но всё равно бэкапить.

## 11.9 Логи и наблюдаемость

### Executions — главный инструмент

- **Настрой фильтр:** показывать только `error` — меньше шума.
- **Включи auto-refresh** — новые ошибки появляются сразу.
- **Клик на красную ноду** — внутри JSON с input/output, видно, что пришло.

### Логирование в Supabase

```sql
CREATE TABLE workflow_logs (
  id BIGSERIAL PRIMARY KEY,
  workflow_name TEXT,
  execution_id TEXT,
  status TEXT,  -- 'success' | 'error' | 'warning'
  chat_id BIGINT,
  duration_ms INT,
  message TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

В каждом workflow — финальная нода `INSERT` в эту таблицу.

## 11.10 Документация для клиента

Если делаешь workflow на заказ — **обязательно** в Sticky Note:

1. Что делает (по-человечески)
2. Какие сервисы используются
3. Где менять настройки (API-ключи, тексты)
4. К кому обращаться при ошибке

## 11.11 Самые частые «вредные советы» из чата

> «ИИ-ассистент (ChatGPT/Claude) — лучший источник решений»

✅ **Лучше:** ИИ отлично помогает с шаблонами кода, но **конкретную ошибку в твоей среде** — спрашивай в чате / читай логи. Из чата: «Я бился с этой задачей... просто поставил loop и через него все страницы прогонял» — это **опыт**, а не промпт.

> «Используй `pkill -9 python` чтобы перезапустить»

❌ **Нет:** потеряешь данные и состояние. Сначала `pkill -TERM`, подождать, потом `-9` если не помогло.

> «Поставь rate-limit побольше — пусть LLM думает дольше»

⚠️ **Следи за балансом:** больше rate-limit → больше токенов → больше $. Начни с дефолта, оптимизируй по необходимости.

> «Всё в одном workflow — проще»

❌ **Нет:** при росте — боль. Разделяй: `telegram-trigger` → `parse-message` → `route-by-intent` → отдельные sub-workflows для каждого intent.

## 11.12 Когда переходить с бесплатного n8n на платный

| Признак | Действие |
|---|---|
| Workflow 24/7 на n8n.cloud | **Self-hosted** (свой сервер) — бесплатно |
| Нужна история executions дольше 7 дней | self-hosted + чистка по расписанию |
| Нужны папки | разблокировать лицензию (бесплатно через community unlock) |
| 5+ параллельных executions | увеличить `N8N_WORKERS` |
| Multi-user (команда) | self-hosted с авторизацией |

✅ **Best practice:** для серьёзных проектов — **всегда self-hosted**. n8n.cloud — только для оценки.
