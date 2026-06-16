# 04 — Error handling (обработка ошибок)

> Основано на уроке 5 (Error Workflow) + реальные кейсы из чата + памятка Mavis по [ENVIRONMENT.md §3 VPS Beget] и [MISTAKES.md §X.Y].

## 4.1 Базовая архитектура

```
[Prod Workflow 1] ──┐
[Prod Workflow 2] ──┤
[Prod Workflow 3] ──┼──► [Error Workflow]
                    │      │
                    │      ├─ Error Trigger
                    │      ├─ Telegram → Send Message (админу)
                    │      └─ Supabase → INSERT (лог ошибок)
                    │
Settings каждого: Error Workflow = "error-handler"
```

## 4.2 Error Trigger — что доступно

Error Trigger отдаёт следующие поля:

| Поле | Пример | Зачем |
|---|---|---|
| `execution.id` | 12345 | уникальный ID упавшего запуска |
| `execution.mode` | "trigger" / "manual" / "webhook" | как запустилось |
| `workflow.name` / `workflow.id` | "telegram-bot" / 7 | какой workflow упал |
| `lastNodeExecuted` | "Telegram: Send Message" | на какой ноде упало |
| `error.message` | "Unauthorized" | текст ошибки |
| `error.node` | (имя ноды) | полезно для логов |
| `error.timestamp` | 2026-01-15T... | когда |

⚠️ **Чего НЕТ:** ID пользователя / chat_id, который инициировал запрос. Это и есть та проблема, что обсуждали в чате (см. §4.4).

## 4.3 Простой Error Workflow (минимум)

```
Error Trigger
    ↓
Set Variables (lastNodeExecuted, error.message, workflow.name)
    ↓
Telegram → Send Message
  chat_id: $env.ADMIN_CHAT_ID
  text: "🚨 {{$json.workflow.name}} упал: {{$json.error.message}}"
```

Чтобы `$env.ADMIN_CHAT_ID` работал, в `.env`:
```
ADMIN_CHAT_ID=123456789
```

## 4.4 Проблема: «как узнать chat_id юзера, у которого упало»

Из чата (январь 2026): «При ошибке организовать сообщение в чат **пользователю** (не админу), сообщение типа "мы уже в курсе и разбираемся". Триггер error не даёт инфу об id. ИИ предлагает 2 варианта:
1. Настройку в критических нодах (их слишком много).
2. Через Supabase сохранять id, потом в error-workflow взять и отправить в нужный чат».

### Решение №2 (рекомендую)

В каждом prod-workflow в самом начале (после Telegram Trigger) пишешь `chat_id` в таблицу:

```sql
-- Supabase
CREATE TABLE active_sessions (
  chat_id BIGINT PRIMARY KEY,
  user_name TEXT,
  last_workflow TEXT,
  last_step TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

В workflow:
```
Telegram Trigger (chat_id = $json.message.chat.id)
    ↓
Supabase → Upsert
  table: active_sessions
  data: { chat_id, user_name, last_workflow, last_step }
    ↓
[основная логика]
```

В error-workflow:
```
Error Trigger
    ↓
Supabase → Select (последние N active_sessions)
    ↓
Telegram → Send Message (chat_id = $json.chat_id, text = "⚠️ Сбой, мы разбираемся")
```

⚠️ **Нюанс:** отправлять сообщение сразу всем — спам. Лучше слать **только тем, чей workflow реально упал**. Для этого в Supabase сохраняй `last_workflow` + `last_step` — потом в error-workflow фильтруй.

## 4.5 Retry-паттерны

### На уровне одной ноды

У HTTP Request и многих других нод есть:
- `Retry on Fail` — включить
- `Max Retries` — сколько раз
- `Wait Between Retries` — пауза в мс

✅ **Best practice:** для внешних API (Telegram, OpenAI, YandexGPT) — **включай** `Retry on Fail`, `Max Retries: 3`, `Wait: 5000`. Многие ошибки — это 5xx на стороне сервиса, через секунду всё работает.

### На уровне workflow

Нода **Stop and Error** — принудительно «роняет» workflow с твоим сообщением. Используй, когда IF-каскад обнаружил, что данные не подходят, и дальше идти нельзя.

```
IF (data is valid)
  ├─ true  → Continue
  └─ false → Stop and Error (message: "Invalid input: {{$json}}")
```

## 4.6 «Lost connection to server» (500)

Из чата (`671fdf61`):
> «При запуске workflow появляется ошибка "lost connection to server" / 500»

Чаще всего это:
- **Долгий workflow** превысил таймаут HTTP-запроса от клиента (не workflow, а UI). Решение — workflow не виноват, это UI отвалился. Workflow продолжил выполняться на сервере. Проверь Executions.
- **OOM** — серверу не хватило RAM. Решение — меньше параллельных workflow, или upgrade.
- **Webhook от внешнего сервиса** слишком большой (multipart с большим файлом). Решение — увеличить `N8N_PAYLOAD_SIZE_MAX` в .env.

⚠️ Не паникуй из-за 500. Сначала проверь Executions → возможно, всё прошло.

## 4.7 «Chat not found» в Telegram-ноде

Из чата:
> «Почему у меня выдает ошибку в воркфлоу из урока по вакансиям hh в последней ноде телеграмм, и пишет что чат не найден? Хотя я поставила правильный chat_id»

Причины:
1. **`chat_id` — строка вместо числа** (или наоборот). Telegram-нода требует **строку** или **число**, проверь формат.
2. **Бот не стартован** — пользователь не нажал `/start` у бота. Бот не может писать, пока пользователь не инициирует диалог.
3. **В webhook приходит `chat_id` под другим ключом** — у Telegram Trigger это `$json.message.chat.id`, у Bot-меню — может быть `$json.callback_query.message.chat.id`.
4. **Групповой чат** — нужно `chat_id` группы, а не пользователя.

Подробнее: [07-telegram-bots.md §7.2](07-telegram-bots.md).

## 4.8 Удаление старых executions

```bash
# Вручную в UI
# Executions → выбрать всё → Delete

# Через API
curl -X DELETE 'https://n8n.yourdomain.ru/api/v1/executions?deleteBefore=2026-01-01' \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

⚠️ Известная проблема (см. [MISTAKES.md §X]): «Чистить executions через `deleteBefore` быстрее, чем по одному».

## 4.9 Глобальный error workflow в Settings

Помимо per-workflow Error Workflow, есть **глобальная** настройка в Settings → Workflows → Default error workflow. Это удобно — не надо в каждом workflow прописывать.
