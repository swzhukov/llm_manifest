# Шаг 5. Параметры и особенности среды

## Sandbox (где я работаю)

| Параметр | Значение |
|---|---|
| OS | Linux (debian bookworm) |
| Node.js | v22.17.0 |
| npm | 10.9.2 |
| Python | 3.11 |
| Workspace | `/workspace` |
| Locale | en (но user — ru-RU) |
| Date | зависит от треда (sandbox wipe между сессиями) |

### Sandbox wipe между сессиями
- ❌ `/root/.mavis/secrets/` стирается
- ❌ Env vars стираются
- ❌ apt packages стираются (sshpass, flask)
- ✅ `/workspace/*` сохраняется (включая `.ssh_beget_pass`)

**Что нужно делать в начале каждой сессии:**
```bash
apt-get update && apt-get install -y sshpass
pip install --break-system-packages <missing-packages>
# Helper /workspace/.vps-helper.sh автоматически source'ит /workspace/.ssh_beget_pass
```

## VPS Beget (где живёт бот)

| Параметр | Значение |
|---|---|
| Hostname | `seefeesnahurid.beget.app` |
| SSH user | `root` |
| SSH password | `/workspace/.ssh_beget_pass` (export BEGET_SSH_PASSWORD='...') |
| OS | Linux (debian, ядро стандартное) |
| IP | 217.114.7.5 |
| Hosting | Beget VPS |
| IP forwarding | Через cloudflared + traefik |

### Стек на VPS

**Docker контейнеры:**
- `n8n-n8n-1` (порт 5678) — n8n 2.17.7
- `n8n-n8n-worker-1` (порт 5679) — n8n task runner
- `n8n-postgres-1` (порт 5432) — postgres:16
- `n8n-redis-1` (порт 6379) — redis:6-alpine
- `n8n-traefik-1` (порты 80, 443) — reverse proxy

**Systemd services:**
- `kapital-poll.service` — polling daemon (СЛОМАН, 409 Conflict)
- `kapital-remind.service` — reminder daemon (active)
- `newton-api.service` — Flask app (на самом деле запускается через `nohup`, не через systemd)

**Файловая структура:**
```
/opt/beget/
├── kapital/
│   ├── data/                # state.json, логи, health
│   ├── deploy/              # add_*.py endpoints
│   ├── docker/              # docker-compose
│   ├── scripts/             # daemons
│   ├── src/                 # Python пакеты (kapital, dashboard)
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── README.md
└── n8n/
    ├── newton-api.py         # Flask app, port 8080
    └── ...
```

### Secrets на VPS

```bash
/root/.env   # KAPITAL_YANDEX_GPT_API_KEY=<YANDEX_GPT_API_KEY>
             # KAPITAL_YANDEX_GPT_FOLDER_ID=b1gj791m9sc92argfa0q
```

## Telegram

| Параметр | Значение |
|---|---|
| Bot username | @KapitalInvestBot |
| Bot token | `<TELEGRAM_BOT_TOKEN>` (HARDCODED в n8n, нужно в env) |
| Webhook URL | `https://seefeesnahurid.beget.app/webhook/03727273-87bd-4d80-b4fe-4f413a3618ee/webhook` |
| User (PM) | chat_id 261540559, username @sergzh7 |
| Bot ID | 8954745093 |

⚠️ **Все эти credentials в plain text в n8n workflow JSON. Нужно вынести в env vars.**

## YandexGPT

| Параметр | Значение |
|---|---|
| API Key | `<YANDEX_GPT_API_KEY>` |
| Folder ID | `b1gj791m9sc92argfa0q` |
| Model | `yandexgpt-lite` |
| IAM token TTL | 12h |
| Daily cap per user | 4000 токенов |
| Cap reset | midnight |

## Web App (Vite+React)

| Параметр | Значение |
|---|---|
| URL | https://ejgxa2qa9mpl.space.minimax.io |
| Hosting | minimax.io Spaces (CDN) |
| Build size | 245KB (65KB gzip) |
| Framework | Vite 8.0.16 + React 18 + TypeScript + Tailwind 3.4.17 |
| State | localStorage (нет бэкенда) |
| API calls | ЦБ РФ (https://www.cbr-xml-daily.ru/daily_json.js) — USD/RUB, CNY/RUB |
| Theme | Dark (#0a0a0a) |

## GitHub

| Параметр | Значение |
|---|---|
| User | swzhukov |
| Repo (wiki) | swzhukov/llm_manifest |
| Token | `GITHUB_LLM_MANIFEST_TOKEN` (PAT, scope=repo) |
| Используется для | wiki-curator: MISTAKES.md, ENVIRONMENT.md, sprint-logs |
| URL raw | https://raw.githubusercontent.com/swzhukov/llm_manifest/main/ |

⚠️ **Сейчас НЕ используется активно. Sprint 3 локальные артефакты в /workspace, не в GitHub.**

## Memory topics (Mavis system)

| Topic | Размер | Назначение |
|---|---|---|
| `bash-pitfalls` | 30KB | Конкретные грабли bash |
| `beget-vps-access` | 3KB | SSH access, пароли |
| `llm-manifest-state` | 4KB | Runtime state wiki |
| `n8n-api-quirks` | 17KB | n8n 2.17.7 REST API грабли |
| `n8n-endpoint-defensive-coding` | 5KB | Defensive coding for Flask endpoints |
| `n8n-wiki-local` | 4KB | Локальная wiki n8n |
| `n8n-workflow-cli-deploy` | 3KB | CLI deploy когда API key expired |
| `self-improve-on-errors` | 8KB | Standing instruction |
| `telegram-bot-menu` | 2KB | Persistent Bot Menu |
| `skills-manifest` | 5KB | Persistent manifest |

## Особенности

### n8n quirks (важные)

1. **N8N API key unauthorized** → используй `docker exec n8n-n8n-1 n8n export:workflow` (см. `n8n-workflow-cli-deploy`)
2. **`publish:workflow` не применяет без restart** → `docker restart n8n-n8n-1`
3. **HTTP defaults to GET** → всегда `method: 'POST'` в n8n
4. **Internal HTTP uses `host.docker.internal:8080`** (НЕ `localhost:8080` — IPv6 ECONNREFUSED)
5. **Code node для JS** — inline `{{ }}` не eval
6. **PUT workflow silently accepts connections to non-existent nodes** — validate после PUT
7. **IF-каскад: text routes в main chain**, не side-branches
8. **`$(NodeName)`** fails "Node hasn't been executed" if accessed from different path

### Telegram API quirks

1. **`reply_to_message_id` опциональный** — null OK, но для forwarded messages ставит 400
2. **Bot API URL**: `https://api.telegram.org/bot<token>/<method>`
3. **Webhook конфликтует с getUpdates** — 409 Conflict если оба активны
4. **Bot Menu через setMyCommands** — persistent кнопка "Меню" внизу чата

### Flask quirks

1. **n8n вызывает Flask** через `host.docker.internal:8080`
2. **`parse_mode: Markdown`** — `*` для bold, `_` для italic, ``` для code
3. **`disable_web_page_preview: true`** — для ссылок
4. **defensive coding** в каждом endpoint: `user_id = str(data.get('user_id', '...')).strip()`

## Препятствия к запуску (что я терял время на)

1. **Sandbox wipe → sshpass пропадает** (5+ минут на каждом треде)
2. **VPS пароль в `/root/.mavis/secrets/` → wiped** (но `/workspace/.ssh_beget_pass` сохраняется)
3. **N8N API key expired** → используй CLI export/import
4. **Polling daemon 409** → не чинить, оставить как есть (webhook работает)
5. **Classify модификации** — каждое изменение ломает chain в непредсказуемых местах
6. **YandexGPT лимит** — тестами легко исчерпать, recovery = midnight

## Что НЕ работает (стабильно)

| Что | Влияние | Workaround |
|---|---|---|
| `/reset` в Telegram | Не сбрасывает настройки | Кнопка "Сбросить" в /settings |
| Polling daemon | Не работает (409) | Webhook работает |
| YandexGPT лимит | 4000 tok/день на user | Подождать до полуночи |
| Real broker data | Mock в app | Manual import |
| Real Я.Таблица | State.json | Не реализовано |
| Auto-deploy | Ручной deploy | Скрипт есть |
| Monitoring | Нет | Daemon health files есть, но не отдаются вовне |
