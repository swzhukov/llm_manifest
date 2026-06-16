# gstack-team (Mavis skill)

Multi-role виртуальная команда инженеров (CEO / Eng Manager / Designer / Reviewer / QA / Security / Release) для нетривиальных multi-file / архитектурных / pre-ship задач. Реализация методологии [garrytan/gstack](https://github.com/garrytan/gstack) на средствах Mavis (без Claude Code).

## Состав

- `SKILL.md` — основная инструкция с 8 фазами
- `references/phases.md` — короткий чек-лист для Phase 0-7
- `scripts/sprint-log.py` — генератор `sprint-log.md` из параметров

## Когда применяется

- 3+ файлов, новая фича, модуль, сервис
- Запросы: «собери», «ship it», «проведи аудит», «разбери», «построй фичу»
- Архитектурное решение (БД, API shape, system split)
- Pre-ship аудит (security, perf, design consistency)

**НЕ применять** на: опечатки, rename, one-shot fix, чистые вопросы, research.

## Ключевые правила

1. **Phase 5 — ОБЯЗАТЕЛЬНО через spawn verifier'а** (или готового peer Verifier). Не саморевью.
2. **Phase 7** вызывает `wiki-curator` — фиксирует новые знания в `swzhukov/llm_manifest`.
3. **Scope discipline** в Phase 4: если фича не в design doc — стоп, спросить пользователя.

## Генерация sprint log

```bash
python3 scripts/sprint-log.py \
  --task "feature-x" \
  --mode "Hold Scope" \
  --worktree "../feature-x" \
  --phases "1:design,2:arch,4:build,5:review,7:ship" \
  --decisions "Used n8n HTTP node;Webhook polling" \
  --deferred "Admin panel;Email fallback" \
  --learnings "1C: refresh token before request" \
  --out sprint-log.md
```

## Связь

- Phase 2 использует `wiki-loader` для контекста среды
- Phase 7 вызывает `wiki-curator` для обновления wiki
