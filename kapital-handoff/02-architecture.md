# Шаг 2. Концепция и архитектура

## Было заявлено (Phase 1-7)

Полная архитектура в `/workspace/architecture/arch_v2.md`:
- **n8n + Sheets (Google) → миграция в FastAPI+PostgreSQL в Phase C**
- **6 workflows** вместо 11
- **MOEX API** для цен
- **YandexGPT** для AI
- **Яндекс.Таблицы вместо Google** (для 152-ФЗ compliance)

## Что РЕАЛЬНО построено (отличается от плана)

### Архитектура as-built

```
┌─────────────────────────────────────────────────────────┐
│  КЛИЕНТЫ                                                │
│  ┌──────────────────┐   ┌──────────────────────────┐   │
│  │ Telegram Bot     │   │ Web App (Vite+React+TS)  │   │
│  │ @KapitalInvestBot│   │ ejgxa2qa9mpl.space.io   │   │
│  └──────────────────┘   └──────────────────────────┘   │
└─────────────┬────────────────────────┬─────────────────┘
              │                        │
              ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│  VPS Beget (seefeesnahurid.beget.app)                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ n8n 2.17.7 (Docker) — webhook-based             │   │
│  │ WF_K2_K3_combined (127 нод, 93 connections)    │   │
│  │ url: webhook/03727273-87bd-4d80-b4fe-4f413a3618ee│   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼──────────────────────────┐   │
│  │ newton-api.py (Flask) │ systemd: newton-api      │   │
│  │ port 8080            │                           │   │
│  │ Конечные точки:                                │   │
│  │   /kapital/dashboard  /kapital/settings_v2      │   │
│  │   /kapital/ask_sprint3 /kapital/help            │   │
│  │   /kapital/fraud_help  /kapital/setup_help      │   │
│  │   /kapital/reset_help  /kapital/digest_help     │   │
│  │   /kapital/today      /kapital/plan             │   │
│  │   /kapital/goal       /kapital/iis3             │   │
│  │   /kapital/share      /kapital/done             │   │
│  │   /kapital/start      /kapital/ask              │   │
│  │   /kapital/fraud      /kapital/help_text        │   │
│  │   /kapital/settings_menu /kapital/event_log     │   │
│  │   /kapital/streak_update /kapital/...           │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Polling daemon (systemd: kapital-poll)         │   │
│  │ scripts/poll_daemon_v3.py                        │   │
│  │ ⚠️ 409 Conflict (webhook active) — не работает │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Reminder daemon (systemd: kapital-remind)      │   │
│  │ scripts/reminder_daemon.py                      │   │
│  │ ✅ active, payday reminders каждые 6ч           │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ PostgreSQL (Docker)                             │   │
│  │ Workflow data, executions, executions_data      │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Redis (Docker)                                  │   │
│  │ n8n queue                                       │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ YandexGPT (external API)                        │   │
│  │ model: yandexgpt-lite, folder b1gj791m9sc92argfa0q│   │
│  │ IAM token caching 12h                           │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ State storage                                   │   │
│  │ /opt/beget/kapital/data/state.json              │   │
│  │ (JSON, multi-user, не Postgres)                 │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Отличия от плана

| План | Реальность |
|---|---|
| Яндекс.Таблицы как DB | ❌ state.json как плоский JSON |
| 6 workflows | ❌ 4-5 workflows, 1 главный (WF_K2_K3_combined) разросся до 127 нод |
| 200 users scale | ❌ 1 user (PM) |
| Phase C миграция в FastAPI+PostgreSQL | ❌ Flask (newton-api) для endpoint'ов, Postgres только для n8n data |
| MOEX API для цен | ❌ Нет реальных цен, mock data в app |
| YandexGPT интеграция | ✅ Реальная (с лимитом 4000 tok/день) |
| Web-приложение | ✅ Vite/React/TS deployed (Sprint 4) |
| Google Sheets | ❌ Нет (был план, но не реализован) |

## Концепция "что продукт ДОЛЖЕН делать" (после диалога)

Из обсуждения в чате, **PM сказал**:
- 1 экран — 1 главное число
- 3 действия в месяц максимум
- Никаких простыней в Telegram (>400 chars)
- Кнопки должны работать

**Концепция v1:**
1. **Web app** — основной интерфейс (✅ deployed)
2. **Telegram bot** — quick commands (✅ 19/19)
3. **Reminder daemon** — payday notifications (✅ systemd)
4. **AI-ассистент** — /ask с YandexGPT (✅ 4000 tok/день)
5. **/fraud** — защита от скама (✅ fallback help, реальный анализ в chain)

## Параметры инфраструктуры

| Параметр | Значение |
|---|---|
| VPS hostname | `seefeesnahurid.beget.app` |
| SSH user | `root` |
| SSH password | в `/workspace/.ssh_beget_pass` |
| n8n container | `n8n-n8n-1`, port 5678 |
| Postgres container | `n8n-postgres-1`, port 5432 |
| Redis container | `n8n-redis-1` |
| Flask | `newton-api.py`, port 8080 |
| Workspace | `/opt/beget/kapital` |
| State file | `/opt/beget/kapital/data/state.json` |
| Web app | https://ejgxa2qa9mpl.space.minimax.io |
| Telegram bot | @KapitalInvestBot |

## Узкие места архитектуры (выявлено за Sprint 4)

1. **n8n workflow разросся до 127 нод** — невозможно поддерживать одному человеку
2. **Нет автотестов** — всё ручное через webhook → execution data → парсинг
3. **Classify как god-object** — все команды в одном Code node, любое изменение ломает chain
4. **Polling daemon сломан** — 409 Conflict с webhook, не работает но systemd active
5. **State в JSON** — не масштабируется, нет миграций, нет конкурентного доступа
6. **Нет логирования в Flask** — logfile 758 bytes, ничего не пишется при ошибках

## Рекомендация на следующий диалог

**КРИТИЧНО**: не делать n8n workflow больше. Все новые фичи добавлять как:
1. Новые HTTP endpoint'ы в Flask (просто, можно тестировать)
2. Code node в n8n вызывает endpoint (без новых IF-каскадов)
3. Classify триммить до минимума (только /start /help /settings + free text → /ask)
