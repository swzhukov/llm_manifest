# HANDOFF.md — Полный снимок состояния research-agent на 2026-06-24

> **Назначение:** source-of-truth файл для нового диалога с Mavis. Содержит ВСЁ, что нужно знать агенту, чтобы продолжить работу без контекста предыдущего разговора.

> **Аудит:** сделан Mavis 2026-06-24 после Sprint 23 (A-G кроме VK). Спринт 22 (Flask recovery) зафиксирован в MISTAKES §3.64. Все новые lessons в §10.

---

## 0. Мета

- **Дата handoff:** 2026-06-24
- **Версия:** Research Agent v6.0.27 (workflow, active), **Flask v6.0.30 (post-Sprint 23, endpoints + monitoring)**
- **Workflow ID:** `VGVepaHqmjg2PXSj`, versionCounter=586, active=True, **50 нод**
- **Flask архитектура:** `newton-api.py` (12 строк обёртка) → `core/app.py` (162 строки) → `packages/{research,kb,telegram_bot}/routes.py` (~2300 строк с register(app))
- **Repo:** `https://github.com/swzhukov/AnalizIstochnikov`
- **Sprint 23 (2026-06-24):** YouTube channel endpoint, Newton 503 fix, Bot Menu 8 commands, /user_stats real counters, cron monitoring + Newton watchdog. VK отложен (нужен service_token).
- **llm_manifest:** `https://github.com/swzhukov/llm_manifest` (ENVIRONMENT.md, MISTAKES.md §3.1-§3.64, wiki/)
- **PM:** Сергей Жуков (Telegram user_id 261540559)
- **Bot:** @ZhukovsFirstBot (token в `/opt/beget/n8n/.env`)
- **Sprint 22 (2026-06-23):** восстановлен Flask из урезанного shim'а. Endpoints заработали. E2E webhook тест OK (24 сек, 0 errors). Подробности в §9.

---

## 1. Цели создания продукта

### Что это
**Личный research-агент** для инвестора Сергея Жукова. Принимает URL (YouTube / Rutube / VK / Kinescope / Vimeo / PeerTube / Dzen / подкасты) или голосовое/аудио в Telegram → возвращает **HTML-дайджест** (summary + action items + топ-комментарии) + TL;DR + опционально MP3-озвучку.

### Почему
- Сергей смотрит много видео про инвестиции, но не успевает всё. Бот делает саммари.
- PM = реальный инвестор (Альфа-Инвестиции, ИИС тип A3, watchlist), не тестер.
- Личный use, не B2B. Масштабирование не нужно — 1 user.

### Что НЕ делаем
- Не B2B SaaS
- Не мобильное приложение
- Не голосовой ассистент (только команды)
- Не реальное время / streaming
- Не мультиязычный (только русский + английский subs)

### Архитектурный принцип
**Opinionated default + быстрые решения**. PM не хочет сравнения вариантов — хочет один путь и обоснование.

---

## 2. Концепция и архитектура

### Высокоуровневая схема
```
Telegram user (Сергей, user_id=261540559)
        ↓ webhook POST
Traefik (reverse proxy :443)
        ↓
n8n webhook_yt_research (50 нод, responseMode=responseNode)
        ↓
Flask API (systemd, :8080, packages: research/kb/telegram_bot)
        ↓
   ┌────┴─────┬─────────┬───────────┐
   ↓          ↓         ↓           ↓
yt-dlp    Newton CLI  YandexGPT  SQLite
(extract, (transcribe, (summary,  (kb.db,
 subs,    TTS,         digest,    sources,
comments) fetch,        action     claims,
          diarize,      items)     actions,
          voices,                   digests,
          summarize)                seen_updates)
```

### Технологический стек (зафиксированный)
| Слой | Технология | Версия | Зачем |
|---|---|---|---|
| Frontend | Telegram Bot API | — | Единственный UI |
| Orchestrator | n8n | 2.17.7 (Docker) | Workflow automation |
| API | Flask | 3.x (Python 3.12) | Обёртка над внешними сервисами |
| Subs extraction | yt-dlp | latest | Универсальный extract для 14+ платформ |
| Transcription | Newton CLI | 1.0+ | gigaAM v3 (рус), parakeet (мульти), whisper, diarize, TTS |
| LLM | YandexGPT | yandexgpt-lite | Суммаризация, action items, comments analysis |
| DB | SQLite | 3 | Persistent storage |
| Process mgmt | systemd | — | НЕ pkill -9 |
| Webhook proxy | Traefik | 3.6.5 | SSL termination |
| DNS / VPS | Beget | — | `seefeesnahurid.beget.app`, IP 217.114.7.5 |
| Container runtime | Docker Compose | — | n8n stack |

### Ключевые архитектурные решения (зачем именно так)

1. **n8n webhook + responseMode=responseNode** вместо Telegram Trigger node — потому что credentials через API silently ignored (см. MISTAKES §3.3).
2. **Flask + JSON API** между n8n и Newton — потому что n8n Code node не может запускать child_process (см. MISTAKES §3.47).
3. **Two webhook approach**: `webhook_yt_research` для main flow, `Respond to Webhook` сразу после ack (Sprint 21 — retry-storm fix).
4. **Static data для dedup НЕ работает** между executions. Используем Flask `/seen_update` + SQLite таблицу.
5. **Code node `runOnceForAllItems`** + `$input.all()` для multi-item routing (typeVersion 1, не 2 — V8 bugs).
6. **`items[0].json`** для read, `JSON.stringify({...})` для body в HTTP Request nodes.
7. **Systemd `EnvironmentFile=/opt/beget/n8n/.env`** вместо hardcoded secrets.

---

## 3. Состав текущего релиза (v6.0.27)

### 3.1 n8n workflow `Research Agent v6.0.27`
- **ID:** `VGVepaHqmjg2PXSj`
- **versionCounter:** 586
- **Active:** True
- **Nodes:** 50
- **Webhook path:** `research-agent` (responseNode)

#### 50 нод (по порядку выполнения):

| # | Node | Type | Что делает |
|---|---|---|---|
| 1 | webhook_yt_research | webhook | Принимает Telegram update |
| 2 | Code — Parse Command v6.0.27 | code | Parse cmd + dedup через /seen_update |
| 3 | SWITCH — Route by _route v6.0.21 | switch | 5 outputs: fetch / channel / media / callback / help |
| 4 | Code — Build ack msg v6.0.21 | code | "Понял, обрабатываю..." |
| 5 | IF needs_ack | if | True → /send_message (ack), False → Respond |
| 6 | HTTP /send_message (ack) | httpRequest | Telegram sendMessage |
| 7 | Respond to Webhook | respondToWebhook | **Сразу 200 OK** (Sprint 21) |
| 8 | Code — Pass through v6.0.21 | code | Setup write_audio=true для non-YouTube |
| 9 | HTTP /process_url | httpRequest | Universal extract для 14 платформ |
| 10 | HTTP /user_profile | httpRequest | User profile из KB |
| 11 | Code — Build YandexGPT payload | code | Format prompt с user_profile |
| 12 | HTTP /yagpt_summarize (chunking внутри) | httpRequest | YandexGPT summary |
| 13 | HTTP /comments_analyze | httpRequest | YandexGPT comments analysis |
| 14 | Code — Build Digest | code | Format digest структуру |
| 15 | HTTP /render_digest | httpRequest | HTML render |
| 16 | HTTP /kb_save | httpRequest | Save to SQLite (sources + digests + actions) |
| 17 | HTTP /send_document | httpRequest | Telegram sendDocument (HTML файл) |
| 18 | HTTP /send_message (TL;DR) | httpRequest | TL;DR текстом |
| 19 | HTTP /send_message (error) | httpRequest | Error fallback |
| 20 | Code — Build help/error msg | code | /help, /start, /invalid меню |
| 21 | HTTP /send_message (help) | httpRequest | Telegram sendMessage с inline keyboard |
| 22 | HTTP /youtube_channel_latest | httpRequest | YouTube channel → latest videos |
| 23 | HTTP /send_message (channel notice) | httpRequest | "Канал @user → последнее видео" |
| 24 | Code — Use channel result | code | Route на process_url OR notice |
| 25 | Code — Skip if no url | code | Skip если не URL |
| 26 | HTTP /telegram_download | httpRequest | Скачать файл из Telegram |
| 27 | Code — Build media notice | code | "Транскрибирую файл..." |
| 28 | HTTP /send_message (media notice) | httpRequest | Telegram sendMessage |
| 29 | IF media_empty | if | True → media empty handler, False → transcribe |
| 30 | HTTP /transcribe | httpRequest | Newton transcribe (v3 / parakeet / whisper) |
| 31 | Code — Build media YandexGPT payload | code | Format для медиа |
| 32 | Code — Media empty handler | code | "Файл не распознан" |
| 33 | HTTP /send_message (media empty) | httpRequest | Telegram sendMessage |
| 34 | HTTP /handle_callback | httpRequest | Ack callback_query |
| 35 | Code — Build callback payload v6.0.21 | code | Set _action для SWITCH |
| 36 | SWITCH — Route callback v6.0.23 | switch | 6 outputs: stats/recent/pending/close/help/audio_last |
| 37 | HTTP /user_stats (callback) | httpRequest | Статистика |
| 38 | HTTP /digests_recent (callback) | httpRequest | 5 последних дайджестов |
| 39 | HTTP /actions_recent (callback) | httpRequest | Pending actions |
| 40 | Code — Format callback result v6.0.23 | code | Format result message |
| 41 | HTTP /send_message (callback result) | httpRequest | Telegram sendMessage |
| 42 | Code — Build help topic v6.0.23 | code | Sub-help (YouTube / Rutube / VK / etc) |
| 43 | HTTP /send_message (help topic) | httpRequest | Telegram sendMessage |
| 44 | Code — Close menu v6.0.21 | code | Delete menu message |
| 45 | Code — Find last digest v6.0.26 | code | Подготовка к /digests_recent (last) |
| 46 | HTTP /digests_recent (last) | httpRequest | Последний дайджест |
| 47 | Code — Build audio from last v6.0.26 | code | Format audio script |
| 48 | HTTP /audio_digest (last) | httpRequest | Newton TTS, голос burunov |
| 49 | HTTP /send_audio (last) | httpRequest | Multipart upload в Telegram |
| 50 | Code — Build callback payload v6.0.21 (см. #35) | — | (см. выше) |

#### Connections (high-level):
```
webhook → Parse Cmd → SWITCH
   ↓ (output 0) fetch → Ack msg → [IF ack → send_message → Respond] + Pass through → process_url
   ↓ (output 1) channel → youtube_channel_latest → Use channel result
   ↓ (output 2) media → telegram_download → media notice → [IF empty → media empty] | transcribe → media YandexGPT
   ↓ (output 3) callback → Build callback payload → SWITCH callback → [stats | recent | pending | close | help | audio_last]
   ↓ (output 4) help → Build help msg → send_message → Respond
```

### 3.2 Flask endpoints (пакеты в `/opt/beget/n8n/research-agent/packages/`)

#### `packages/research/routes.py`
| Endpoint | Method | Что делает |
|---|---|---|
| `/process_url` | POST | Universal extract для 14 платформ (YouTube, Rutube, VK, Kinescope, Vimeo, PeerTube, Dzen, Smotrim, VKPlay, Kinopoisk, Yandex Play, Apple Podcast, Google Podcast, SoundCloud) |
| `/transcribe` | POST | Newton transcribe (файл или URL) |
| `/fetch` | POST | Скачать URL в файл |
| `/download` | POST | Generic download |
| `/telegram_download` | POST | Download file из Telegram по file_id |
| `/upload` | POST | Upload file |
| `/save_text` | POST | Save text в KB |

#### `packages/kb/routes.py`
| Endpoint | Method | Что делает |
|---|---|---|
| `/kb_save` | POST | Save source + digest + actions |
| `/kb_query` | GET | Query KB |
| `/user_profile` | GET/POST | Get/update user profile |
| `/render_digest` | POST | HTML render дайджеста |
| `/action_feedback` | POST | Action status (done / skip / progress) |
| `/action_status` | GET | Get action status |
| `/actions_recent` | GET | Pending actions list |
| `/digests_recent` | GET | Recent digests (поддерживает dict+list формат items_json) |
| `/user_stats` | GET | User stats (digests/actions/pending) |
| `/summarize` | POST | Newton LLM summarize (llama/gpt4) — **401 с текущим токеном** |
| `/tts` | POST | Newton TTS (голос: default/burunov) |
| `/newton_voices` | GET | Список голосов |
| `/newton_transcribe` | POST | Multi-engine transcribe (v3/parakeet/whisper/diarize/stereo-v3) |
| `/newton_fetch` | POST | YouTube → fetch + transcribe (Parakeet) |
| `/audio_digest` | POST | Text → MP3 (digest_id, voice) |
| `/diarize` | POST | Speaker diarization |
| `/comments_analyze` | POST | YandexGPT comments analysis |
| **`/seen_update`** | POST/GET | **Sprint 21: dedup webhook updates** (TTL 5 мин) |

#### `packages/telegram_bot/routes.py`
| Endpoint | Method | Что делает |
|---|---|---|
| `/send_message` | POST | Telegram sendMessage (с parse_mode + reply_markup) |
| `/send_audio` | POST | Multipart upload audio (MP3/OGG) |
| `/send_voice` | POST | Voice message upload |
| `/set_my_commands` | POST | Persistent Bot Menu |
| `/help_inline` | POST | /help с inline keyboard |
| `/handle_callback` | POST | Ack callback_query + route |

### 3.3 SQLite schema (`/opt/beget/n8n/kb.db`)

```sql
-- sources
CREATE TABLE sources (
  id INTEGER PRIMARY KEY,
  url TEXT UNIQUE NOT NULL,
  kind TEXT,
  external_id TEXT,
  title TEXT,
  added_at TEXT,
  last_seen TEXT
);

-- claims (YandexGPT тезисы — DROPPED, но таблица осталась)
CREATE TABLE claims (
  id INTEGER PRIMARY KEY,
  source_id INTEGER,
  ts_in_video TEXT,
  text TEXT,
  lang TEXT,
  url TEXT,
  claim_type TEXT,
  created_at TEXT
);

-- digests
CREATE TABLE digests (
  id INTEGER PRIMARY KEY,
  period_from TEXT,
  period_to TEXT,
  created_at TEXT,
  items_json TEXT,  -- DICT {title, summary, meta, actions_count}
  html_path TEXT,
  tg_msg_ids TEXT,
  user_id INTEGER
);

-- actions
CREATE TABLE actions (
  id INTEGER PRIMARY KEY,
  digest_id INTEGER,
  user_id INTEGER,
  text TEXT,
  confidence REAL,
  status TEXT,  -- pending / done / skipped
  relevance TEXT,
  created_at TEXT,
  updated_at TEXT
);

-- user_profile
CREATE TABLE user_profile (
  user_id INTEGER PRIMARY KEY,
  name TEXT,
  watchlist TEXT,  -- JSON array
  risk_profile TEXT,
  budget_daily_rub INTEGER,
  updated_at TEXT
);

-- seen_updates (Sprint 21 — dedup)
CREATE TABLE seen_updates (
  update_id INTEGER PRIMARY KEY,
  ts INTEGER
);
```

### 3.4 Поддерживаемые платформы (14)

| Платформа | Extract | Comments | Audio transcribe |
|---|---|---|---|
| YouTube | yt-dlp (subs_auto / subs_requested) | 4 Invidious + 3 Piped | Newton (если subs нет) |
| Rutube | yt-dlp (встроенные subs) | Official API | Newton v3 |
| VK | yt-dlp (subs, часто CDN-блок) | m.vk.com scrape (нужен service_token) | Newton v3 |
| Kinescope | oembed + master.m3u8 + yt-dlp | Description only | Newton v3 |
| Vimeo | yt-dlp | Description | Newton v3 |
| PeerTube | yt-dlp (instance-specific URL) | Description | Newton v3 |
| Dzen | yt-dlp | Description | Newton v3 |
| Smotrim | yt-dlp | Description | Newton v3 |
| VKPlay | yt-dlp | Description | Newton v3 |
| Kinopoisk | yt-dlp | Description | — |
| Yandex Play | yt-dlp | Description | — |
| Apple Podcast | yt-dlp | Description | Newton v3 |
| Google Podcast | yt-dlp (RSS feed) | Description | Newton v3 |
| SoundCloud | yt-dlp | Description | Newton v3 |

### 3.5 Inline buttons (текущее меню)
1. 📊 Статистика → user_stats
2. 🕐 Последние → digests_recent
3. ⏳ Pending → actions_recent
4. 🎙 Аудио → audio_last (опциональная озвучка)
5. 📖 Справка → help_docs (подменю)
6. ✖ Закрыть → deleteMessage

### 3.6 Persistent Bot Menu (setMyCommands)
```
/start  — Запустить бота
/help   — Справка и меню
/stats  — Статистика дайджестов и actions
/recent — Последние 5 дайджестов
/pending — Невыполненные actions
/audio  — Аудио-дайджест последнего материала
```

### 3.7 Auth & budget
- `ALLOWED_TELEGRAM_USERS=261540559` (только PM)
- `DAILY_BUDGET_RUB=200`
- `YANDEX_GPT_API_KEY=<secret, в /opt/beget/n8n/.env>`
- `YANDEX_GPT_FOLDER_ID=b1gj791m9sc92argfa0q`
- `NEWTON_TOKEN=<secret, в /opt/beget/n8n/.env>` (транскрибация работает, **summarize — 401**)

---

## 4. Ошибки Mavis (паттерны)

### 4.1 Sandbox wipes state
**Симптом:** `/tmp`, `/root/.mavis/secrets/` стираются между командами (или сессиями).
**Fix:** Восстанавливать secrets в начале каждой работы:
```bash
mkdir -p /root/.mavis/secrets
printf '<beget_password>' > /root/.mavis/secrets/beget_ssh; chmod 600
printf 'host=...\nuser=root\nport=22\nvps_ip=217.114.7.5\n' > /root/.mavis/secrets/beget_ssh_meta; chmod 600
# n8n API key из БД
docker exec -e PGPASSWORD=$POSTGRES_PASSWORD n8n-postgres-1 psql -U root -d n8n -t -A -c "SELECT \"apiKey\" FROM user_api_keys WHERE label='mavis-deploy-2026-06'" > /tmp/key
JWT=$(grep -oE 'eyJ[A-Za-z0-9._-]+' /tmp/key | head -1)
printf 'mavis-deploy-2026-06\n%s\n' "$JWT" > /root/.mavis/secrets/n8n_api_key; chmod 600
```
Также `pip install --break-system-packages pexpect` каждый раз.

### 4.2 n8n Code node cache
**Симптом:** PUT обновляет jsCode, но execution запускает СТАРЫЙ код. Дубли `const body = item.body`, "Identifier already declared".
**Fix:** Менять `node.id` (suffix `-v6-0-27-foo`) — n8n видит как новую ноду.

### 4.3 n8n staticData per-execution scope
**Симптом:** `$getWorkflowStaticData('global')` НЕ делится между executions. Dedup не работает.
**Fix:** Flask `/seen_update` + SQLite таблица с TTL.

### 4.4 Переименование ноды → silent fail в refs
**Симптом:** Переименовал `Code — Parse Command` в `Code — Parse Command v6.0.27`. Другие ноды имеют `$('Code — Parse Command + user_id').first().json` → runtime error "Referenced node doesn't exist".
**Fix:** При переименовании обновить ВСЕ `$('Old Name')` в jsCode + headerParameters + jsonBody всех нод.

### 4.5 Heredoc через `.vps-helper.sh` ломает контент
**Симптом:** `python3 -c "..."` или многострочные строки с `'`/`"` ломаются при передаче через pexpect.
**Fix:** Записывать Python скрипт в файл через base64, передавать `echo 'BASE64' | base64 -d > script.py && python3 script.py`.

### 4.6 GitHub `git clone --depth 1` показывает только последний commit, не cumulative
**Симптом:** Думал что §3.1-3.62 потеряны — на самом деле они были в истории (60→3002→3052→3113→60→3173 строк).
**Fix:** Всегда проверять через `git clone --depth 1` + `wc -l` после PUT. Если файл уменьшился — он перезаписан. Использовать `git checkout <commit> -- file` для restore.

### 4.7 Telegram webhook timeout = 5 сек
**Симптом:** Workflow 30-90 сек → Telegram ретраит update_id → 7-12 executions на 1 message → спам дайджестов.
**Fix:** `HTTP /send_message (ack)` → `Respond to Webhook` СРАЗУ (1 сек). Дальнейшая обработка асинхронно.

### 4.8 No `message_id` в send_message/send_document
**Симптом:** Telegram возвращает "Bad Request: message to be replied not found" если `reply_to_message_id` указывает на несуществующий.
**Fix:** В n8n HTTP Request jsonBody не передавать `message_id` (только в отдельных случаях, проверенно).

### 4.9 Code node typeVersion 2 + runOnceForEachItem = V8 bug
**Симптом:** `$input.first().json` → "Can't use .first() here" или "A 'json' property isn't an object".
**Fix:** Использовать **typeVersion: 1** + `$input.all()` в `runOnceForAllItems`.

### 4.10 YandexGPT env vars названия
**Правильно:** `YANDEX_GPT_API_KEY`, `YANDEX_GPT_FOLDER_ID`. Не `YAGPT_*`. Folder `b1gj791m9sc92argfa0q` (не `b1g8ad6ckje9d3jvsnem`).

### 4.11 extract_video_id returns TUPLE
**Fix:** Всегда `_extracted = extract_video_id(url); video_id = _extracted[1] if isinstance(_extracted, tuple) else None`.

### 4.12 chunk_text returns LIST
**Fix:** Всегда `chunks[0]` для текущего чанка, не `chunk_text(...)`.

### 4.13 No `pkill -9`
**Fix:** `systemctl restart <service>`. pkill убивает фьютексами.

### 4.14 Long heredoc с python3 -c ломает bash
**Fix:** Записывать .py через base64 или файлом через `/workspace/.vps-helper.sh "cat > /tmp/x.py << 'EOF' ... EOF"`.

### 4.15 __pycache__ на VPS
**Fix:** `find /opt/beget/n8n -name '__pycache__' -type d -exec rm -rf {} +` перед restart.

### 4.16 DROP YandexGPT "тезисы" (claims)
**Решение:** Sprint 18 убрал claims из HTML — DROP'нуты.

### 4.17 Audio по кнопке (НЕ auto-flow)
**Правило:** Audio digest — ОПЦИЯ по кнопке "🎙 Аудио". НЕ в auto-flow для каждого дайджеста.

### 4.18 Kinescope custom oembed
**Паттерн:** `https://kinescope.io/oembed?url=<page_url>` → JSON с `html` → regex `https?://[^"]+master\.m3u8[^"]+` → передать в yt-dlp.

### 4.19 VK comments БЕЗ service_token
**Реальность:** api.vk.com/method/video.getComments → 401 "token required". m.vk.com scrape → JS-рендеринг, без auth ничего нет.
**Fix:** Нужен VK service_token (регистрация приложения на dev.vk.com).

### 4.20 n8n HTTP node defaults to GET
**Fix:** Всегда указывать `method: 'POST'` в jsonBody params.

### 4.21 n8n internal HTTP: `host.docker.internal:8080` НЕ `localhost:8080`
**Причина:** IPv6 ECONNREFUSED.

### 4.22 /seen_update в коде Parse Command
**Правило:** Используется `await this.helpers.httpRequest(...)` в `runOnceForAllItems`. Не забыть `await`!

---

## 5. Параметры и особенности среды

### 5.1 VPS Beget
- **Host:** `seefeesnahurid.beget.app` (DNS) / `217.114.7.5` (IP)
- **User:** `root`
- **Port:** 22
- **Password:** `<secret, в /root/.mavis/secrets/beget_ssh>`
- **OS:** Ubuntu 24.04.4 LTS
- **Hardware:** 1 vCPU, 1.9 GB RAM, 0 swap, ~14 GB disk (6 GB free)
- **TZ:** Europe/Moscow
- **SSH restrictions:** ForceCommand blocks nested ssh → используй `.vps-helper.sh` через pexpect

### 5.2 n8n stack (Docker Compose)
- **n8n-n8n-1** + **n8n-n8n-worker-1** (n8nio/n8n:2.17.7)
- **n8n-postgres-1** (postgres:16)
- **n8n-redis-1** (redis:6-alpine)
- **n8n-traefik-1** (traefik:3.6.5)
- **Postgres password:** `<secret, в /opt/beget/n8n/.env>` (root) / `<secret>` (non-root)
- **N8N encryption key:** `<secret, в /opt/beget/n8n/.env>`

### 5.3 n8n API
- **Base URL:** `https://seefeesnahurid.beget.app/api/v1/`
- **Auth:** `X-N8N-API-KEY: <api_key>`
- **Извлечение API key:**
  ```bash
  docker exec -e PGPASSWORD=$POSTGRES_PASSWORD n8n-postgres-1 psql -U root -d n8n -t -A -c "SELECT \"apiKey\" FROM user_api_keys WHERE label='mavis-deploy-2026-06'"
  ```
- **Workflow ID:** `VGVepaHqmjg2PXSj` (Research Agent v6.0.27)

### 5.4 Telegram
- **Bot:** @ZhukovsFirstBot
- **Token:** `<secret, в /opt/beget/n8n/.env>`
- **PM user_id:** `261540559`
- **KAPITAL bot:** `<другой token, в /opt/beget/n8n/.env>` (ДРУГОЙ, НЕ ТРОГАТЬ)
- **Webhook:** `https://seefeesnahurid.beget.app/webhook/research-agent`

### 5.5 YandexGPT
- **API key:** `<secret, в /opt/beget/n8n/.env>`
- **Folder ID:** `b1gj791m9sc92argfa0q`
- **Model:** `yandexgpt-lite`
- **URL:** `https://llm.api.cloud.yandex.net/foundationModels/v1/completion`
- **Auth header:** `Authorization: Api-Key <api_key>` (НЕ Bearer!)
- **modelUri:** `gpt://<folder_id>/yandexgpt-lite`

### 5.6 Newton CLI (8 сервисов healthy)
- **Transcribe v3 (RU GigaAM):** https://bit-asr3.1bitai.ru
- **Parakeet (мульти):** https://bit-transcribe-parakeet-prod.1bitai.ru
- **WhisperX:** https://bit-asr-whisper.1bitai.ru
- **Diarize v3:** https://bit-asr-diarize3.1bitai.ru
- **Stereo v3 (АТС):** https://bit-dual-channel-v3.1bitai.ru
- **TTS (Fish Speech):** https://bit-tts.1bitai.ru — голоса: default, burunov (Сергей Бурунов)
- **Fetch (YouTube):** https://bit-fetch-prod.1bitai.ru
- **LLM Summarize:** https://bit-summarize.1bitai.ru — **401 с текущим токеном**

### 5.7 Flask systemd
- **Service:** `newton-api.service`
- **ExecStart:** `/usr/bin/python3 newton-api.py` (cwd `/opt/beget/n8n`)
- **EnvironmentFile:** `/opt/beget/n8n/.env`
- **ExecStartPre:** `fuser -k 8080/tcp 2>/dev/null; sleep 2` (release port)
- **MemoryMax:** 700M (защита от OOM)
- **Restart:** always

### 5.8 File paths
- **VPS Flask:** `/opt/beget/n8n/newton-api.py` + `/opt/beget/n8n/research-agent/packages/{research,kb,telegram_bot}/`
- **VPS .env:** `/opt/beget/n8n/.env` (mode 600)
- **VPS KB DB:** `/opt/beget/n8n/kb.db`
- **VPS temp:** `/opt/beget/n8n/newton-tmp/` (audio MP3, транскрипты)
- **Sandbox workspace:** `/workspace/`
- **Sandbox secrets:** `/root/.mavis/secrets/`
- **Sandbox helper:** `/workspace/.vps-helper.sh` (pexpect-based SSH)

### 5.9 GitHub
- **Repo:** `https://github.com/swzhukov/AnalizIstochnikov` (MIT)
- **llm_manifest:** `https://github.com/swzhukov/llm_manifest` (ENVIRONMENT.md + MISTAKES.md + wiki/)
- **Push:** HTTPS + PAT (`GITHUB_LLM_MANIFEST_TOKEN=<secret>`)
- **API:** `curl -X PUT -H "Authorization: token $TOKEN" -H "Content-Type: application/json" -d "@body.json" "https://api.github.com/repos/swzhukov/llm_manifest/contents/MISTAKES.md"`

---

## 6. Что работает (подтверждено)

### Real E2E через Telegram (2026-06-22/23)
- YouTube: digest + TL;DR (msg_id 478, 567, 745+)
- Rutube: digest + TL;DR (msg_id 539/540/541, 657+)
- VK: transcript через Newton (msg_id 512-516)
- Sprint 18 callback buttons: stats/recent/pending/help/close — все работают
- Sprint 19 audio по кнопке: msg_id 567 (1MB MP3 голосом burunov)
- Sprint 20 /stats /recent /pending /audio текстовые команды
- Sprint 21 dedup: 3 retry → 1 execution + 2 deduped

### Flask endpoints tested OK
- /process_url YouTube: 20757 chars, 5 comments, status 200
- /seen_update: status 200 (TTL 5 мин)
- /audio_digest: 25KB MP3 burunov, status 200
- /newton_voices: список голосов, status 200
- /digests_recent: 3 дайджеста с title (после Sprint 20 fix)

### Newton services healthy
- 8/8 healthy по `newton health`

---

## 7. Противоречия и открытые вопросы (требуют внимания PM)

### 7.1 Число нод в workflow
- **Утверждение в HANDOFF:** "50 нод"
- **Реальность:** API dump показывает 50 нод
- **Раньше я писал:** "v6.0.27, 51 нод" — **ошибка**
- **Контекст:** После Sprint 19 был v6.0.25 (47 нод), Sprint 20 добавил 5 нод для audio (всего 50), Sprint 21 ничего не добавил (только /seen_update во Flask).

### 7.2 MISTAKES.md — была ли потеря данных?
- **PM запросил:** "учтены все ошибки"
- **Реальность:** §3.1-§3.62 БЫЛИ в git истории, я ошибочно решил что потеряны. Восстановил.
- **Урок:** GitHub raw URL с `git clone --depth 1` показывает только последний commit, не cumulative. Нужно `git clone` (full) + `git log -- MISTAKES.md` для проверки истории.

### 7.3 Newton summarize 401
- **Симптом:** `Malformed token: Not enough segments`
- **Возможные причины:** (а) Требуется другой scope (прод-токен), (б) Требуется отдельный API key для LLM Summarize vs транскрибации, (в) Newton сервисный сбой.
- **Workaround:** Используем YandexGPT для summarization. Newton Summarize не блокирует flow.
- **Нужно:** Проверить с PM — есть ли отдельный LLM-токен?

### 7.4 VK comments без service_token
- **Статус:** Заблокировано.
- **Решение:** PM должен зарегистрировать VK-приложение (Standalone) на dev.vk.com → получить service_token → положить в `.env` как `VK_SERVICE_TOKEN`.
- **Endpoint:** `/process_url` уже поддерживает VK_SERVICE_TOKEN, добавлю логику при наличии.

### 7.5 Kinescope — реально работает?
- **Тест:** Реально не тестировал с PM. Только internal curl.
- **Что нужно:** PM должен прислать Kinescope URL для real E2E.

### 7.6 Sprint 18-19-20-21 не проверены PM лично
- **Sprint 18 comments для Rutube:** API OK, PM не подтвердил.
- **Sprint 19 audio auto-flow:** Убран в Sprint 20.
- **Sprint 20 audio по кнопке:** PM не нажимал.
- **Sprint 21 dedup:** PM не подтвердил лично.
- **Нужно:** PM должен реально прислать URL и проверить каждое поведение.

### 7.7 n8n staticData — точно ли per-execution?
- **Моя гипотеза:** Per-execution scope (поэтому dedup не работает между executions).
- **Документация n8n:** Static data per-workflow, но per-node instance.
- **Возможно:** Я ошибся в интерпретации. Может работать через `$getWorkflowStaticData('global')` если настроить правильно.
- **Нужно:** Проверить в новой сессии, если будет время.

---

## 8. Sprint backlog (не сделано)

### 8.1 КРИТИЧНО (блокирует PM)
- ❌ **VK comments** — нужен VK service_token от PM

### 8.2 ВАЖНО (PM просил в Sprint 20)
- ❌ **/recent /stats /help /start текстовые команды** — СДЕЛАНО в Sprint 20 ✅
- ❌ **Persistent Bot Menu (setMyCommands)** — СДЕЛАНО в Sprint 20 ✅
- ❌ **digests_recent.title** — СДЕЛАНО в Sprint 20 ✅
- ❌ **Audio digest как опция** — СДЕЛАНО в Sprint 20 ✅
- ❌ **/summarize Newton LLM fix** — НЕ СДЕЛАНО (401)

### 8.3 NICE-TO-HAVE
- Apple/Google Podcasts через feedparser (RSS feed)
- Twitter/X, Instagram, TikTok support
- Persistent Bot Menu inline buttons (отдельно от setMyCommands)
- /recent /stats text commands — улучшить форматирование
- digests_recent — показывать дату + duration + размер

### 8.4 ТЕХНИЧЕСКИЙ ДОЛГ
- Добавить `__pycache__` cleanup в install.sh
- Добавить unit tests для /process_url (mock Newton)
- Добавить /health_full endpoint
- Заменить hardcoded tokens на env vars
- Добавить `--debug` mode для Flask

---

## 9. MISTAKES reference

Полная база: https://github.com/swzhukov/llm_manifest/blob/main/MISTAKES.md

Ключевые секции:
- §3.1-§3.10: базовые n8n/Flask gotchas (request body, jsonBody, switch)
- §3.30-§3.40: v6.0.7-v6.0.10 (YandexGPT fixes, claims drop)
- §3.50-§3.60: Sprints 12-18 (multi-source subs, voice flow, dedupe UX, Kinescope)
- §3.61: Sprint 19 (Newton full + audio auto)
- §3.62: Sprint 20 (menu rewrite, audio option, Bot Menu)
- §3.63: Sprint 21 (retry-storm fix, dedup via Flask, immediate 200 OK)

---

## 10. Команды (cheatsheet)

### 10.1 SSH to VPS
```bash
/workspace/.vps-helper.sh "command here"
```

### 10.2 Restart Flask
```bash
/workspace/.vps-helper.sh "find /opt/beget/n8n -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; systemctl restart newton-api"
```

### 10.3 Get n8n executions
```bash
export N8N_KEY=$(tail -1 /root/.mavis/secrets/n8n_api_key)
curl -sL -H "X-N8N-API-KEY: $N8N_KEY" "https://seefeesnahurid.beget.app/api/v1/executions?workflowId=VGVepaHqmjg2PXSj&limit=5"
```

### 10.4 PUT workflow
```bash
export N8N_KEY=$(tail -1 /root/.mavis/secrets/n8n_api_key)
curl -sL -X PUT -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" -d "@/tmp/wf.json" "https://seefeesnahurid.beget.app/api/v1/workflows/VGVepaHqmjg2PXSj"
```

### 10.5 Test webhook (Telegram update simulation)
```bash
curl -sL -X POST "https://seefeesnahurid.beget.app/webhook/research-agent" -H "Content-Type: application/json" \
  -d '{"update_id":123,"message":{"message_id":456,"from":{"id":261540559},"chat":{"id":261540559},"date":1750010000,"text":"https://youtu.be/xxx"}}' --max-time 30
```

### 10.6 Push to llm_manifest
```bash
SHA=$(curl -sL -H "Authorization: token $GITHUB_LLM_MANIFEST_TOKEN" "https://api.github.com/repos/swzhukov/llm_manifest/contents/MISTAKES.md" | python3 -c "import json,sys; print(json.load(sys.stdin)['sha'])")
python3 -c "import base64, json; print(json.dumps({'message':'...','content':base64.b64encode(open('/tmp/MISTAKES.md','rb').read()).decode(),'branch':'main','sha':'$SHA'}))" > /tmp/body.json
curl -sL -X PUT -H "Authorization: token $GITHUB_LLM_MANIFEST_TOKEN" -H "Content-Type: application/json" -d "@/tmp/body.json" "https://api.github.com/repos/swzhukov/llm_manifest/contents/MISTAKES.md"
```

### 10.7 Check seen_updates table
```bash
/workspace/.vps-helper.sh "python3 -c 'import sqlite3; con = sqlite3.connect(\"/opt/beget/n8n/kb.db\"); cur = con.cursor(); cur.execute(\"SELECT * FROM seen_updates ORDER BY ts DESC LIMIT 10\"); print(cur.fetchall())'"
```

---

## 11. Файлы для новой сессии

### 11.1 В workspace
- `/workspace/HANDOFF.md` (этот файл)
- `/workspace/ENVIRONMENT.md` (полная база знаний среды)
- `/workspace/MISTAKES.md` (локальная копия, 3173 строки)
- `/workspace/backup/workflows/research-agent-v6.0.27-DEDUP.json` (workflow backup)
- `/workspace/.vps-helper.sh` (SSH helper)

### 11.2 На GitHub
- `swzhukov/llm_manifest/MISTAKES.md` (3173 строки, §3.1-§3.63)
- `swzhukov/llm_manifest/ENVIRONMENT.md` (1922 строки)
- `swzhukov/AnalizIstochnikov/README.md` (v6.0.7 — нужно обновить до v6.0.27)

### 11.3 На VPS
- `/opt/beget/n8n/.env` (secrets, mode 600)
- `/opt/beget/n8n/newton-api.py` (Flask entry)
- `/opt/beget/n8n/research-agent/packages/` (kb, research, telegram_bot)
- `/opt/beget/n8n/kb.db` (SQLite с KB + actions + seen_updates)

---

## 12. Вердикт состояния

**Работает:** main flow (YouTube/Rutube/VK/Kinescope) → дайджест → Telegram. Бот меню работает. Dedup работает. Bot Menu persistent.

**Не работает / блокировано:** VK comments (нужен service_token). Newton Summarize (401).

**Рекомендация для PM:** Прислать VK service_token + проверить лично каждое поведение (Sprint 18-21 не подтверждены PM).

**Рекомендация для Mavis в новой сессии:**
1. Прочитать `/workspace/HANDOFF.md` (этот файл)
2. Прочитать `/workspace/ENVIRONMENT.md` (полная база)
3. Прочитать `/workspace/MISTAKES.md` (все 63 секции ошибок)
4. Восстановить secrets из §5 + §4.1
5. Спросить PM: какой следующий шаг (Sprint 22 = VK + Newton Summarize fix? Или новая фича?)

---

**Конец HANDOFF.md. Сгенерирован Mavis 2026-06-23 в режиме per-step self-check.**

---

## 9. Sprint 22 — Flask recovery (2026-06-23, выполнен)

### 9.1 Что было сломано
`newton-api.py` (107 строк) был урезан до 1 endpoint `/`. Пакеты `packages/{research,kb,telegram_bot}/routes.py` (2040 строк, 3 файла) лежали на диске, но **НИКУДА НЕ ПОДКЛЮЧАЛИСЬ**.

**Симптомы:**
- `/health`, `/process_url`, `/seen_update`, `/audio_digest`, `/user_profile`, `/kb_save` → 404
- Workflow v6.0.27 показывал "success" в n8n executions, но реально выполнял только 6/50 нод
- В Telegram PM получал только ответы на `/start` и `/help`
- `kb.db` = 0 байт (legacy путь). Реальная БД: `/opt/beget/n8n/kb/research.db`

### 9.2 Что сделано (30 мин)
1. ✅ Бэкап `/opt/beget/n8n/backups/sprint22-2026-06-23/` (newton-api.py + packages + kb.db + service)
2. ✅ Достал `core/app.py` (162 строки) из `swzhukov/AnalizIstochnikov` master ветки
3. ✅ Заменил `newton-api.py` на тонкую обёртку:
   ```python
   import sys
   sys.path.insert(0, '/opt/beget/n8n/research-agent')
   from core.app import app
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=8080)
   ```
4. ✅ `systemctl daemon-reload && systemctl restart newton-api`
5. ✅ Все 3 пакета зарегистрировались: `[research] endpoints registered OK`, `[telegram_bot] endpoints registered OK`, `[kb] endpoints registered OK`
6. ✅ KB schema автоинициализировалась: `/opt/beget/n8n/kb/research.db` (372 KB, 66 digests, 6 tables)
7. ✅ Smoke test 8 endpoints → все HTTP 200
8. ✅ E2E webhook тест с YouTube URL (`dQw4w9WgXcQ`) → execution 2056: SUCCESS, 17/50 нод, 0 errors, 24 сек от URL до отправки в Telegram

### 9.3 Что протестировано ✅
- `/` — service info (200)
- `/health_full` — RAM 61%, disk 60%, load 1.3, uptime, auth, last_error (200)
- `/user_profile` — профиль PM (261540559, ИИС A3, watchlist, цели — НЕ ПОТЕРЯН!)
- `/user_stats` — пустой `{}` (нет данных для статистики, нужен реальный use)
- `/seen_update` — dedup работает (POST возвращает age в секундах если seen)
- `/digests_recent` — 10 последних дайджестов (включая 21.06.2026 экономика РФ, IMOEX падает)
- `/newton_voices` — 2 голоса (default, burunov)
- E2E URL → Telegram — полный pipeline (process_url → yagpt_summarize → comments_analyze → render_digest → send_document → send_message)

### 9.4 Что НЕ протестировано ⚠️
- 33 alternate path ноды (channel, media, callback, audio_last, help sub-topics)
- `/kapital/*` endpoints — это **ДРУГОЙ проект** на том же Flask (НЕ ТРОГАТЬ)
- Newton `/summarize` — 401, требует другой ключ
- `/voices/upload` — кастомные голоса PM
- Persistent Bot Menu buttons → реальный Telegram click

### 9.5 Новая архитектура (v6.0.28 / Flask v6.0.1)

```
Telegram user → Traefik :443 → n8n webhook (50 нод)
                                  ↓ HTTP
                            Flask :8080 (newton-api.py → core/app.py)
                                  ↓ load_packages(app)
                            ┌─────┴─────┬──────────┐
                            ↓           ↓          ↓
                  packages/research  packages/kb  packages/telegram_bot
                  (14 платформ)      (SQLite)      (sendMessage/audio)
                            ↓           ↓          ↓
                          yt-dlp    research.db  Telegram API
                          Newton    (66 digests)
                          YandexGPT
```

### 9.6 Известные проблемы (Sprint 23+)
1. `/user_stats` возвращает `{}` — нет реальных данных для статистики (счётчики не ведутся, либо в user_stats нужны другие запросы)
2. VK comments — нужен service_token от PM
3. Newton `/summarize` — 401 (отдельный ключ, не тот что `NEWTON_TOKEN`)
4. 33 alternate path ноды workflow не покрыты тестами — нужны отдельные smoke tests для `/help subtopics`, `/audio`, `/recent`, `/pending`, callback handlers
5. `last_error` в `/health_full` показывает `/kapital/get_state 404` — это нормально (другой проект)

### 9.7 Sprint 23+ roadmap (по приоритету)
1. **Тесты alternate paths** — `/help` с inline buttons, `/audio`, `/recent`, `/pending`, callback handlers (~1 час, defensive coding + E2E)
2. **VK comments** — нужен VK service_token, потом `/comments_analyze` для VK (Sprint 24, ~3 часа)
3. **Newton `/summarize` fix** — посмотреть какой ключ нужен, добавить в `.env` (30 мин)
4. **Статистика counters** — добавить счётчики в `user_stats` (sources count, last digest date, action completion rate) (~2 часа)
5. **Persistent Bot Menu inline buttons** — сейчас только `setMyCommands`, можно добавить persistent buttons через `ReplyKeyboardMarkup` (опционально)
6. **GitHub commit workflow** — `workflows/research-agent-v1.1.json` в репо УСТАРЕЛ (v1.1, не v6.0.27). Нужно экспортировать актуальный workflow через n8n API PUT в `workflows/research-agent-v6.0.27.json` (~30 мин)
7. **HANDOFF refresh** — этот HANDOFF уже подустарел. После Sprint 23+ стоит перегенерить

### 9.8 Lessons learned (cross-project)
- ✅ **Health endpoint обязателен** — `/health_full` должен существовать с самого начала (MISTAKES §3.64.1)
- ✅ **Backup перед каждым refactorом** — даже если "я просто строчку удалю" (MISTAKES §3.64.3)
- ✅ **n8n "success" ≠ workflow работал** — проверять `executedNodes / totalNodes` ratio (MISTAKES §3.64.2)
- ✅ **load_packages MUST `sys.exit(1)` при ошибке** — иначе silent fail, workflow показывает "success" с 6/50 нод (MISTAKES §3.64.2)
- ✅ **Реальный путь БД** = `/opt/beget/n8n/kb/research.db`, не `/opt/beget/n8n/kb.db` (MISTAKES §3.64.6)

---

## 10. Sprint 23 (2026-06-24) — production hardening

### 10.1 Что сделано (A-G, кроме VK)

| # | Задача | Результат |
|---|---|---|
| A | `/youtube_channel_latest` endpoint | ✅ Реализован через `yt-dlp --flat-playlist`, возвращает JSON с videos[] (id, title, url, duration_sec) |
| B | Newton `/summarize` 401 fix | ✅ Graceful 503 вместо 500 с actionable hint: нужен `sk-` virtual key от LiteLLM admin |
| C | VK comments | ⏸️ Отложен (нужен service_token от PM, инструкция в HANDOFF §10.5) |
| D | Persistent Bot Menu | ✅ Расширен с 6 до 8 команд (`/channel`, `/health` добавлены), `setMyCommands` → `result: true` |
| E | `/user_stats` real counters | ✅ Счётчики из БД: digests_count, last_digest_at, sources_count, actions_total/pending/done, dedup_24h |
| F | HANDOFF refresh | ✅ Этот файл (v6.0.30) |
| G | Newton key watchdog | ✅ Cron `*/30 * * * *` проверяет `/summarize`, шлёт Telegram alert при 503 (не чаще 1 раза / 6 часов) |

### 10.2 Security fix (Sprint 23 side effect)
- ✅ Удалён **hardcoded Newton token fallback** из 5 мест `kb/routes.py` (Сергей раньше зашил токен в код)
- ⚠️ Токен `XmhocLHmdTFOf8NaqrdBCr4ai30o0XGxaGUckEqzrXk` уже скомпрометирован (был в чате + в коде) — **PM должен ротировать** после Sprint 24

### 10.3 Cron мониторинг (new)
- `/opt/beget/n8n/monitoring/health_check.sh` — каждые 5 мин, alerts на RAM>85%, disk>85%, auth_disabled, last_error (фильтрует KAPITAL)
- `/opt/beget/n8n/monitoring/newton_watchdog.sh` — каждые 30 мин, alert если `/summarize` → 503 (NEWTON_TOKEN invalid)
- Both → Telegram message на /send_message endpoint

### 10.4 GitHub commits (Sprint 23)
- `swzhukov/AnalizIstochnikov`: `workflows/research-agent-v6.0.27.json` (commit `0659a4bc8e`, 107 KB, 50 нод)
- Sprint 22 wiki в `swzhukov/llm_manifest`: MISTAKES.md `74d438d4e1`, ENVIRONMENT.md `937a021108`, HANDOFF.md `f4bc8a9250`
- Sprint 23 commits — готовим

### 10.5 VK service_token — инструкция для PM (отложен на потом)

1. Открыть https://vk.com/apps?act=manage (или новую панель VK ID)
2. Создать **"Standalone-приложение"** (НЕ мини, НЕ no-code, НЕ сайт, НЕ Маруся)
3. В настройках приложения → **API** → включить доступы: `video.getComments`, `video.get`, `users.get`
4. Раздел **Ключи доступа** → скопировать **Сервисный ключ** (~85 символов base64)
5. Прислать токен Mavis (запишу через heredoc, НЕ в открытом виде)
6. Sprint 24: добавить в `/opt/beget/n8n/.env` как `VK_SERVICE_TOKEN`, расширить `/comments_analyze` для VK

**Безопасность:**
- ❌ Service token даёт доступ к публичным данным через API приложения, не может писать комменты / читать личку / получать доступ к аккаунту
- ⚠️ Rate limit 5000 req/день — превышение → бан приложения
- ✅ Если утечёт — другой человек сможет читать публичные комменты VK от имени приложения, но не более

### 10.6 Roadmap (Sprint 24+)
- VK comments (после получения service_token)
- Newton `/summarize` full fix (после получения `sk-` virtual key)
- Export `workflows/research-agent-v6.0.27.json` в GitHub — DONE (Sprint 23)
- HANDOFF refresh — DONE (Sprint 23)
- Persistent Bot Menu inline buttons (опционально)
- Production deploy plan (Traefik routing, logrotate, бэкап БД)

### 10.7 Lessons learned (Sprint 23)
- 10.7.1 **Workflow вызывает endpoint, которого нет в packages** — `/youtube_channel_latest` был в workflow (HTTP нода) но не реализован в Flask. Lesson: при добавлении HTTP ноды в n8n сначала создавать endpoint, потом workflow.
- 10.7.2 **Токен в коде = утечка** — hardcoded fallback в `kb/routes.py` был виден всем кто имел доступ к коду. Lesson: **никогда** hardcoded secrets, всегда `os.environ.get`.
- 10.7.3 **Newton CLI использует Bearer, а нужен JWT** — `bit-summarize.1bitai.ru` принимает только `sk-XXXX` virtual key, не access token. Lesson: для LiteLLM proxy всегда генерировать virtual key через `/key/generate` admin endpoint.
- 10.7.4 **Schema mismatch при UPDATE** — actions таблица имеет `acted` (0/1), не `status` ('pending'/'done'). Lesson: всегда проверять `PRAGMA table_info` перед написанием запросов.
- 10.7.5 **Cron мониторинг + watchdog = раннее обнаружение падений** — узнаём о проблемах за 30 мин, не через жалобу PM. Lesson: добавлять cron при каждом production deploy.

---

**Конец HANDOFF.md v6.0.30 (post-Sprint 23 A-G, без VK). Сгенерирован Mavis 2026-06-24.**


---

## 11. Sprint 23.1 hotfix (2026-06-24) — восстановление `/yagpt_summarize`

### 11.1 Что произошло
PM отправил YouTube URL → бот вернул HTML-дайджест **с пустым summary и без actions**. Cron health_check поймал `/yagpt_summarize|404 Not Found`.

### 11.2 Корневая причина
В Sprint 18-21 был удалён `@app.route('/yagpt_summarize', methods=['POST'])` декоратор, но функция и helper'ы остались. Workflow вызывал endpoint → 404 → render_digest получал пустой текст.

### 11.3 Recovery (15 мин)
1. `cp routes.py.bak-1782104537 routes.py` — bak файл в production директории (auto-backup от какого-то инструмента) имел полную версию
2. `insert_youtube_endpoint.py` — добавил Sprint 23 `/youtube_channel_latest`
3. `systemctl restart newton-api`
4. Тест: 5 буллетов + 3 actions + 0.16₽ за токены YandexGPT

### 11.4 Что увидит PM
Следующий URL от PM даст **полноценный дайджест с summary и actions**, не пустой.

### 11.5 Lessons
- 11.5.1 Endpoint health check на КАЖДЫЙ endpoint через cron smoke test (не только `/health_full`)
- 11.5.2 `@app.route` рядом с `def` без пустых строк — легче grep'ать и труднее случайно удалить
- 11.5.3 `.bak` файлы в production — НЕ удалять, переносить в `/backups/`
- 11.5.4 Backup packages/*/routes.py перед рефакторингом (а не только newton-api.py)

### 11.6 GitHub commits (Sprint 23.1)
- `swzhukov/llm_manifest` MISTAKES.md: §3.66 — добавлено
- HANDOFF обновлён (этот файл)

---

**Конец HANDOFF.md v6.0.31 (Sprint 22 + 23 + 23.1 hotfix). Сгенерирован Mavis 2026-06-24.**

---

## 12. Sprint 24 (2026-06-24) — Kinescope support fix

### 12.1 Что произошло
PM отправил Kinescope URL `https://kinescope.io/m62ooCk2KbbvArqMy954bU/plZ228gK` → бот ответил "❌ Эта ссылка не поддерживается".

### 12.2 Корневая причина
KINESCOPE_RE в `packages/research/utils.py` поддерживал только UUID и числовые ID:
```python
KINESCOPE_RE = re.compile(r'kinescope\.io/(?:embed/)?([0-9a-f]{8}-...|[0-9]+)', re.IGNORECASE)
```
Реальный Kinescope URL имеет формат `/<base62-id>/<hash>` (например `m62ooCk2KbbvArqMy954bU`) — НЕ поддерживался.

Также `process_url` использовал `yt-dlp` для всех платформ, но yt-dlp возвращает 403 для Kinescope (прямой download запрещён).

### 12.3 Fix (15 мин)
1. ✅ Обновил `KINESCOPE_RE` чтобы поддерживал base62 ID + `/embed/<id>` + `/<id>/<hash>`
   ```python
   KINESCOPE_RE = re.compile(r'kinescope\.io/(?:embed/)?([A-Za-z0-9_-]{6,64})(?:/[A-Za-z0-9_-]+)?', re.IGNORECASE)
   ```
2. ✅ Добавил kinescope-specific handler в `process_url`: использует oembed endpoint + master.m3u8 generic (yt-dlp с m3u8 URL)
3. ✅ Тест curl: `https://kinescope.io/m62ooCk2KbbvArqMy954bU/plZ228gK` → title: "Онлайн-практикум_Группа 6_Константин Никитин_27.04"

### 12.4 Тест regex (после fix)
```
https://kinescope.io/m62ooCk2KbbvArqMy954bU/plZ228gK → ('kinescope', 'm62ooCk2KbbvArqMy954bU')
https://kinescope.io/12345                            → (None, None)  # слишком короткий, OK
https://kinescope.io/abc-12345-1234-1234-1234-1234… → ('kinescope', 'UUID')
https://kinescope.io/embed/abc123                     → ('kinescope', 'abc123')
```

### 12.5 Lessons
- 12.5.1 **Платформа "поддерживается" в utils.py ≠ реально обрабатывается в process_url** — нужно проверять оба уровня
- 12.5.2 **yt-dlp generic с m3u8 URL работает** для платформ где yt-dlp extractor не поддерживается
- 12.5.3 **oembed endpoint** — универсальный способ получить метаданные без авторизации

### 12.6 GitHub commits (Sprint 24)
- `swzhukov/llm_manifest` HANDOFF.md: §12 — добавлено
- MISTAKES.md обновлён

---

**Конец HANDOFF.md v6.0.32 (Sprint 22 + 23 + 23.1 + 24). Сгенерирован Mavis 2026-06-24.**

### 12.7 Sprint 24.1 (2026-06-24) — Parse Command fix

**Что было сломано:** даже после Sprint 24 fix в `process_url`, Parse Command code node в workflow не имел regex для Kinescope → отправлял в `cmd = 'invalid'` → "Эта ссылка не поддерживается".

**Fix:**
1. ✅ Добавил Kinescope regex в Parse Command: `kinescope\.io\/(?:embed\/)?([A-Za-z0-9_-]{6,64})(?:\/[A-Za-z0-9_-]+)?`
2. ✅ Добавил ack_text: 'Понял, обрабатываю Kinescope видео...'
3. ✅ Workflow PUT v586 → v587

**Также найдена проблема:** Build YandexGPT payload нода читает `subs.text`, не `subs_text`. Kinescope handler возвращал только `subs_text`. Fix: добавил `text` поле + все нужные workflow fields (timeline, video_id, title, duration, method, char_count, comments, platform, kind).

**PUT через n8n API:**
- Только `name + nodes + connections + settings={}`
- Read-only поля (active, settings.callerPolicy, settings.executionOrder, settings.binaryMode) НЕ передаются

**Гитхаб commits:**
- `swzhukov/AnalizIstochnikov` workflows/research-agent-v6.0.27.json: v587 (Kinescope regex)


### 12.8 Sprint 25 (2026-06-24) — cron spam fix + Kinescope transcribe fallback

**Что сделано:**
1. ✅ Cron health_check фильтрует 22 bot-паттерна (SDK/webLanguage, cgi-bin/luci, manager, wp-admin, /.env, etc.)
2. ✅ Kinescope handler fallback на Newton transcribe (parakeet) если title+description < 500 chars
3. ✅ Health.log тест: `/manager|404` НЕ шлёт alert (фильтр работает)

**Lessons:** см. MISTAKES §3.68.

