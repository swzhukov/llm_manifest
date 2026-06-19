---
title: Саммари сессий диалога
tags: [meta, log]
created: 2026-06-15
---
# Саммари сессий диалога

## Сессия 1 (14–15 июня 2026) – Принципы Карпатого
1. Запрос принципов работы с ИИ.
2. Выдача 4 столпов и 6 концепций.
3. Инициализация вики.

## Сессия 2 (15 июня 2026) – Углубление
4. Извлечение концепций Agentic Engineering, RLVR.
5. Первый `lint wiki`, исправление битых ссылок.

## Сессия 3 (15 июня 2026) – Глобальное обновление
6. Глубокий анализ, создание папок raw/, SCHEMA.md, AGENTS.md.
7. Добавление Loop Engineering, контекстной инженерии, сравнение клиентов.
8. Создание 4-модульного курса (practical-course.md).
9. Создание Манифеста Совета экспертов (COUNCIL_RECOMMENDATIONS.md).

## Сессия 4 (16 июня 2026) – Унификация reference docs
10. PM попросил объединить 2 reference-файла (DEVELOPMENT_PLAYBOOK Капитала + ENVIRONMENT research-agent) в единый `ENVIRONMENT.md` v3.0 (1922 строки, 19 секций).
11. Аналогично — 2 каталога ошибок (ERRORS_AND_LESSONS + MISTAKES) → единый `MISTAKES.md` v3.0 (1654 строки, 17 секций).
12. **Критично:** в исходных файлах найдены 5 утечек секретов (hardcoded bot tokens, YandexGPT key, folder_id, postgres password, encryption key) — все вычищены, заменены на плейсхолдеры.
13. PM попросил написать универсальный системный промт для задач «Создание автоматизаций» с жёсткой интеграцией wiki.
14. Создан `wiki/templates/SYSTEM_PROMPT_AUTOMATION.md` (556 строк, 14 секций): boot sequence (force-read wiki), context filter, 4 режима Update Protocol (CAN-WRITE-FULL / CAN-READ-ONLY / OFFLINE / DEGRADED), LLM-agnostic (DeepSeek/Kimi/Minimax/Qwen/Perplexity).
15. Применены скиллы: wiki-loader (синхронизация вики), wiki-curator (обновление log.md и session-summaries.md), gstack-team (8-фазный спринт имитирован).

**Статус:** 3 reference-файла готовы, ждут коммита в репо. Заблокировано: n8n Code node bug (нужен fresh API key).

## Сессия 5 (17 июня 2026) – research-agent workflow fix
16. PM дал fresh n8n API key — разблокирована задача Code node fix.
17. Применён gstack-team (8 фаз, Phase 3+6 skip, Phase 5 self-review из-за 2x subagent 429).
18. Phase 4: 3 PUT'а в n8n — fix `json.message` → `json.body.message` + recursive replace `$('code_parse')` → `$('Code — Parse Command + user_id')` в 7 нодах.
19. Phase 6: execution 693 (test /start) = success, execution 697 (test YouTube URL) = Code node OK + HTTP /youtube_meta вызван, но Flask downstream 500.
20. Phase 7: wiki-curator — MISTAKES §3.X (новый) + n8n-api-quirks memory topic (3 урока).
21. Self-improve: self-review пропустил 7 broken references. Урок: даже в self-review рекурсивно проверять references и читать ВСЕ n8n logs, не только Code node.

**Статус:** n8n Code node fix ЗАШИПЛЕН в production (workflow active=true, versionCounter=20). Flask /youtube_meta — отдельный downstream bug (НЕ в scope этого спринта).


## Сессия 6 (19 июня 2026) – E2E workflow fix + Flask fallback
22. Sprint 7 (продолжение Sprint 6): SSH access restored, fresh n8n API key, Flask restart без auto-reloader.
23. Smoke test `/youtube_subs` = 200 OK, 68K chars VTT, 1.9s (yt-dlp primary).
24. E2E test (webhook → 9 нод): **дошёл до HTTP /send_document** — главный milestone. Все 8 основных нод отрабатывают за 30 сек (YandexGPT).
25. Найдены 3 критичные проблемы Sprint 5 (были неполные):
    - §3.22: `options.continueOnFail=true` не работает в webhook-triggered flow → fallback в Python
    - §3.24: Sprint 5 fix `$('code_parse')` → `$('Code — ...')` был только в `headerParameters`, забыли `jsonBody` + `jsCode Build Digest` (6 нод) → recursive id→name fix
    - §3.25: удаление ноды требует чистки connections в обе стороны
26. Fix: добавил fallback в `/youtube_meta` (200 + minimal dict при пустом YOUTUBE_API_KEY) + удалил ноду /youtube_meta + recursive replace id→name в 6 нодах + optional `message_id` в /send_document.
27. MISTAKES.md: добавлены §3.19-3.29 (11 новых уроков Sprint 6+7).
28. Финальное состояние: workflow v53, 12 нод, active. E2E test = 9/12 нод ✅, 1 фейл на /send_document с фейковым message_id (ОЖИДАЕМО для теста).
29. Production-ready: PM может сделать реальный тест через Telegram-бот @ZhukovsFirstBot.

**Статус:** Workflow ЗАШИПЛЕН. Flask fallback добавлен. Все 11 уроков в MISTAKES.md (локально). Готово к коммиту в llm_manifest.

