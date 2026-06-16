# ENVIRONMENT.md — единый reference контекста среды

> **Версия:** 3.0 (unified, июнь 2026) — объединяет DEVELOPMENT_PLAYBOOK (Капитал) + ENVIRONMENT (research-agent)
> **Назначение:** Полный «снимок» знаний о среде, стеке, API, паттернах и best practices. Проект-агностик. Используется как шаблон для ЛЮБОГО нового проекта в этой среде.
> **Как применять:** отдать этот файл + `MISTAKES.md` агенту в начале нового проекта. Агент сразу понимает, какие среды есть, какие API доступны, какие паттерны работают, каких ошибок избегать.

---

## ОГЛАВЛЕНИЕ

0. [Контекст пользователя (PM)](#0-контекст-пользователя-pm)
1. [Архитектурные паттерны (proven)](#1-архитектурные-паттерны-proven)
2. [Окружения и шаблоны секретов](#2-окружения-и-шаблоны-секретов)
3. [VPS Beget — структура, деплой, нюансы](#3-vps-beget--структура-деплой-нюансы)
4. [n8n (2.17.7) — workflow automation](#4-n8n-2177--workflow-automation)
5. [Flask + Python API на VPS](#5-flask--python-api-на-vps)
6. [YandexGPT интеграция](#6-yandexgpt-интеграция)
7. [Telegram Bot — best practices](#7-telegram-bot--best-practices)
8. [State persistence (multi-user JSON)](#8-state-persistence-multi-user-json)
9. [Memory topics — что и где фиксировать](#9-memory-topics--что-и-где-фиксировать)
10. [Тестирование](#10-тестирование)
11. [CI/CD без CI — ручной deploy](#11-cicd-без-ci--ручной-deploy)
12. [YouTube subs — источники (если нужно качать)](#12-youtube-subs--источники-если-нужно-качать)
13. [GitHub — auth и scopes](#13-github--auth-и-scopes)
14. [Cheatsheet — copy-paste команды](#14-cheatsheet--copy-paste-команды)
15. [Чеклист перед продакшн-деплоем](#15-чеклист-перед-продакшн-деплоем)
16. [Частые «How to»](#16-частые-how-to)
17. [Reference URLs](#17-reference-urls)
18. [Что читать ПЕРВЫМ в новой сессии](#18-что-читать-первым-в-новой-сессии)

---

## 0. Контекст пользователя (PM)

> **Самопроверка перед каждым turn'ом:** это НЕ «средний клиент». PM — фаундер/ПМ, не аналитик, не клиницист, не академический исследователь.

| Параметр | Значение | Что это меняет |
|---|---|---|
| Имя | Sergey Zhukov (Сергей) | Личное обращение по имени, не «пользователь» |
| Среда | **Windows PowerShell**, НЕ bash | Каждая команда должна явно работать в PS или быть кросс-совместимой |
| Стиль | Короткие русские фразы, без академической обвязки | Не «rest assured», «happy to help» — а «сделал X, проверь Y» |
| Решения | Быстрые, **opinionated default** без hedging | Давать 1 рекомендацию + обоснование, а не «можно A или B» |
| Доверие | «Давай делай все сам» | Не спрашивать каждую мелочь, а решать самому + фиксировать |
| Scope | Допускает **полный ребилд** при сдвиге предпосылок | Лучше пересобрать, чем патчить in place |
| Стоп-сигналы | «У нас всё хорошо», «это выходит за рамки», «нужны исследования» | Эти фразы = СТОП, пересмотреть |

**🚫 НЕ делать:**
- Hedging («could be», «можно рассмотреть»)
- «50 фич с приоритетами» — лучше 5 фич с обоснованием
- «Нужны дополнительные исследования пользователей» (для MVP = нет)
- «Может, попробуем X без Y» (без обоснования)
- Перед каждой командой уточнять «ты в bash или PowerShell?» — PM даст ответить один раз, дальше запоминаем

**✅ Делать:**
- Структурированный вывод (карточки, таблицы, чеклисты)
- Минимум мета-комментариев, максимум конкретных следующих шагов
- Anti-pattern lists (жёсткие «не делать X»)
- single financial anchor + capability ranking при продуктовых решениях
- Резать scope решительно, не пытаться покрыть всё

**Где это зафиксировано в памяти агента:** `user_profile` тема — обновлять при обнаружении новых паттернов.

---

## 1. Архитектурные паттерны (proven)

### 1.1 Стек (production-ready для этой среды)

```
Telegram user
   ↓ webhook
Traefik (reverse proxy, порты 80/443)
   ↓
n8n workflow (оркестратор)
   ├─ IF-каскад для routing
   ├─ Code-ноды для форматирования
   └─ HTTP Request к Flask API
   ↓
Flask API (monolith или split, порт 8080)
   ├─ Multi-user state (JSON / Postgres)
   ├─ Бизнес-логика (Python)
   └─ Lazy import модулей
   ↓
YandexGPT (HTTPS к llm.api.cloud.yandex.net)
   +
Telegram Bot API (HTTPS к api.telegram.org)
   +
Опционально: YouTube subs (yt-dlp / Piped / Invidious)
```

### 1.2 Главный принцип — «n8n для glue, Python для бизнес-логики»

- **n8n:** маршрутизация сообщений, вызовы API, отправка в Telegram, inline-кнопки
- **Python/Flask:** вся бизнес-логика, валидация, вычисления, state management
- **НИКАКОЙ бизнес-логики в n8n Code nodes** — только `$('NodeName').first().json.body` форматирование
- **НИКАКИХ** `if-elif` цепочек в Python > 3 уровня — вынести в state machine

### 1.3 Альтернативы, которые НЕ сработали (анти-паттерны)

- ❌ Google Sheets / Google Cloud для данных РФ (152-ФЗ — данные не должны покидать РФ юрисдикцию)
- ❌ Mobile app вместо Telegram-бота (Telegram = дифференциатор, mobile = 6+ мес разработки)
- ❌ Telethon / Userbot (overkill, Telegram Bot API хватает)
- ❌ B2B в MVP (B2C быстрее валидировать unit-economics)
- ❌ Whisper / STT в Phase A (ROI не подтверждён)
- ❌ Real estate / банковские модули (юридическая сложность, вне scope)
- ❌ n8n Switch-узел через API (ненадёжен, нельзя редактировать через REST) — **IF-каскад ONLY**
- ❌ n8n Telegram Trigger с credential через API (credentials silently ignored) — **Webhook node + setWebhook**
- ❌ Hardcoded bot token в n8n HTTP Request URL (работает, но anti-pattern) — credential в Phase B+

### 1.4 Структура Python-проекта (multi-package)

```
/opt/beget/<project>/
├── src/<project>/          # модули (fraud.py, payday.py, ...)
├── tests/                  # pytest
├── deploy/                 # Flask integration (add_<project>_endpoints.py)
├── data/state.json         # persistent state (multi-user)
├── workflows/              # n8n workflows (JSON экспорт)
├── strategy/               # research, market analysis
└── docker/, scripts/
```

Или для split-project:
```
/opt/beget/
├── <project>/              # Python-проект
│   ├── src/<project>/
│   ├── tests/
│   └── ...
└── n8n/                    # n8n stack
    ├── newton-api.py       # Flask monolith (или <project>-api.py если split)
    ├── .env
    ├── docker-compose.yml
    └── <project>/          # deploy код
```

---

## 2. Окружения и шаблоны секретов

### 2.1 VPS Beget

| Параметр | Значение |
|---|---|
| Хост | `seefeesnahurid.beget.app` (DNS) / `217.114.7.5` (IP, виден в Telegram getWebhookInfo) |
| User | `root` |
| Port | `22` (стандартный SSH) |
| Password | **НЕ в этом файле** — в `/root/.mavis/secrets/beget_ssh` (mode 600) |
| Стек | Docker Compose (`n8n-n8n-1`, `n8n-n8n-worker-1`, `n8n-postgres-1`, `n8n-traefik-1`, `n8n-redis-1`) |
| OS | Ubuntu 24.04.4 LTS |
| Hardware | 1 vCPU, 1.9 GB RAM, 0 swap, ~14 GB disk (6 GB free) |
| TZ | Europe/Moscow |

### 2.2 n8n (default для этой среды)

| Параметр | Значение |
|---|---|
| URL | `https://seefeesnahurid.beget.app/` |
| UI | `https://seefeesnahurid.beget.app/` (login = email/password) |
| API base | `https://seefeesnahurid.beget.app/api/v1/` |
| Auth header | `X-N8N-API-KEY: <api_key>` |
| API key location | PostgreSQL: `user_api_keys.apiKey` (columns: `id`, `label`, `"apiKey"`) |
| API key извлечение | `docker exec -e PGPASSWORD=<pg_pass> n8n-postgres-1 psql -U root -d n8n -c "SELECT \"apiKey\" FROM user_api_keys WHERE label='<label>'"` |
| n8n version | `2.17.7` (image `docker.n8n.io/n8nio/n8n:2.17.7`) |
| Encryption key | Из `.env`: `N8N_ENCRYPTION_KEY=<uuid>` |

### 2.3 Telegram Bot (шаблон)

| Параметр | Значение |
|---|---|
| Bot token | **НЕ в этом файле** — в `.env` или в `/root/.mavis/secrets/telegram_bot_<project>` |
| Webhook path | `/webhook/<webhookId>/webhook` (UUID) или `/webhook/<name>` (path-based) |
| getWebhookInfo | `https://api.telegram.org/bot<token>/getWebhookInfo` |

**⚠️ Multi-bot на одном VPS:**
- Telegram API разрешает только **1 webhook per bot** (per token)
- Разные боты = разные токены = разные webhook URL'ы
- Проверять через `getWebhookInfo` КАЖДЫЙ бот при старте

### 2.4 YandexGPT (шаблон)

| Параметр | Значение |
|---|---|
| API key | **НЕ в этом файле** — в `.env` (`<PROJECT>_YANDEX_GPT_API_KEY`) |
| Folder ID | **НЕ в этом файле** — в `.env` (`<PROJECT>_YANDEX_GPT_FOLDER_ID`) |
| Model | `yandexgpt-lite` (default) |
| URL | `https://llm.api.cloud.yandex.net/foundationModels/v1/completion` |
| Pricing | ~0.20₽ за 1K токенов (yandexgpt-lite) |
| Daily cap | 4000 токенов/юзер (anti-spam) или согласно `<PROJECT>_DAILY_BUDGET_RUB` |
| Auth | `Authorization: Api-Key <api_key>` (НЕ Bearer!) |
| modelUri | `gpt://<folder_id>/yandexgpt-lite` (без `https://`!) |

### 2.5 Локальная разработка (sandbox agent)

| Параметр | Значение |
|---|---|
| Workspace | `/workspace/<project>/` |
| Source | `/workspace/<project>/src/<project>/` |
| Tests | `/workspace/<project>/tests/` |
| Python version | 3.11 (системный) |
| pytest | Глобально: `pip3 install pytest --break-system-packages` |
| Запуск тестов | `cd /workspace/<project> && PYTHONPATH=src python3 -m pytest tests/ -v` |
| Deploy helper | `/workspace/.vps-helper.sh` (см. §3.3) |

### 2.6 Секреты (ГДЕ ХРАНИТЬ, не ЧТО)

**🚨 Правило:** секреты НИКОГДА не в:
- Git репо (даже в `.env.example` без values — но и без шаблонов)
- Memory topics
- Playbook / environment docs
- Chat history (после первого сохранения)

**✅ Где хранить:**

| Секрет | Файл / где |
|---|---|
| VPS SSH password | `/root/.mavis/secrets/beget_ssh` (mode 600) |
| n8n API key | Тот же файл `beget_ssh` (поле `n8n_key=`) ИЛИ `/root/.mavis/secrets/n8n_api_key` |
| Bot tokens | `.env` проекта (mode 600) — НЕ в memory |
| YandexGPT API key + folder_id | `.env` проекта (mode 600) |
| Postgres password | `/opt/beget/n8n/.env` (mode 600) |
| n8n encryption key | `/opt/beget/n8n/.env` (mode 600) |

**Формат `/root/.mavis/secrets/beget_ssh`:**
```
host=<vps_host>
user=root
port=22
password=<password>
n8n_key=<api_key_here>
```

**🚨 КРИТИЧНО:** этот файл **теряется между сессиями** (in-memory). Первая команда в новой сессии — восстановление (см. MISTAKES §1.2).

---

## 3. VPS Beget

### 3.1 Структура `/opt/beget/`

```
/opt/beget/
├── <project1>/                 # Python-проект 1
│   ├── src/<project1>/
│   ├── tests/
│   ├── deploy/
│   ├── data/state.json
│   ├── workflows/
│   └── ...
├── <project2>/                 # Python-проект 2
│   └── ...
└── n8n/                        # Newton + n8n + Telegram Transcription
    ├── newton-api.py           # Flask monolith (или split per project)
    ├── newton-api.py.bak.*     # бэкапы (формат YYYYMMDD_HHMMSS)
    ├── .env                    # все секреты n8n + projects
    ├── docker-compose.yml      # n8n stack
    ├── n8n_storage/            # n8n data
    ├── db_storage/             # n8n postgres data
    ├── redis_storage/          # n8n redis data
    ├── traefik_data/           # n8n reverse proxy
    ├── <project>/              # код каждого project'а
    ├── newton-tmp/             # tmp files for Newton
    └── backups/                # backups
```

### 3.2 SSH и ForceCommand

**Проблема:** Beget shared hosting имеет `ForceCommand` в sshd_config → `ssh host 'cmd'` (inline) может блокироваться.

**Решение:** использовать **heredoc** через stdin:
```bash
/workspace/.vps-helper.sh 'bash -s' <<'REMOTE'
ls /opt/beget/
REMOTE
```

Или просто **интерактивная SSH-сессия** PM'а (а не вложенная команда).

### 3.3 Helper-скрипт `/workspace/.vps-helper.sh`

```bash
#!/bin/bash
set -e
HOST="seefeesnahurid.beget.app"
USER="root"
PASS=$(cat /root/.mavis/secrets/beget_ssh | grep password= | cut -d= -f2-)
if [ "$1" = "file_cp" ]; then
    sshpass -p "$PASS" scp -o StrictHostKeyChecking=no -r "$2" "$USER@$HOST:$3"
elif [ "$1" = "get" ]; then
    sshpass -p "$PASS" scp -o StrictHostKeyChecking=no "$USER@$HOST:$2" "$3"
else
    sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 "$USER@$HOST" "$@"
fi
```

**Восстановление (после рестарта sandbox):**
```bash
apt-get update && apt-get install -y sshpass
mkdir -p /root/.mavis/secrets
# ⚠️ СОЗДАТЬ ФАЙЛ РУКАМИ через read/PM, НЕ через heredoc в chat
```

**⚠️ Пароль содержит спецсимволы** (формат `~<8chars><base64>+`) — bash подставляет `~` как HOME.
**Решение:** `cut -d= -f2-` сохраняет `~` буквально (это не bash variable expansion).

**Типичные команды:**
```bash
# Один удалённый bash (heredoc)
/workspace/.vps-helper.sh 'bash -s' <<'REMOTE'
ls /opt/beget/
REMOTE

# Inline shell (только если нет спецсимволов)
/workspace/.vps-helper.sh "ls /opt/beget/<project>/src/"

# Upload файл
/workspace/.vps-helper.sh file_cp /workspace/<project>/src/<project>/<file>.py /opt/beget/<project>/src/<project>/<file>.py

# Download файл
/workspace/.vps-helper.sh get /opt/beget/<project>/data/state.json /tmp/state.json
```

### 3.4 Docker на Beget

```bash
# Контейнеры n8n
docker ps --format '{{.Names}} | {{.Image}} | {{.Status}}'

# Логи
docker logs n8n-n8n-1 2>&1 | tail -30

# Зайти в контейнер
docker exec -it n8n-postgres-1 psql -U root -d n8n

# Запустить Flask с env из .env
cd /opt/beget/n8n && set -a; source .env; set +a; nohup python3 newton-api.py > api.log 2>&1 &
```

### 3.5 Beget — частые нюансы

- **sshpass теряется** после рестарта/обновлений — переустановить
- **secrets файл теряется** после рестарта sandbox — пересоздать
- **Нет systemd-менеджера** для сервисов — запускаются через `nohup` в фоне
- **Postgres in container** — для доступа нужны env-переменные из `/opt/beget/n8n/.env`
- **Traefik проксирует** на n8n контейнер, webhook URL всегда `https://seefeesnahurid.beget.app/...`
- **ForceCommand** в sshd (см. §3.2)
- **IP-based YouTube CDN block** (см. §12.1) — `googlevideo.com` не доступен напрямую
- **1.9 GB RAM** — не запускать > 1-2 Python процессов одновременно
- **0 swap** — OOM kill при пиках

---

## 4. n8n (2.17.7)

### 4.1 Архитектура workflow

- **Название workflow:** осмысленное (`research_agent`, `payday_ritual`, `iis_loop`)
- **Один Telegram Trigger** на бота. Несколько workflow = несколько триггеров = конфликты
- **Webhook path:**
  - UUID-based (default): `/webhook/<webhookId>/webhook`
  - Path-based (через `path` field в Webhook node): `/webhook/<name>` — **предпочтительно** для multi-bot setup
- **Telegram updates:** `message` + `callback_query` (в `additionalFields.allowedUpdates`)
- **HTTPS обязательно** — Telegram не отправит на http://

### 4.2 n8n API — основные endpoints

```bash
# Headers (ВСЕ запросы)
X-N8N-API-KEY: <api_key>
Content-Type: application/json

# List workflows
GET /api/v1/workflows
→ {"data": [{"id": "...", "name": "...", "active": true, "nodes": [...], "connections": {...}}]}

# Get single workflow
GET /api/v1/workflows/<id>
→ полный объект

# Update (PUT)
PUT /api/v1/workflows/<id>
Body: {"name": "...", "nodes": [...], "connections": {...}, "settings": {...}}
⚠️ Никаких других полей (id, createdAt, updatedAt, activeVersionId, tags, isArchived, etc.) — будет 400 "additional properties"

# Activate
POST /api/v1/workflows/<id>/activate
→ {"active": true, ...}

# Deactivate
POST /api/v1/workflows/<id>/deactivate
→ {"active": false, ...}

# Get executions
GET /api/v1/executions?workflowId=<id>&limit=N
→ {"data": [{"id": "...", "status": "success|error", "startedAt": "...", "stoppedAt": "..."}]}

# Get execution with data
GET /api/v1/executions/<id>?includeData=true
→ runData со всеми executed нодами
```

### 4.3 Webhook node vs Telegram Trigger

**WebHook node (РЕКОМЕНДУЕТСЯ):**
- ✅ НЕ требует credential в workflow
- ✅ Задаётся `path` (например `research-agent`)
- ✅ Управляется через `setWebhook` API
- ✅ Поддерживает multi-bot setup

**Telegram Trigger:**
- ❌ Требует credential → n8n API **silently ignores** credentials в PUT
- ❌ WebhookId = UUID, нельзя задать path
- ⚠️ Работает только в UI

**Webhook path-based (новый паттерн):**
```
Webhook node:
  - httpMethod: POST
  - path: 'research-agent'  # не UUID, а имя
  - responseMode: 'lastNode'
  - options.allowedUpdates: '["message"]'

Telegram setWebhook:
  POST https://api.telegram.org/bot<token>/setWebhook
  {
    "url": "https://<vps>/webhook/research-agent"
  }
```

### 4.4 Classify-нода (главный routing)

**ВАЖНО:** в Webhook-based workflow данные лежат в `json.body`, не в `json.message`!

```javascript
// Webhook node output: {headers, params, query, body, webhookUrl, executionMode}
const update = $('webhook_yt_research').first().json.body;  // ← body, не message

let route = 'other';
let user_id = null;
let message_id = null;
let text = '';
let is_forwarded = false;

if (update.callback_query) {
  const cq = update.callback_query;
  user_id = cq.from.id;
  message_id = cq.message ? cq.message.message_id : null;
  text = cq.data || '';
  if (text === 'cmd_done') route = 'done';
  else if (text === 'cmd_settings') route = 'settings';
  // ...
} else if (update.message) {
  const msg = update.message;
  user_id = msg.from.id;
  message_id = msg.message_id;
  text = (msg.text || msg.caption || '').trim();
  is_forwarded = !!(msg.forward_from || msg.forward_from_chat || msg.forward_sender_name || msg.forward_signature);
  if (text.startsWith('/')) {
    if (text === '/start' || text.startsWith('/start@')) route = 'start';
    // ...
  } else if (is_forwarded && text.length >= 20) {
    route = 'fraud_inline';
  } else if (text.length >= 1) {
    route = 'ask';
  }
}

return [{ json: { route, user_id, message_id, text, is_forwarded, update } }];
```

### 4.5 Каскад IF-узлов (proven pattern, ONLY via API)

```
Webhook → Classify → IF start
                          ├─ true → HTTP get_state → fmt start → reply start
                          └─ false → IF done
                                       ├─ true → HTTP streak → ...
                                       └─ false → IF goal
                                                    ├─ true → HTTP goal
                                                    └─ false → ...
                                                                └─ false → IF help
                                                                             └─ false → "fallback"
```

- Каждый IF проверяет `route == '<command>'`
- true → специфический HTTP+fmt+reply
- false → следующий IF

**⚠️ Switch-узел НЕ работает через API** — IF-каскад ONLY. Подробнее: MISTAKES §3.8.

### 4.6 HTTP Request нода — паттерн

**Базовый POST к Flask API:**
```
Method: POST
URL: http://host.docker.internal:8080/<project>/<endpoint>
Send Body: true
Specify Body: json
JSON Body: ={{ JSON.stringify({user_id: String($('Classify').first().json.user_id)}) }}
```

**⚠️ ВАЖНО:**
- `JSON.stringify` обязателен! Без него expression отправляется AS STRING
- `host.docker.internal` (внутри контейнера), не `localhost`
- Все параметры явно кастовать: `String(...)`, `Number(...)`, `parseInt(...)`

**Inline keyboard в reply:**
```javascript
// Code node 'fmt_<name>'
const user_id = $('Classify').first().json.user_id;
const data = $('HTTP <endpoint>').first().json;
const body = {
  chat_id: user_id,
  text: data.message,
  reply_markup: {
    inline_keyboard: data.keyboard  // или [[{text, callback_data}]]
  }
};
return [{ json: { body } }];
```

**Reply to Telegram (с inline keyboard через Webhook/Code path):**
```
Method: POST
URL: https://api.telegram.org/bot<TOKEN>/sendMessage
JSON Body: ={{ JSON.stringify($('fmt <name>').first().json.body) }}
```

### 4.7 Inline buttons — полный flow

1. **User нажимает кнопку** → Telegram шлёт `callback_query` с `data: 'cmd_X'`
2. **Classify** распознаёт `cmd_X` → route
3. **IF cmd_X** → HTTP update → fmt → reply
4. **Reply** — `callback_query.answer()` НЕ нужен (только если хочется убрать "loading")

**Регистрация callback'ов** — отдельные `else if` блоки в Classify:
```javascript
else if (text === 'cmd_X') route = 'X';
```

**⚠️ КРИТИЧНО:**
- `callback_data` ≤64 байт (Telegram limit), **рекомендую ≤32 байт для запаса**
- Префиксы: `cmd_`, `setv_`, `schv_`
- Каждый callback_data ДОЛЖЕН быть зарегистрирован в Classify, иначе route = 'other'

### 4.8 n8n connection reference

**⚠️ КРИТИЧНО:** connections ссылаются на `node.name`, НЕ на `node.id`. Переименование ноды ломает connections.

```json
"connections": {
  "Classify": {
    "main": [[{"node": "IF start", "type": "main", "index": 0}]]
  }
}
```

**При переименовании ноды** обновить ВСЕ ссылки в `connections` И в Code nodes (`$('OldName')` → `$('NewName')`).

### 4.9 Активация workflow после PUT

**Проблема:** после PUT workflow может остаться в режиме "активен, но webhook unregistered" — Telegram шлёт updates, n8n не получает.

**Решение:**
```bash
# 1. Deactivate
curl -X POST /api/v1/workflows/<id>/deactivate
sleep 1
# 2. PUT обновлённого workflow
curl -X PUT /api/v1/workflows/<id> -d @wf.json
sleep 1
# 3. Activate (это перерегистрирует webhook)
curl -X POST /api/v1/workflows/<id>/activate
```

**Верификация:**
```bash
curl -s "https://api.telegram.org/bot<token>/getWebhookInfo"
# {"pending_update_count": 0, "url": "https://<vps>/webhook/<name>"}
```

### 4.10 Симуляция Telegram update (отладка без бота)

**Webhook-based (path-based):**
```bash
curl -sk -X POST "https://seefeesnahurid.beget.app/webhook/<name>" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 9999999,
    "message": {
      "message_id": 1,
      "from": {"id": 261540559, "is_bot": false, "first_name": "Test"},
      "chat": {"id": 261540559, "type": "private"},
      "date": 1718260000,
      "text": "/start"
    }
  }'
```

**Telegram Trigger (UUID-based):**
```bash
curl -sk -X POST "https://seefeesnahurid.beget.app/webhook/<webhookId>/webhook" \
  -H "Content-Type: application/json" \
  -d '...'
```

Если n8n принял — вернёт `{"data": [{"json": {...}}]}` (или подобное). Если нет — `webhook is not registered`.

### 4.11 n8n node types cheat-sheet

| Тип | Назначение | Когда использовать |
|---|---|---|
| Webhook | Вход для HTTP POST | Telegram updates (multi-bot) |
| Telegram Trigger | Вход для Telegram | Single bot, UI setup |
| IF | Условный routing | КАЖДЫЙ route = отдельный IF |
| Switch | Multi-way routing | **НЕ через API**, IF-cascade only |
| Code | JavaScript execution | Форматирование body для HTTP Request |
| HTTP Request | Вызов внешних API | Flask API, Telegram API |
| Set | Задать поля в item | Подготовка данных |
| Cron | Расписание | Reminders, daily jobs |
| Telegram | Отправка сообщений | **БЕЗ inline_keyboard** (см. §4.7) |

---

## 5. Flask + Python API

### 5.1 Структура `newton-api.py` (monolith)

```python
#!/usr/bin/env python3
import os, subprocess, time, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
TOKEN = os.environ.get('NEWTON_TOKEN', '')

# === Newton endpoints (legacy) ===
@app.route('/transcribe', methods=['POST'])
def transcribe(): ...
# и т.д.

# === PROJECT ENDPOINTS (auto-patched) ===
import sys
sys.path.insert(0, '/opt/beget/<project>')
try:
    from deploy.add_<project>_endpoints import register_<project>_endpoints
    register_<project>_endpoints(app)
    print(f"[<PROJECT>] endpoints registered OK", flush=True)
except Exception as e:
    print(f"[<PROJECT>] FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
```

### 5.2 `add_<project>_endpoints.py` — паттерн регистрации

```python
"""<Project> endpoints patch for newton-api.py.

Использование (в newton-api.py, перед if __name__):
    import sys
    sys.path.insert(0, '/opt/beget/<project>')
    try:
        from deploy.add_<project>_endpoints import register_<project>_endpoints
        register_<project>_endpoints(app)
    except Exception as e:
        print(f'[<PROJECT>] FAILED: {e}', flush=True)
"""

import os
import logging
from datetime import datetime, date

# Lazy import: если <project> не установлен — endpoints вернут 503
try:
    from <project>.<module> import <func1>, <func2>
    # ...
    PROJECT_AVAILABLE = True
except ImportError as e:
    PROJECT_AVAILABLE = False
    IMPORT_ERROR = str(e)

logger = logging.getLogger('<project>_api')

def register_<project>_endpoints(app):
    """Добавить /<project>/* endpoints к существующему Flask app."""
    from flask import jsonify, request

    @app.route('/<project>/health', methods=['GET'])
    def <project>_health():
        return jsonify({
            'status': 'ok' if PROJECT_AVAILABLE else 'unavailable',
            'service': '<project>-api',
            'version': 'X.Y.Z',
            '<project>_available': PROJECT_AVAILABLE,
            'endpoints': ['/<project>/health', ...]
        })

    @app.route('/<project>/<endpoint>', methods=['POST'])
    def <project>_<endpoint>():
        body = request.get_json(silent=True) or {}
        user_id = str(body.get("user_id", "")).strip()  # ⚠️ Всегда str + strip
        if not user_id:
            return jsonify({"ok": False, "error": "user_id обязателен"}), 400
        try:
            from <project>.<module> import <func>
            result = <func>(user_id, ...)
            return jsonify({"ok": True, **result})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    logger.info(f'<Project> vX.Y endpoints зарегистрированы. PROJECT_AVAILABLE={PROJECT_AVAILABLE}')
    return app
```

### 5.3 Паттерн endpoint с user_id

```python
@app.route('/<project>/<endpoint>', methods=['POST'])
def <project>_<endpoint>():
    body = request.get_json(silent=True) or {}
    user_id = str(body.get("user_id", "")).strip()  # ⚠️ ВСЕГДА
    if not user_id:
        return jsonify({"ok": False, "error": "user_id обязателен"}), 400
    try:
        from <project>.<module> import <func>
        result = <func>(user_id, ...)
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
```

**🚨 Каждый endpoint должен:**
- Принимать `user_id` в body
- Возвращать JSON (не HTML, не plain text)
- Обрабатывать exceptions (try/except)
- Возвращать `usage: {total_today, limit}` для LLM endpoints

### 5.4 Фоновый запуск

```bash
pkill -9 -f newton-api.py 2>/dev/null || true
sleep 2  # ⚠️ недостаточно, лучше 10
cd /opt/beget/n8n
set -a; source .env; set +a  # ⚠️ КРИТИЧНО — без этого env НЕ загружен
nohup python3 newton-api.py > api.log 2>&1 &
sleep 3
```

**⚠️ Без `source .env` переменные `<PROJECT>_YANDEX_GPT_FOLDER_ID`, `NEWTON_TOKEN` и т.д. будут пустыми!**

### 5.5 Health-check

```bash
curl -s http://localhost:8080/<project>/health | python3 -m json.tool
```

Показывает: `status`, `version`, `<project>_available`, `import_error`, `endpoints` (список).

### 5.6 Архитектурное замечание (split vs monolith)

`newton-api.py` — это **monolith**: Flask app с двумя+ «мирами». Это работает, но для нового проекта лучше **разделить**:

**Split (рекомендуется для production):**
- `newton-api.py` — только Newton
- `<project>-api.py` — только Project (отдельный процесс на отдельном порту)
- `traefik` — роутит по host/path

**Monolith (быстрее для MVP):**
- Один `newton-api.py` импортирует несколько `add_*_endpoints` модулей
- Все endpoints в одном процессе
- **Риск:** OOM kill при нескольких активных проектах

### 5.7 Альтернативный паттерн: `Blueprint` (Flask ≥2.0)

```python
# add_<project>_endpoints.py
from flask import Blueprint, jsonify, request

bp_<project> = Blueprint('<project>', __name__, url_prefix='/<project>')

@bp_<project>.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@bp_<project>.route('/<endpoint>', methods=['POST'])
def endpoint(<endpoint>):
    body = request.get_json(silent=True) or {}
    # ...
    return jsonify({...})

def register_<project>_endpoints(app):
    app.register_blueprint(bp_<project>)
```

**Преимущества:**
- Изоляция namespace (нет конфликтов с другими blueprints)
- Регистрация одной строкой
- Легко отключить/удалить blueprint

### 5.8 Auth gate (для LLM-тяжёлых endpoints)

```python
ALLOWED_USERS = set(os.environ.get('ALLOWED_TELEGRAM_USERS', '').split(','))

def _check_auth():
    body = request.get_json(silent=True) or {}
    user_id = str(body.get("user_id", "")).strip()
    if not user_id or user_id not in ALLOWED_USERS:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    return None

@app.route('/<project>/llm_call', methods=['POST'])
def llm_call():
    auth_err = _check_auth()
    if auth_err: return auth_err
    # ... LLM call
```

**Env:** `ALLOWED_TELEGRAM_USERS=261540559,...`

---

## 6. YandexGPT интеграция

### 6.1 Файл `yandex_gpt.py` (общий)

```python
import os
import urllib.request
import urllib.error

YANDEX_GPT_API_KEY = os.environ.get("<PROJECT>_YANDEX_GPT_API_KEY") or os.environ.get("YANDEX_GPT_API_KEY")
YANDEX_GPT_FOLDER_ID = os.environ.get("<PROJECT>_YANDEX_GPT_FOLDER_ID") or os.environ.get("YANDEX_GPT_FOLDER_ID")
YANDEX_GPT_MODEL = os.environ.get("<PROJECT>_YANDEX_GPT_MODEL", "yandexgpt-lite")

URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
DAILY_TOKEN_LIMIT = int(os.environ.get("<PROJECT>_DAILY_BUDGET_TOKENS", 4000))
DAILY_BUDGET_RUB = float(os.environ.get("<PROJECT>_DAILY_BUDGET_RUB", 200))
```

**Приоритет env:** `<PROJECT>_YANDEX_GPT_*` > `YANDEX_GPT_*` (для multi-project на одном VPS).

### 6.2 Системный промпт с state

```python
def _build_system_prompt(state: dict | None) -> str:
    base = (
        "Ты — ИИ-ассистент '<Project>', ... "
        "Тон: дружелюбный, без воды, по делу. "
        "Максимум 6-8 строк, эмодзи умеренно. "
        "НЕ давай индивидуальных рекомендаций, но обсуждай общие вопросы."
    )
    if not state:
        return base + "\n\nПрофиль юзера ещё не настроен."

    parts = [base, "\n\nПрофиль юзера:"]
    if state.get("_name"):
        parts.append(f"• Имя: {state['_name']}")
    # ... остальные поля
    return "\n".join(parts)
```

### 6.3 RAG-lite — последние N events как история

```python
def _get_history(user_id: str, n: int = 5) -> list[dict]:
    """Последние N 'ask' events = conversation history."""
    state = get_store()._get_unlocked(user_id)
    ask_events = [e for e in state.get('events', []) if e.get('type') == 'ask'][-n:]
    return [{'role': e.get('role', 'user'), 'text': e.get('text', '')} for e in ask_events]
```

### 6.4 Daily cap (anti-spam)

**Token-based cap:**
```python
def _check_daily_limit(user_id: str, needed_tokens: int) -> tuple[bool, int]:
    """Returns (ok, total_today)."""
    events = get_events_today(user_id, event_type='ask')
    total_today = sum(e.get('data', {}).get('tokens', 0) for e in events)
    return (total_today + needed_tokens <= DAILY_TOKEN_LIMIT, total_today)
```

**Budget-based cap (RUB):**
```python
def _check_budget(user_id: str, est_tokens: int) -> tuple[bool, float]:
    """Returns (ok, spent_today_rub)."""
    spent_rub = get_spent_today_rub(user_id)  # из events_log
    cost = est_tokens * 0.0002  # ~0.20₽/1K tokens
    return (spent_rub + cost <= DAILY_BUDGET_RUB, spent_rub)
```

### 6.5 Request body (точный формат)

```json
{
  "modelUri": "gpt://<folder_id>/yandexgpt-lite",
  "completionOptions": {
    "stream": false,
    "temperature": 0.6,
    "maxTokens": 500
  },
  "messages": [
    {"role": "system", "text": "..."},
    {"role": "user", "text": "..."}
  ]
}
```

### 6.6 Response — извлечение текста

```python
result = json.loads(response.read())
text = result['result']['alternatives'][0]['message']['text']
usage = result['result']['usage']
# usage: {inputTextTokens, completionTokens, totalTokens}
```

**⚠️ YandexGPT иногда оборачивает JSON:**
```
"text": "```json\n{...}\n```"
```
Парсить regex fallback:
```python
import re
m = re.search(r'\{[\s\S]*\}', text)
if m: return json.loads(m.group(0))
```

### 6.7 Частые ошибки YandexGPT

| Симптом | Причина | Решение |
|---|---|---|
| `Authentication failed` | Wrong API key | Проверить `<PROJECT>_YANDEX_GPT_API_KEY` в .env |
| `Folder not found` (403) | Wrong folder ID | Проверить `<PROJECT>_YANDEX_GPT_FOLDER_ID` в .env |
| `Folder ID не задан` (наша ошибка) | `.env` не подгружен при старте Flask | `set -a; source .env; set +a` перед `nohup` |
| `Invalid model URI` (400) | `gpt://` syntax | `gpt://<folder_id>/yandexgpt-lite` (без `https://`) |
| `Authorization: Api-Key` | `Bearer` вместо `Api-Key` | Заголовок `Authorization: Api-Key <key>` |
| 429 Too Many Requests | Превышен rate limit (~10 RPM) | `time.sleep(2)` между вызовами |
| Token cap hit | `DAILY_TOKEN_LIMIT` exceeded | Возвращать ошибку + `usage.total_today` |
| Ответ — фактически неверный | yandexgpt-lite ≠ GPT-4 | Уточнять system prompt, тестировать edge cases |

---

## 7. Telegram Bot

### 7.1 Bot Menu (persistent commands)

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "start", "description": "🏁 Начать / перезапустить"},
      {"command": "today", "description": "📅 Что сегодня (hero-число + payday)"},
      {"command": "schedule", "description": "📆 Расписание DCA-взносов"}
    ]
  }'
```

**Лимиты:** 100 команд, описание ≤256 символов, названия ≤32 символа, lowercase, a-z0-9_.

### 7.2 Inline keyboard — формат callback_data

```json
{
  "inline_keyboard": [
    [{"text": "✅ Сделал", "callback_data": "cmd_done"}],
    [
      {"text": "💰 Изменить", "callback_data": "cmd_set_monthly_amount"},
      {"text": "📅 Преcет", "callback_data": "cmd_set_schedule_preset"}
    ]
  ]
}
```

**⚠️ callback_data:**
- ≤64 байт (Telegram limit)
- **Рекомендую ≤32 байт** для запаса
- Префиксы: `cmd_`, `setv_`, `schv_`
- **Каждый** `callback_data` ДОЛЖЕН быть зарегистрирован в Classify

### 7.3 parse_mode — НЕ Markdown

**Проблема:** `parse_mode: "Markdown"` ломает API на спецсимволах (звёздочки, подчёркивания).

**Решение:**
- НЕ указывать `parse_mode` (Telegram рендерит plain text)
- ИЛИ `parse_mode: "MarkdownV2"` (с экранированием всех спецсимволов)
- ИЛИ `parse_mode: "HTML"` (проще, но не покрывает всё)

**В текущих проектах:** plain text (без parse_mode). OK, читаемо.

### 7.4 Webhook setup

**Telegram setWebhook (через API):**
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<vps>/webhook/<bot_name>",
    "allowed_updates": ["message", "callback_query"],
    "drop_pending_updates": true
  }'
```

**getWebhookInfo (verification):**
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo" | python3 -m json.tool
# {
#   "url": "https://<vps>/webhook/<bot_name>",
#   "has_custom_certificate": false,
#   "pending_update_count": 0,
#   "max_connections": 40
# }
```

**⚠️ Webhook НЕ работает на http://** — только https://.

**⚠️ Удалить webhook (при переключении на polling или для debug):**
```bash
curl -s "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

### 7.5 Bot commands: 12-15 best practices

Держите Bot Menu ≤15 команд (Telegram scroll). Группируйте:
- **Core:** /start /today /plan /done
- **Insights:** /goal /iis3 /share /digest
- **Config:** /settings /setup /schedule
- **Help:** /help /ask

### 7.6 Anti-patterns Telegram-бота

- ❌ Inline keyboard > 8 кнопок (не помещается на экране)
- ❌ Reply > 4096 символов (обрезается)
- ❌ `parse_mode: "Markdown"` без экранирования
- ❌ `callback_data` > 64 байт
- ❌ Длинные polling loops — используйте webhook
- ❌ Long-running tasks (YandexGPT + 5 сек latency) — сообщить "⌛ Думаю..." через callback answer
- ❌ 2+ Telegram Trigger'а для одного бота (только 1 webhook per bot)
- ❌ `allowed_updates: []` (пусто = только message, не callback_query) — ОБЯЗАТЕЛЬНО включить callback_query

---

## 8. State persistence (multi-user JSON)

### 8.1 Когда JSON OK, когда Postgres

| Объём | Рекомендация |
|---|---|
| ≤500 юзеров | JSON-файл OK, бэкапы ежедневно |
| 500–1000 | Warning zone, нужны автоматические бэкапы |
| >1000 | **MUST** переехать на Postgres / SQLite (для РФ — Яндекс.Таблица для 152-ФЗ) |

### 8.2 Структура state.json

```json
{
  "users": {
    "261540559": {
      "_name": "Сергей",
      "payday_day": 10,
      "monthly_amount": 15000,
      "risk_profile": "balanced",
      "broker": "alfa",
      "iis_type": "A3",
      "goal": {
        "type": "podushka",
        "target_amount": 1000000,
        "target_years": 5.5,
        "current_amount": 175000
      },
      "current_streak": 1,
      "streak_freeze_q": 0,
      "last_payday_done_at": "2026-06-05",
      "last_payday_month": "2026-06",
      "holdings": [],
      "podushka_months": 6.0,
      "pending_setting": null,
      "schedule": {
        "preset": "salary_day",
        "remind_before_days": 3,
        "pause_until": null,
        "history": []
      },
      "created_at": "2026-05-01T...",
      "updated_at": "2026-06-13T..."
    }
  },
  "events": [
    {"ts": "2026-06-13T...", "user_id": "261540559", "type": "payday_done", "data": {}}
  ]
}
```

### 8.3 `state_store.py` — паттерн с thread-safety

```python
import json
import threading
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = '/opt/beget/<project>/data/state.json'
EVENTS_TTL_DAYS = 90
MAX_EVENTS = 5000

DEFAULT_USER_STATE: dict[str, Any] = {
    '_name': 'Юзер',
    'current_streak': 0,
    'streak_freeze_q': 0,
    'last_payday_done_at': None,
    'last_payday_month': None,
    'holdings': [],
    'risk_profile': 'balanced',
    'monthly_amount': 15000,
    'podushka_months': 6.0,
    'payday_day': 5,
    'broker': 'alfa',
    'iis_type': 'A3',
    'goal': {
        'type': 'podushka',
        'target_amount': 600000,
        'target_years': 3.0,
        'current_amount': 175000,
    },
    'pending_setting': None,
    'schedule': {
        'preset': 'salary_day',
        'remind_before_days': 0,
        'pause_until': None,
        'history': [],
    },
    'created_at': None,
    'updated_at': None,
}


class StateStore:
    def __init__(self, path: str | None = None):
        # ⚠️ НЕ path=DEFAULT_STATE_PATH (default оценивается в момент class definition!)
        # Использовать path=None + path or DEFAULT
        self.path = Path(path or DEFAULT_STATE_PATH)
        self.data: dict[str, Any] = {'users': {}, 'events': []}
        self._lock = threading.Lock()
        self._load()

    def _get_unlocked(self, user_id: str) -> dict[str, Any]:
        """Get state without acquiring lock (use when already holding lock)."""
        if user_id not in self.data['users']:
            self.data['users'][user_id] = json.loads(json.dumps(DEFAULT_USER_STATE))
            # ↑ deep copy через JSON (чтобы default не мутировался)
        return self.data['users'][user_id]

    def get(self, user_id: str) -> dict[str, Any]:
        """Thread-safe getter."""
        with self._lock:
            return self._get_unlocked(user_id)

    def update(self, user_id: str, **kwargs) -> dict:
        """Thread-safe update. ⚠️ Не вызывать self.get() под self._lock!"""
        with self._lock:
            state = self._get_unlocked(user_id)
            state.update(kwargs)
            state['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            self._save()
            return state
```

**🚨 КРИТИЧНО:** никогда `def f(x=CONST)` — всегда `def f(x=None); self.x = x or CONST`. Подробнее: MISTAKES §5.1.

### 8.4 Синглтон-доступ

```python
_store = None

def get_store() -> StateStore:
    global _store
    if _store is None:
        _store = StateStore()
    return _store
```

### 8.5 Migration со старого формата

```python
def _load(self):
    if not self.path.exists():
        self._save()
        return
    try:
        with open(self.path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        # Backward compat: если это старый формат (плоский state), мигрируем
        if 'users' not in loaded:
            loaded = {
                'users': {loaded.get('user_id', 'unknown'): {k: v for k, v in loaded.items() if k != 'user_id'}},
                'events': [],
            }
            logger.info('Migrated old state format to multi-user (backward compat)')
        self.data = loaded
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f'Failed to load state: {e}, using defaults')
        self.data = {'users': {}, 'events': []}
```

**При добавлении нового поля в DEFAULT_USER_STATE** — миграция обязательна (defensive read):
```python
state = get_store()._get_unlocked(user_id)
# ИЛИ
state = get_store().get(user_id)
state.get('new_field', DEFAULT_USER_STATE['new_field'])  # defensive
```

### 8.6 Events log (TTL + cap)

```python
EVENTS_TTL_DAYS = 90
MAX_EVENTS = 5000

def log(user_id: str, event_type: str, data: dict) -> dict:
    store = get_store()
    event = {
        'ts': datetime.utcnow().isoformat() + 'Z',
        'user_id': user_id,
        'type': event_type,
        'data': data,
    }
    with store._lock:
        store.data['events'].append(event)
        # TTL
        cutoff = datetime.utcnow() - timedelta(days=EVENTS_TTL_DAYS)
        store.data['events'] = [
            e for e in store.data['events']
            if datetime.fromisoformat(e['ts'].rstrip('Z')) > cutoff
        ]
        # Cap
        if len(store.data['events']) > MAX_EVENTS:
            store.data['events'] = store.data['events'][-MAX_EVENTS:]
        store._save()
    return event
```

### 8.7 Backup

```bash
# Ручной бэкап
/workspace/.vps-helper.sh get /opt/beget/<project>/data/state.json /workspace/backups/state_$(date +%Y%m%d).json

# Cron (ежедневно)
0 3 * * * /workspace/.vps-helper.sh get /opt/beget/<project>/data/state.json /workspace/backups/state_$(date +\%Y\%m\%d).json
```

---

## 9. Memory topics — что и где фиксировать

### 9.1 Что фиксировать в memory

| Тема | Когда | Где |
|---|---|---|
| Bash pitfalls | После каждой неочевидной башизмы | `bash-pitfalls` |
| n8n API quirks | После каждой нестандартной находки | `n8n-api-quirks` |
| Self-improve | После каждой ошибки → извлечь урок | `self-improve-on-errors` |
| Telegram bot menu | Когда настраиваешь persistent commands | `telegram-bot-menu` |
| VPS access | Когда настраиваешь новый VPS / меняются секреты | `beget-vps-access` (только пути, НЕ пароли) |

### 9.2 Антипаттерн memory

❌ Хранить в memory:
- Конкретные пароли
- API keys (полные)
- Имена юзеров
- Финансовые данные
- Длинные stack traces
- Hardcoded secrets

✅ Хранить в memory:
- Имена env-переменных
- Структуры путей
- Паттерны и шаблоны
- Ссылки на источники
- Да/нет про «работает ли X»

### 9.3 Формат topic

```markdown
# bash-pitfalls

## 2026-06-13: sshpass теряется после рестарта
- **Симптом:** `sshpass: command not found`
- **Причина:** пакет не предустановлен, слетает после обновлений
- **Решение:** 
  ```bash
  apt-get update && apt-get install -y sshpass
  ```
- **Файлы:** `/root/.mavis/secrets/beget_ssh` тоже слетает — пересоздавать
```

### 9.4 ⚠️ Memory topics могут пустеть между сессиями

**Наблюдение:** `memory_topic_read` иногда возвращает пустоту между сессиями в некоторых runtime.

**Компенсация:**
- Все критичные уроки — в **файлах** (ENVIRONMENT.md, MISTAKES.md)
- `bash-pitfalls`, `n8n-api-quirks` — best-effort, не source of truth
- Если memory tool не работает — не паниковать, писать в файл

### 9.5 META-урок: записывать в memory в ТОМ ЖЕ turn

**Самая частая meta-ошибка:** перечислить уроки в ответе чата, но **не записать** в memory topic. Следующая сессия начинается с нуля.

**Правило:** урок в `memory_topic_edit`/`_append` в **том же turn**, что и обнаружение.

---

## 10. Тестирование

### 10.1 Локальный pytest

```bash
cd /workspace/<project>
PYTHONPATH=src python3 -m pytest tests/ -v
```

⚠️ `PYTHONPATH=src` обязателен (src/<project>/* а не ./<project>/*).

### 10.2 Если pytest нет

```bash
pip3 install pytest --break-system-packages
```

(Нет venv — system pip; для prod лучше venv, но для разработки ОК)

### 10.3 Конвенция тестов

```python
# tests/test_<module>.py
import pytest
from <project>.<module> import <func>


class TestEdgeCase:
    def test_<case>(self):
        result = <func>(...)
        assert result == expected
```

**Edge cases обязательны:** empty, null, max, min, переходные значения.

### 10.4 Чеклист перед коммитом

- [ ] `pytest tests/ -v` — все pass
- [ ] Новые edge cases покрыты
- [ ] Hardcoded значения НЕ добавлены
- [ ] Imports обновлены
- [ ] Docstrings обновлены
- [ ] `find . -name __pycache__ -exec rm -rf {} +` (избежать stale .pyc)

### 10.5 Тесты на проде (smoke test)

```bash
# Health
curl -s http://localhost:8080/<project>/health | python3 -m json.tool

# Каждый endpoint
curl -s -X POST http://localhost:8080/<project>/<endpoint1> -H 'Content-Type: application/json' -d '{"user_id": "261540559"}'
curl -s -X POST http://localhost:8080/<project>/<endpoint2> -H 'Content-Type: application/json' -d '{"user_id": "261540559", "text": "test"}'
```

**🚨 Правило:** после ЛЮБОГО deploy — минимум 1 smoke test. Если 500 — откатывать.

---

## 11. CI/CD без CI

### 11.1 Deploy flow (manual)

```
1. Local edit
   ↓ cd /workspace/<project>
2. Local tests
   ↓ PYTHONPATH=src python3 -m pytest tests/
3. SCP to VPS (per file)
   ↓ /workspace/.vps-helper.sh file_cp <local> <remote>
4. Restart Flask
   ↓ pkill -9 -f newton-api.py
   ↓ sleep 10  (не 2-3, FIN_WAIT)
   ↓ cd /opt/beget/n8n
   ↓ set -a; source .env; set +a
   ↓ nohup python3 newton-api.py > api.log 2>&1 &
5. Smoke test
   ↓ curl http://localhost:8080/<project>/health
6. n8n update (if workflow changed)
   ↓ PUT /api/v1/workflows/<id> with new JSON
   ↓ Deactivate → Activate cycle
   ↓ Verify: getWebhookInfo.pending_update_count == 0
7. Manual test in Telegram
   ↓ @<bot_username>
```

### 11.2 Что можно автоматизировать

- Bash-скрипт `deploy.sh` (в `/opt/beget/<project>/deploy/`) — SCP + restart + smoke test
- Git pre-commit hook: `pytest tests/`
- Cron: `cp state.json backups/state_$(date +%Y%m%d).json` daily
- Health-check cron: каждые 5 мин `curl /<project>/health` → алерт если не 200

### 11.3 Что НЕ стоит автоматизировать сразу

- Multi-server deploy
- Rolling updates
- Auto-rollback (только если F&F активны и есть SLA)
- Canary deploys (overkill для 1.9 GB VPS)

---

## 12. YouTube subs — источники

### 12.1 Приоритет надёжности (на 2026-06)

| Источник | Надёжность | Скорость | Качество subs |
|---|---|---|---|
| **yt-dlp (Android VR client)** | ✅ **PRIMARY** | 1.5-2s | Отличное (auto + manual) |
| Piped (community mirrors) | ❌ **DEAD** (с 2026-06) | — | — |
| Invidious (community) | ❌ **DEAD** (с 2026-06) | — | — |
| YouTube Data API v3 | ⚠️ Требует API key, есть quota | 200ms | Только captions.list, не VTT |
| Прямой googlevideo.com | ❌ **ЗАБЛОКИРОВАН** на Beget (IP) | — | — |

**Вывод:** **yt-dlp — единственный надёжный источник** в этой среде.

### 12.2 yt-dlp оптимальный pattern

```bash
# 1. Получить metadata (с auto-generated subs URL)
yt-dlp --dump-single-json --skip-download "https://youtu.be/<id>" > /tmp/meta.json

# 2. Извлечь URL VTT из meta.json
sub_url=$(jq -r '.requested_subtitles.ru[0].url // .requested_subtitles.en[0].url' /tmp/meta.json)

# 3. Скачать VTT
curl -sL "$sub_url" -o /tmp/subs.vtt

# 4. Парсить VTT → plain text (см. §12.3)
```

**Время:** ~1.5s (meta) + ~2s (VTT) = **~3.5s total**.

**❌ НЕ использовать `--write-auto-subs`** — качает всю video metadata, ~60s.

### 12.3 VTT → plain text parser

```python
import re

def vtt_to_text(vtt_content: str) -> str:
    """VTT → plain text (убрать timestamps и cue identifiers)."""
    lines = []
    for line in vtt_content.split('\n'):
        # Skip timestamps (00:00:00.000 --> 00:00:05.000)
        if re.match(r'^\d{2}:\d{2}:\d{2}', line):
            continue
        # Skip empty lines and cue identifiers
        if not line.strip() or line.strip().isdigit():
            continue
        # Skip WEBVTT header
        if line.startswith('WEBVTT'):
            continue
        lines.append(line.strip())
    return '\n'.join(lines)
```

### 12.4 ⚠️ Критичные паттерны обработки JSON

```python
# ❌ BAD: .get(key, default) возвращает None если value == None
_subs = _meta.get('requested_subtitles', {}).get(prefer_lang)
# Если _meta['requested_subtitles'] == None (НЕ отсутствует, а ЯВНО null) → .get падает

# ✅ GOOD: (x or default) срабатывает и для None, и для отсутствующего ключа
_subs = (_meta.get('requested_subtitles') or {}).get(prefer_lang)
```

**Правило:** при работе с JSON API ВСЕГДА оборачивай `.get(key, default)` в `(x or default)`.

### 12.5 Установка yt-dlp на VPS

```bash
pip3 install --break-system-packages yt-dlp
# или
pip3 install --upgrade --break-system-packages yt-dlp  # обновить
```

**⚠️ yt-dlp часто обновляется** (YouTube ротирует endpoint'ы). Проверять раз в месяц.

---

## 13. GitHub — auth и scopes

### 13.1 Два способа push

| Метод | Когда | Плюсы | Минусы |
|---|---|---|---|
| **HTTPS + `gh auth`** | По умолчанию | Не нужен SSH-ключ, OAuth scope | Требует `gh auth setup-git` |
| **SSH + `gh ssh-key add`** | Multi-device, CI/CD | Ключ reusable | Нужно `ssh-keygen` + `gh ssh-key add` |

### 13.2 HTTPS + gh auth (рекомендуется)

```bash
# 1. gh auth login (один раз)
gh auth login --web --git-protocol https

# 2. Настроить git credential helper
gh auth setup-git

# 3. remote URL — HTTPS
git remote set-url origin https://github.com/<user>/<repo>.git

# 4. Push
git push origin main
```

**🚨 `gh auth login --git-protocol ssh` НЕ настраивает SSH-ключ!** Использует OAuth (HTTPS). Флаг `--git-protocol ssh` — HINT для вывода, реальный SSH ключ НЕ создаётся.

### 13.3 SSH + gh ssh-key add

```bash
# 1. Сгенерировать ключ
ssh-keygen -t ed25519 -C "<comment>" -f ~/.ssh/<alias> -N ""

# 2. Добавить в GitHub
gh ssh-key add ~/.ssh/<alias>.pub -t "<title>"

# 3. remote URL — SSH
git remote set-url origin git@github.com:<user>/<repo>.git

# 4. Push
git push origin main
```

### 13.4 ⚠️ НЕ класть токены в git remote URL

**🚨 Антипаттерн:**
```bash
# ❌ ТОКЕН В URL = утечка
git remote add origin https://ghp_TOKEN@github.com/<user>/<repo>.git
```

**После push проверить:**
```bash
git remote -v  # НЕ должен содержать https://TOKEN@
```

### 13.5 OAuth scope: `workflow` для GitHub Actions

**Проблема:** при push в репо с `.github/workflows/*.yml` → ошибка 403 если scope `workflow` не выдан.

**Решение:**
```bash
# Переавторизоваться с правильным scope
gh auth refresh -h github.com -s workflow
```

**Если workflow не нужен** — проще удалить `.github/workflows/*.yml` перед push, чем возиться со scope.

### 13.6 `.gitignore` паттерны

**🚨 Паттерн `kb/` матчит ЛЮБУЮ `kb/` в дереве:**
```
# .gitignore
kb/                  # ❌ матчит packages/kb/ тоже
/packages/kb/        # ✅ матчит только /packages/kb/
```

**Правило:** `pattern/` (без `/` в начале) матчит во всех поддиректориях; `/pattern/` (с `/` в начале) матчит только от корня.

### 13.7 Что НЕ коммитить

- `__pycache__/` (добавить в `.gitignore`)
- `*.pyc`
- `.env` (только `.env.example` с плейсхолдерами)
- `secrets/`, `*.key`, `*.pem`
- `data/state.json` (state — runtime, не код)
- `venv/`, `.venv/`
- `node_modules/`
- `*.log`

---

## 14. Cheatsheet — copy-paste команды

### 14.1 С нуля — настроить VPS helper

```bash
# 1. Установить sshpass
apt-get update && apt-get install -y sshpass

# 2. Создать secret
mkdir -p /root/.mavis/secrets
# ⚠️ СОЗДАТЬ ФАЙЛ РУКАМИ через read/PM, НЕ через heredoc в chat
chmod 600 /root/.mavis/secrets/beget_ssh

# 3. Создать helper
cat > /workspace/.vps-helper.sh <<'BASH'
#!/bin/bash
set -e
HOST="seefeesnahurid.beget.app"
USER="root"
PASS=$(cat /root/.mavis/secrets/beget_ssh | grep password= | cut -d= -f2-)
if [ "$1" = "file_cp" ]; then
    sshpass -p "$PASS" scp -o StrictHostKeyChecking=no -r "$2" "$USER@$HOST:$3"
elif [ "$1" = "get" ]; then
    sshpass -p "$PASS" scp -o StrictHostKeyChecking=no "$USER@$HOST:$2" "$3"
else
    sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 "$USER@$HOST" "$@"
fi
BASH
chmod +x /workspace/.vps-helper.sh

# 4. Тест
/workspace/.vps-helper.sh "echo OK"
```

### 14.2 Настроить n8n workflow

```bash
# Получить API key
/workspace/.vps-helper.sh "docker exec -e PGPASSWORD=<pg_pass> n8n-postgres-1 psql -U root -d n8n -c \"SELECT \\\"apiKey\\\" FROM user_api_keys\""

# List workflows
N8N_KEY="..."
curl -sk -H "X-N8N-API-KEY: $N8N_KEY" "https://<vps>/api/v1/workflows" | python3 -m json.tool

# Activate
curl -sk -X POST -H "X-N8N-API-KEY: $N8N_KEY" "https://<vps>/api/v1/workflows/<id>/activate"
```

### 14.3 Deploy Python файла

```bash
/workspace/.vps-helper.sh file_cp /workspace/<project>/src/<project>/<file>.py /opt/beget/<project>/src/<project>/<file>.py

# Restart
/workspace/.vps-helper.sh "pkill -9 -f newton-api.py; sleep 10; cd /opt/beget/n8n; set -a; source .env; set +a; nohup python3 newton-api.py > api.log 2>&1 &"
sleep 3

# Smoke test
/workspace/.vps-helper.sh "curl -s http://localhost:8080/<project>/health"
```

### 14.4 Deploy n8n workflow

```bash
# 1. PUT (с очищенными полями)
N8N_KEY="..."
python3 -c "
import json
d = json.load(open('/workspace/wf.json'))
out = {k: d[k] for k in ('name','nodes','connections','settings')}
json.dump(out, open('/tmp/wf_clean.json', 'w'), ensure_ascii=False)
"
curl -sk -X PUT -H "X-N8N-API-KEY: $N8N_KEY" -H 'Content-Type: application/json' \
  "https://<vps>/api/v1/workflows/<id>" -d @/tmp/wf_clean.json

# 2. Deactivate → Activate
curl -sk -X POST -H "X-N8N-API-KEY: $N8N_KEY" "https://<vps>/api/v1/workflows/<id>/deactivate"
sleep 1
curl -sk -X POST -H "X-N8N-API-KEY: $N8N_KEY" "https://<vps>/api/v1/workflows/<id>/activate"
```

### 14.5 Тест Telegram-бота

```bash
# Отправить сообщение
curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": <user_id>, "text": "/start"}'

# Проверить webhook
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo" | python3 -m json.tool

# Установить webhook
curl -s "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://<vps>/webhook/<name>", "allowed_updates": ["message", "callback_query"]}'

# Удалить webhook
curl -s "https://api.telegram.org/bot<TOKEN>/deleteWebhook"
```

### 14.6 Симуляция Telegram update

```bash
curl -sk -X POST "https://<vps>/webhook/<name>" \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 9999999,
    "message": {
      "message_id": 1,
      "from": {"id": 261540559, "is_bot": false, "first_name": "Test"},
      "chat": {"id": 261540559, "type": "private"},
      "date": 1718260000,
      "text": "/start"
    }
  }'
```

### 14.7 Получить n8n API key

```bash
# Из Postgres контейнера
/workspace/.vps-helper.sh "docker exec -e PGPASSWORD=\$(grep POSTGRES_PASSWORD /opt/beget/n8n/.env | cut -d= -f2) n8n-postgres-1 psql -U root -d n8n -t -c \"SELECT \\\"apiKey\\\" FROM user_api_keys WHERE label='<label>'\""
```

---

## 15. Чеклист перед продакшн-деплоем

### 15.1 Локально

- [ ] `pytest tests/ -v` — все pass
- [ ] Нет hardcoded секретов
- [ ] Логи не пишут в `print()` (используй `logger`)
- [ ] Errors обрабатываются (try/except в endpoints)
- [ ] Edge cases покрыты тестами
- [ ] Docstring на каждом новом публичном API
- [ ] `find . -name __pycache__ -exec rm -rf {} +` (избежать stale .pyc)

### 15.2 На VPS

- [ ] `curl http://localhost:8080/<project>/health` → `status: ok`
- [ ] Все endpoints возвращают корректный JSON
- [ ] State файл бэкапнут
- [ ] Workflow активирован (не "failed validation")
- [ ] `getWebhookInfo.pending_update_count == 0`
- [ ] Bot menu зарегистрирован (`getMyCommands` есть)
- [ ] API logs чистые (нет 500-ок)
- [ ] Disk usage на VPS <80% (state.json + logs)
- [ ] YandexGPT лимиты не превышены
- [ ] Все credentials есть в `.env` (folder_id, API key, bot token)
- [ ] `set -a; source .env; set +a` выполнен перед `nohup`

### 15.3 Перед F&F (Friends & Family)

- [ ] 5/5 PM сделал все core commands (hard gate)
- [ ] Weekly digest понятен (если есть)
- [ ] `/ask` возвращает релевантные ответы
- [ ] fraud-check ловит реальные скамы (если есть)
- [ ] 0 critical errors за 7 дней

---

## 16. Частые «How to»

### 16.1 Как добавить новую команду в Bot Menu

```bash
# 1. Classify → новая команда
# 2. Bot Menu
curl -s "https://api.telegram.org/bot<TOKEN>/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{"commands": [..., {"command": "newcmd", "description": "..."}]}'

# 3. n8n: Classify + IF-каскад + HTTP/format/reply
```

### 16.2 Как добавить новое поле в state

1. `state_store.py`: добавить в `DEFAULT_USER_STATE`
2. Миграция: при следующей `_load()` новый user получит default
3. Endpoint для update: `POST /<project>/<endpoint> {user_id, field, value}`
4. UI: `/settings` → новая inline-кнопка
5. Тесты на дефолтное значение

### 16.3 Как добавить новый n8n workflow

1. UI: New Workflow → добавить nodes → save
2. Получить JSON: `GET /api/v1/workflows/<id>` (auto-save to JSON file)
3. Edit JSON локально (mass changes)
4. `PUT /api/v1/workflows/<id>` (с `{name, nodes, connections, settings}` only)
5. `Deactivate → Activate`
6. Verify: `getWebhookInfo.pending_update_count == 0`

### 16.4 Как сделать inline-кнопку «назад»

```json
[{"text": "⬅ Назад", "callback_data": "cmd_<previous>"}]
```

В Classify: добавить `else if (text === 'cmd_<previous>') route = '<previous>';`

### 16.5 Как добавить reminder cron (3 дня до payday)

1. n8n: Cron Trigger (daily 9:00 MSK)
2. HTTP: `GET /opt/beget/<project>/data/state.json` (или через `/<project>/get_state`)
3. Проверить: `payday_day - today_day == 3` AND `schedule.remind_before_days == 3`
4. Если да → sendMessage с напоминанием
5. Если `pause_until != null` → skip

### 16.6 Как протестировать YandexGPT ответ

```bash
# Через Flask API
curl -s -X POST http://localhost:8080/<project>/ask \
  -H "Content-Type: application/json" \
  -d '{"user_id": "261540559", "text": "Что такое ИИС-3?"}' | python3 -m json.tool
```

### 16.7 Как прочитать логи n8n

```bash
/workspace/.vps-helper.sh "docker logs n8n-n8n-1 2>&1 | tail -30"
```

Типичные логи:
- `Workflow activation failed validation` — webhook unregistered (см. §4.9)
- `Received request for unknown webhook` — Telegram шлёт на несуществующий webhook
- `Calling Error Workflow for ...` — execution error в node
- `Pruning old insights data` — нормально, housekeeping

### 16.8 Как посмотреть execution конкретного workflow

```bash
N8N_KEY="..."
WORKFLOW_ID="..."
curl -sk -H "X-N8N-API-KEY: $N8N_KEY" \
  "https://<vps>/api/v1/executions?workflowId=${WORKFLOW_ID}&limit=10" | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)
for e in d.get('data', []):
    print(f\"id={e['id']} status={e['status']} started={e['startedAt']} stopped={e.get('stoppedAt')}\")
"
```

### 16.9 Как добавить yt-dlp в новый проект

```bash
# На VPS
pip3 install --break-system-packages yt-dlp

# В requirements.txt
yt-dlp>=2025.6.0
```

```python
# В Python
import subprocess, json
def get_subs(url: str, lang: str = 'ru') -> str:
    """Получить subs через yt-dlp."""
    result = subprocess.run(
        ['yt-dlp', '--dump-single-json', '--skip-download', url],
        capture_output=True, text=True, timeout=30
    )
    meta = json.loads(result.stdout)
    subs = (meta.get('requested_subtitles') or {}).get(lang)
    if not subs:
        # fallback на en
        subs = (meta.get('requested_subtitles') or {}).get('en')
    if not subs:
        return ''
    # Скачать VTT
    vtt_url = subs[0]['url']
    import requests
    vtt = requests.get(vtt_url).text
    return vtt_to_text(vtt)
```

### 16.10 Как сделать «default opinionated» layout

Принцип: 1 layout = 1 Telegram message. Содержит:
- Hero-число (главный инсайт)
- Status (countdown/streak/рынок)
- Progress (% к цели)
- Action hint (`/done` / `/plan`)

≤ 8 строк, ≤ 4096 символов. Inline keyboard внизу.

---

## 17. Reference URLs

| Сервис | URL |
|---|---|
| VPS | `https://seefeesnahurid.beget.app/` |
| n8n API | `https://seefeesnahurid.beget.app/api/v1/` |
| Telegram API | `https://api.telegram.org/bot<token>/` |
| YandexGPT | `https://llm.api.cloud.yandex.net/foundationModels/v1/completion` |
| yt-dlp releases | https://github.com/yt-dlp/yt-dlp/releases |
| Piped instances (community list) | https://piped-instances.kavin.rocks/ (если живой) |

---

## 18. Что читать ПЕРВЫМ в новой сессии

**Порядок чтения файлов при старте нового проекта:**

1. **`/workspace/ENVIRONMENT.md` §0** (контекст PM) — 2 мин
2. **`/workspace/MISTAKES.md` §13** (self-check чеклист) — 5 мин
3. **`/workspace/MISTAKES.md` §14** (top-10 самых частых) — 3 мин
4. **`/workspace/ENVIRONMENT.md` §4.1-4.11** (n8n cheatsheet) — 5 мин
5. **`/workspace/ENVIRONMENT.md` §15** (pre-deploy checklist) — 2 мин
6. **Memory topic `bash-pitfalls`** (если есть) — 3 мин
7. **Memory topic `n8n-api-quirks`** (если есть) — 3 мин

**Итого: ~25 мин на "разогрев".** Потом — нормальная работа.

**🚨 Если сессия новая и secrets file пропал** — ПЕРВАЯ КОМАНДА:
```bash
ls /root/.mavis/secrets/ 2>/dev/null && echo "OK" || echo "RESTORE NEEDED"
```

Если "RESTORE NEEDED" — `apt-get install -y sshpass` + создать `beget_ssh` руками (через PM).

---

**Версия файла:** 3.0 (unified) · Дата: 2026-06-16
**Основа:** DEVELOPMENT_PLAYBOOK.md (Капитал) + ENVIRONMENT.md (research-agent) — объединены, секреты вычищены, добавлены уникальные разделы из каждого.
**Следующая ревизия:** при добавлении новой секции (например, 19. Process management для SaaS-проектов).
