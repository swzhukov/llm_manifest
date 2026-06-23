# Kapital — Handoff для нового диалога

**Дата создания:** 23.06.2026
**Состояние продукта:** Sprint 4, 19/19 E2E OK, web app deployed
**PM:** Сергей Жуков (@sergzh7, chat_id 261540559, Тверь)

## ⚠️ ЧИТАЙ СНАЧАЛА: входной промт

Файл `00-INPUT-PROMPT.md` — это **готовый промт** для нового диалога. Скопируй его содержимое в новый чат с Mavis.

## Что внутри

| Файл | Описание |
|---|---|
| `00-INPUT-PROMPT.md` | Готовый входной промт для нового диалога |
| `01-goals.md` | Цели создания продукта + эволюция + противоречия |
| `02-architecture.md` | Реальная архитектура (as-built, не план) |
| `03-current-release.md` | Что работает сейчас (Sprint 4) |
| `04-errors.md` | 12 ошибок разговора + правила предотвращения |
| `05-environment.md` | Параметры среды: sandbox, VPS, secrets, особенности |
| `06-contradictions.md` | 6 противоречий + 8 open questions от PM |

## Что НЕ внутри (но нужно в новом диалоге)

- ❌ Полный исходный код web app — `/workspace/kapital-app/`
- ❌ Полный workflow v15.7 — `/workspace/workflows/wf_v15.7_*.json`
- ❌ Deploy пакет — `/workspace/deploy_package/`
- ❌ Playbook — `/workspace/playbook/DEVELOPMENT_PLAYBOOK.md`
- ❌ Полная архитектура v2 — `/workspace/architecture/arch_v2.md`
- ❌ Audit скрипт — `/workspace/audit_bot.py`
- ❌ Audit results — `/workspace/audit_results.json`

## Что сделать с PM

Прежде чем продолжать разработку, **задай эти вопросы** (из `06-contradictions.md`):

1. "Ты сказал 'Я.Таблицу' и 'доделай бота' — что приоритетнее?"
2. "/settings v2 wizard ОК, /setup больше не нужен?"
3. "Что для тебя 'капитал' — инструмент накопления, игра, или психологическая поддержка?"
4. "Где ты смотришь данные портфеля — Альфа, Я.Таблица, бот, web app?"
5. "Что тебе НУЖНО от бота, чтобы ты его НЕ удалил?"

## Где лежит на GitHub

https://github.com/swzhukov/llm_manifest/tree/main/kapital-handoff

(если ещё не запушил — секция "Push to GitHub" ниже)
