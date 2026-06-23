# Шаг 3. Состав текущего релиза

**Версия**: Sprint 4 — 22.06.2026
**E2E статус**: 19/19 команд OK (audit_results.json)

## Telegram Bot (19/19 OK)

| Команда | Route | Текст | Кнопки | Назначение |
|---|---|---|---|---|
| `/start` | start | 133 chars | 9/6 rows | Главное меню (профиль) |
| `/today` | today | 331 chars | 7/3 rows | Короткий дашборд (2 виджета) |
| `/dashboard` | today | 331 chars | 7/3 rows | Alias для /today |
| `/plan` | plan | 495 chars | 2/1 row | План распределения на месяц |
| `/goal` | goal | 146 chars | 2/1 row | Прогресс к цели |
| `/iis3` | iis3 | 446 chars | 2/2 rows | ИИС-3 статус + расчёт вычета |
| `/share` | share | 174 chars | 1/1 row | Карточка streak |
| `/fraud` | fraud | 35 chars | — | "Слишком короткий текст" (fallback) |
| `/fraud <text>` | fraud | TBD | TBD | Проверка сообщения (chain работает) |
| `/help` | help | 449 chars | 2/1 row | Список 10 команд |
| `/settings` | settings | 210 chars | 7/7 rows | Settings v2 wizard |
| `/done` | done | 76-106 chars | 2/2 rows | Засчитать payday |
| `/ask <вопрос>` | ask | varies | 3/2 rows | YandexGPT (4000 tok/день cap) |
| `/ask` (без вопроса) | ask | ~142 chars | 3/2 rows | "Расскажите, какие вопросы" |
| Free text | ask | varies | 3/2 rows | → /ask fallback |
| `/setup` | setup | 79 chars | 1/1 row | Fallback: "устарела, /settings" |
| `/reset` | reset | 126 chars | 1/1 row | Fallback: "сломан, /settings" |
| `/digest` | digest | 89 chars | 1/1 row | Fallback: "устарела, /today" |
| `/schedule` | schedule | 239 chars | 4/3 rows | Расписание payday |

**Источник**: `/workspace/audit_results.json` (полные логи)

## Web App

**URL**: https://ejgxa2qa9mpl.space.minimax.io

### Структура
- Vite + React 18 + TypeScript + Tailwind CSS
- Mobile-first (на десктопе — фрейм телефона 414px)
- Dark theme (#0a0a0a bg, #1a1a1a cards, #10b981 accent)
- localStorage для настроек (нет бэкенда)
- Mock data (реальные позиции PM из Альфы: SBER, GAZP, LKOH, YDEX, OZON, TMOS, TBRU)

### Экраны
1. **Hero** — портфель 175К₽ / цель 1М₽ / 17.5% прогресс
2. **ActionCard** — "Внеси 400К на ИИС-3 до 31.12" (динамический)
3. **Forecast** — прогноз к цели при 20К/мес + 12% годовых
4. **Positions** — 7 позиций, отсортированы по %
5. **RecentTx** — лента сделок (8 последних)
6. **Markets** — курсы ЦБ РФ (USD/RUB, CNY/RUB, ключевая ставка)
7. **SettingsModal** — wizard для всех 5 настроек

### Файлы
- `/workspace/kapital-app/src/`
  - `App.tsx` — main composition
  - `types.ts` — TypeScript типы (Position, Transaction, Settings, Portfolio)
  - `data/mock.ts` — mock данные Альфа-портфель
  - `lib/finance.ts` — XIRR, прогноз, форматирование
  - `store.ts` — localStorage hooks
  - `components/` — 9 компонентов

## Backend (Flask, 18 endpoints)

`/opt/beget/kapital/deploy/add_kapital_endpoints.py`

### Основные endpoint'ы
- `GET/POST /kapital/dashboard?user_id=X&layout=Y` — Sprint 3 dashboard (200 OK)
- `GET/POST /kapital/dashboard/text` — Telegram-ready text (331 chars)
- `POST /kapital/dashboard/set_layout` — сохранить layout
- `GET /kapital/dashboard/layouts` — список 6 layouts
- `GET/POST /kapital/settings_v2` — wizard endpoint
- `POST /kapital/settings_v2/detail` — детали одной настройки
- `POST /kapital/settings_v2/set` — apply value
- `POST /kapital/ask_sprint3` — YandexGPT (renamed from /kapital/ask)
- `GET /kapital/ask_sprint3/health` — health check
- `GET/POST /kapital/help` — список команд
- `GET/POST /kapital/fraud_help` — инструкция /fraud
- `GET/POST /kapital/setup_help` — fallback /setup
- `GET/POST /kapital/digest_help` — fallback /digest
- `GET/POST /kapital/reset_help` — fallback /reset
- `GET/POST /kapital/settings_menu` — меню настроек (v1 fallback)
- `POST /kapital/today` — daily snapshot
- `POST /kapital/plan` — месячный план
- `POST /kapital/goal` — прогресс к цели
- `POST /kapital/iis3` — ИИС-3 расчёт
- `POST /kapital/share` — share card
- `POST /kapital/done` — отметить payday
- `POST /kapital/ask` — старый /ask (Sprint 1 mock)
- `POST /kapital/fraud` — анализ сообщения
- `POST /kapital/start` — приветствие
- `POST /kapital/event_log` — лог событий
- `POST /kapital/streak_update` — обновить streak

## n8n Workflow

**ID**: `0vbPVWktPYDlqg05`
**Name**: `WF_K2_K3_combined`
**Nodes**: 127
**Connections**: 93
**Webhook**: `https://seefeesnahurid.beget.app/webhook/03727273-87bd-4d80-b4fe-4f413a3618ee/webhook`

### Ключевые ноды
- Telegram Trigger (webhook)
- Classify (Code, ~150 строк JS) — маршрутизация
- 20+ IF нод для каждой команды
- HTTP request ноды (~50) — вызовы Flask endpoint'ов
- fmt ноды (~30) — формирование ответа
- reply ноды (~30) — отправка в Telegram через bot API
- 5 IF нод для fallback chain (help/setup/test/fraud/digest)

### Файлы
- `/workspace/wf_final_state.json` — текущий snapshot
- `/workspace/workflows/wf_v15.7_digest_in_chain.json` — последний залитый

## Daemons

### kapital-poll (polling daemon)
- Файл: `/opt/beget/kapital/scripts/poll_daemon_v3.py`
- Systemd: active (но 409 Conflict)
- **Не работает** из-за webhook
- Файл лога: 1.4M (в основном 409 errors)

### kapital-remind (reminder daemon)
- Файл: `/opt/beget/kapital/scripts/reminder_daemon.py`
- Systemd: active
- Pure logic: `/opt/beget/kapital/src/kapital/b_reminders.py`
- Health: `/opt/beget/kapital/data/remind_health.json` (обновляется)
- Цикл: каждые 6 часов
- Idempotent через `reminder_log.json`

## Что НЕ работает (явные проблемы)

| Что | Статус | Влияние |
|---|---|---|
| Polling daemon | Сломан (409) | Команды от polling не идут, но webhook работает |
| /reset | Fallback | Не сбрасывает настройки, но есть кнопка в /settings |
| YandexGPT лимит | Сбрасывается в полночь | 4000 tok/день, тестами дёргали |
| Real broker data | Mock в app | Нет интеграции с Альфой |
| Real Yandex Tables | State.json | Не используется |
| Settings v2 → реальное сохранение | Callback есть но не проверено | Возможно работает, но не тестировал |
| Auto-deploy | Ручной deploy | Скрипт есть, но не используется |
| Backup/restore | Нет | State.json только |
| Мониторинг | Нет | Health check daemon не отдает вовне |
| Логирование Flask | 758 bytes | Не логирует access |

## Файлы в /workspace

| Файл/папка | Описание |
|---|---|
| `/workspace/audit_bot.py` | E2E audit скрипт (19 команд через webhook) |
| `/workspace/audit_results.json` | Результаты audit'а |
| `/workspace/kapital-app/` | Vite/React/TS web app |
| `/workspace/wf_final_state.json` | Текущий n8n workflow |
| `/workspace/workflows/wf_v15.7_*.json` | История версий workflow |
| `/workspace/sprint-status/SPRINT*.md` | 12 sprint отчётов |
| `/workspace/playbook/DEVELOPMENT_PLAYBOOK.md` | Процесс разработки |
| `/workspace/playbook/ERRORS_AND_LESSONS.md` | Каталог ошибок |
| `/workspace/architecture/arch_v2.md` | Полная архитектура v2 |
| `/workspace/architecture/arch_v1.md` | Архитектура v1 |
| `/workspace/.ssh_beget_pass` | SSH пароль (sandbox-safe location) |
| `/workspace/.vps-helper.sh` | Helper для SSH/SCP |
