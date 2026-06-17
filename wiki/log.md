---
title: Журнал изменений вики
tags: [meta, changelog]
created: 2026-06-15
---
# Журнал изменений вики

## 2026-06-15 (инициализация)
- Созданы: README.md, glossary.md, topics/markdown-knowledge-base.md, session-summaries.md, pending.md.

## 2026-06-15 (после первого lint)
- Исправлена битая ссылка в README.md.
- Созданы index.md, log.md.

## 2026-06-15 (глобальное обновление)
- Добавлены: SCHEMA.md, AGENTS.md, raw/sources.md.
- Добавлены topics: context-engineering.md, loop-engineering.md, from-vibe-to-agentic.md, rlvr.md, llm-clients-comparison.md.
- Создан practical-course.md.

## 2026-06-15 (Манифест Совета экспертов)
- Добавлен COUNCIL_RECOMMENDATIONS.md.

## 2026-06-15 (развертывание нормальной вики)
- Добавлен YAML frontmatter во все файлы.
- Созданы templates/topic-template.md и .gitignore.
- Исправлены опечатки (agendsmd -> agentsmd).

## 2026-06-16 (System Prompt + reference docs unification)
- Создан `wiki/templates/SYSTEM_PROMPT_AUTOMATION.md` — универсальный системный промт для задач «Создание автоматизаций».
- Подготовлены (в sandbox, ещё не закоммичены) `ENVIRONMENT.md` v3.0 и `MISTAKES.md` v3.0 — унифицированные reference-документы, объединяющие опыт двух проектов (Kapital + AnalizIstochnikov).
- Сессия: 3 reference-файла готовы к публикации в репо (см. `wiki/pending.md`).
- Wiki-loader: проверено, 19/19 wiki-файлов синхронизированы с GitHub.

## 2026-06-17 (research-agent workflow fix)
- Исправлен n8n workflow `FRsjN6Ab1FBGAMoM` (Research Agent v1.1).
- Bug 1: `Code — Parse Command + user_id` читал `$('webhook_yt_research').first().json.message` (не существует) → фикс на `json.body.message`.
- Bug 2: 7 HTTP нод имели `$('code_parse')` в jsonBody/jsCode — name-based reference сломан после переименования ноды в v1.1. Recursive replace → fixed.
- Зашиплено 3 PUT'а (Deactivate → PUT → Activate).
- Self-review: 2 subagent 429 → self-verify (с пометкой). Adversarial reviewer бы поймал второй bug раньше.
- Wiki-curator: MISTAKES.md §3.X (new) + n8n-api-quirks memory topic (3 новых урока).
