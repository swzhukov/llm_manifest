# Phase checklist (gstack-team)

Короткий чек-лист для каждой фазы. **Не пропускай** — но и не раздувай (если фаза пустая, skip).

## Phase 0 — разведка (skip если scope clear)

- [ ] Задал 6 вопросов (по одному, не пачкой)
- [ ] Перефразировал задачу словами пользователя
- [ ] Записал 1-параграф → переход в Phase 1

## Phase 1 — design doc (1 страница)

- [ ] Выбран scope mode (Expansion / Selective Expansion / Hold Scope / Reduction) с обоснованием
- [ ] Проблема — 1 предложение
- [ ] Целевой пользователь — 1 предложение
- [ ] Ключевые возможности — 3-5
- [ ] **Вне scope** — явный список (защита от scope creep)
- [ ] Метрика успеха — 1 число
- [ ] **Точка остановки:** показать doc, дождаться approve

## Phase 2 — архитектура (lock)

- [ ] ASCII-диаграмма основного потока
- [ ] State machine (если состояний > 2)
- [ ] Failure modes — 5-8 строк (триггер / симптом / смягчение)
- [ ] Test plan (что QA будет гонять)
- [ ] **Точка остановки:** показать диаграмму, уточнить если нужно

## Phase 3 — design review (skip для backend-only)

- [ ] Оценка 0-10 по осям (clarity / hierarchy / copy / contrast / motion)
- [ ] AI-slop detection: фиолетовый градиент, "seamless", "elevate" — push back конкретно
- [ ] План чтобы добраться до 8+

## Phase 4 — сборка

- [ ] Worktree (если есть git): `git worktree add ../<feature>`, **не коммитить в main**
- [ ] Atomic commits (conventional-commit style, 1 логическое изменение)
- [ ] Scope discipline: если фича не в design doc — **стоп**, спросить
- [ ] Learnings: `memory_topic_append` в `gstack-learnings-<slug>` после успешного паттерна

## Phase 5 — review (ОБЯЗАТЕЛЬНО через spawn verifier)

- [ ] **НЕ ревьюить сам** — adversarial pass
- [ ] Сначала проверить готовых peer-агентов: `mavis { command: "session list", args: { mode: "peers" } }` → искать `verifier`
- [ ] Если есть готовый Verifier — `communicate { to_session: <id> }`
- [ ] Если нет — `communicate { spawn: { agent_name: "verifier" } }`
- [ ] Передать: 4 принципа Карпатого + типичные грабли (race, null, deadlock, secrets, parse_mode Markdown)
- [ ] Auto-fix очевидного, flag остальное пользователю
- [ ] **НЕ переписывать** flagged areas молча

## Phase 6 — QA (skip если нечего запускать)

- [ ] Happy path
- [ ] 3-5 edge cases из failure modes
- [ ] Каждый fix → regression test
- [ ] Если есть test infra — прогнать сам
- [ ] Если нет — team plan (producer + verifier)

## Phase 7 — ship

- [ ] Tests pass
- [ ] Документация актуальна (CLAUDE.md, README, ARCHITECTURE)
- [ ] Нет debug code, TODO без owner, hardcoded secrets
- [ ] Один абзац «что зашиплено, что дальше»
- [ ] **Сначала** summary пользователю, **потом** merge worktree
- [ ] **После шипа:** `wiki-curator` — зафиксировать новые знания в `swzhukov/llm_manifest`
- [ ] **Точка остановки:** «зашиплено. Что дальше?»

## Karpathy 4 (чек на Phase 5)

1. Think — код делает то, чего design doc не просил?
2. Simplicity — что можно выкинуть?
3. Surgical — изменения, которые влияют на что-то незаявленное?
4. Goal-driven — есть ли измеримый критерий успеха, и достигнут ли он?

## Failure handling (one-liner)

- Skip planning → respect, flag риск, proceed
- Scope меняется → рестарт Phase 1 в Reduction
- Scope > 1 сессия → narrowest wedge + backlog
- Review critical → fix до QA
- Sub-agent завис → retry через 5 сек, иначе self-review с пометкой
- Нет git → обычный каталог, `git init && git add -A && git commit -m init: project skeleton`
