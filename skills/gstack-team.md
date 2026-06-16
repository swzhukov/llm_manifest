---
name: gstack-team
description: Multi-role виртуальная команда инженеров (CEO / Eng Manager / Designer / Reviewer / QA / Security / Release) для нетривиальных multi-file / архитектурных / pre-ship задач. Применяй когда задача явно 3+ файлов, требует архитектурного решения, нужен pre-ship аудит, или пользователь явно сказал «сделай», «собери», «ship it», «проведи аудит», «разбери проект». НЕ применять на: опечатки, rename, one-shot fix, чистые вопросы, research-задачи, установку самого gstack.
---

# GStack Team (реализация для Mavis)

## Концепция

**Garry Tan / gstack** (github.com/garrytan/gstack, 110K ⭐, MIT) — фреймворк, который превращает Claude Code в виртуальную команду из 23 ролей с явным спринт-процессом. У пользователя может не быть Claude Code. **Механика переносима** — Mavis умеет поднимать субагентов через `communicate { spawn }` и `team`-план. Каждый «специалист» gstack = субагент с конкретной ролью, system prompt и задачей.

**Что берём из gstack:**
- Sprint с явными фазами и точками остановки
- Ролевое мышление (CEO rethinker / Eng lock / Designer / Reviewer / QA / Security)
- «Confusion Protocol» — не угадывать архитектуру, а спрашивать
- 4 принципа Карпатого как жёсткий чек-лист (см. `wiki/AGENTS.md`)
- Skill registry — накапливаем находки через `memory_topic_append`
- Atomic commits через `worktree-management`
- Code review перед ship — **обязательно через второго агента**, не саморевью

**Что НЕ берём (требует Claude Code / Chromium / GPT Image):**
- `/browse` через GStack Browser
- `/design-shotgun` визуальные mockup-варианты
- `/openclaw` спавн Claude Code сессий
- `/ios-qa` через USB CoreDevice

## Когда применять

Перед стартом — sanity check. `task complexity >= medium`?
- 3+ файлов или новый модуль/сервис → ДА
- Архитектурное решение (БД, API shape, system split) → ДА
- Pre-ship аудит (security, perf, design consistency) → ДА
- Опечатка / rename / one-shot fix → НЕТ, не нужен skill

## Что собрать до старта (не переспрашивать если уже есть)

- Сама задача. Если scope мутный — Phase 0 разберётся.
- Стек пользователя: peek memory topics `beget-vps-access`, `bash-pitfalls`, `n8n-api-quirks`.
- Дедлайн: «до завтра», «хобби» → это меняет режим scope.
- Доступен ли git-репо (нужен для Phase 4 worktree). Если нет — Phase 4 работает в обычном каталоге без worktree. Если нет git вообще — `git init && git add -A && git commit -m "init: project skeleton"`.

## 8 фаз спринта

Каждая фаза = конкретные вызовы инструментов и явная точка остановки. **Не пропускать фазы «для скорости»** — это рецепт переделывать.

### Phase 0 — разведка (только если scope мутный)

**Триггер:** пользователь сказал «хочу сделать X», но X можно понять 3+ способами.
**Цель:** вытащить реальную боль до планирования.

Задать **6 вопросов, по одному за раз** (через `AskUserQuestion` в чате):

1. Конкретная боль + **реальный пример**, не гипотетика
2. Что уже пробовал, почему не сработало
3. Кто ещё с этой болью, как выкручиваются
4. Если волшебная палочка — что идеально
5. Самая узкая первая версия — как выглядит
6. Что заставит через 30 дней бросить

**После 6 ответов:** перефразировать продукт словами пользователя. Часто описана фича, а нужна категория. Записать 1-параграф → Phase 1.

**Skip** если ТЗ чёткое.

### Phase 1 — design doc (1 страница)

4 режима scope — выбрать один и сказать почему в одном предложении:

| Режим | Когда | Эффект |
|---|---|---|
| **Expansion** | Идея undersold, может быть 10x | Добавляем возможности |
| **Selective Expansion** | Ядро расширить, края держать | Микс |
| **Hold Scope** | Scope правильный, just execute | Без изменений |
| **Reduction** | Oversold, MVP режется до 1 вещи | Убираем возможности |

**Не спрашивать какой** — рекомендовать opinionated default (фаундер не любит hedging).

**Артефакт** — 1-страничный design doc в чате:

```
# Design doc: <task-name>
**Режим:** Hold Scope
**Дедлайн:** 2026-06-15

## Проблема (1 предложение)
Пользователь не может записаться на услугу без звонка.

## Целевой пользователь (1 предложение)
Жители СПб, 25-45, записываются 1-3 раза в год.

## Ключевые возможности (3-5)
- Telegram-бот с каталогом услуг
- Бронирование слота
- Оплата через ЮKassa
- Напоминание за 24ч

## Вне scope (явный список — защита от разрастания)
- Админ-панель
- Аналитика / дашборд
- Мульти-тенант
- Email-фоллбек при сбое оплаты
- iOS-приложение

## Метрика успеха (1 число)
50 уникальных пользователей записались через бота за 30 дней.
```

**Точка остановки:** показать doc, спросить «approve / change X». **Не идти дальше без одобрения.** Если пользователь меняет scope — рестарт Phase 1.

### Phase 2 — архитектура (lock)

Для кода: data flow, state machine, error paths, edge cases.

**Артефакт:**

**a) Диаграмма** (ASCII или mermaid) основного потока:

```
[Telegram user]
   │  /start
   ▼
[Telegram Bot API]
   │  webhook
   ▼
[n8n workflow: handle_message]
   │
   ├─→ [Supabase: save user]
   ├─→ [1C HTTP-service: GET services]
   │      │
   │      ▼
   │   [1C: return JSON catalog]
   │
   └─→ [Telegram API: send message]
```

**b) State machine** (если состояний > 2):

```
new → awaiting_payment → paid → confirmed → done
                                  ↘ no_show
                                  ↘ cancelled
```

**c) Failure modes** (5-8 строк):

| Триггер | Симптом | Смягчение |
|---|---|---|
| ЮKassa webhook timeout | Бот не знает что оплата прошла | Polling статуса каждые 60с, max 5 попыток |
| 1С HTTP-service недоступен | Бот не может получить каталог | Кэш каталога в Supabase, fallback на stale data |
| Double-click на оплату | 2 платежа, 1 слот | Идемпотентность по `payment_id`, отменять дубль |
| Telegram rate limit | Сообщения не доходят | Queue в n8n, retry с exp backoff |
| Webhook signature invalid | Кто-то шлёт фейки | Проверка signature в 1С перед обработкой |

**d) Test plan** — что QA-фаза будет гонять:
- Happy path: бот → выбор услуги → оплата → подтверждение
- Edge: оплата без выбора слота, двойной клик, отмена после оплаты
- Failure: 1С лежит, webhook приходит дважды, юзер пишет в бот во время оплаты

**Специфика среды пользователя** (если стек = Beget/n8n/Flask/Telegram/1С):
- Использовать паттерны из `ENVIRONMENT.md` (см. skill `wiki-loader`)
- Проверить `MISTAKES.md` на похожие грабли (см. `wiki-loader`)

**Точка остановки:** показать диаграмму + failure modes. Если нужны уточнения по стеку — спросить (**Confusion Protocol: не угадывать архитектурные решения**).

### Phase 3 — design review (только user-facing)

**Skip** для backend-only / pure-data / API-only. Для UI/UX/bot flows: оценить дизайн 0-10 по осям (clarity, hierarchy, copy, contrast, motion), описать что такое 10, отредактировать план чтобы добраться до 8+.

**AI-slop detection** — если дизайн как у всех SaaS-лендингов (фиолетовый градиент, «seamless», «elevate»), push back конкретно.

### Phase 4 — сборка

Только сейчас писать код. Ссылаться на design doc (Phase 1) и test plan (Phase 2).

**Механики:**

- **Worktree:** если есть git-репо — `git worktree add ../feature-x` через skill `worktree-management`. **Не коммитить в main.**
- **Atomic commits:** conventional-commit style, 1 логическое изменение:
  ```
  feat(bot): add slot selection handler
  fix(1c): handle null service_id in catalog response
  ```
- **Scope discipline:** если нашёл фичу которой нет в design doc — **остановись**, скажи пользователю, **не делай молча**. Спроси «это в scope или out?»
- **Learnings:** после успешного паттерна → `memory_topic_append` в topic `gstack-learnings-<task-slug>` (slug чтобы не было конфликта при параллельных спринтах). Это skill registry из gstack, но через память Mavis.
- **Conventional commits на русском** — допустимо, если в репо так принято.

### Phase 5 — code review (staff engineer audit)

**КРИТИЧНО: поднимать через `communicate { spawn }` субагента-ревьюера. НЕ ревьюить сам** — нужен adversarial pass, не самообман.

**Приоритет агентов (проверять в указанном порядке):**

1. **Сначала проверить готовых peer-агентов** через `mavis { command: "session list", args: { mode: "peers", session_id: "me" } }` — искать агента `verifier` или `Verifier` в списке.
2. **Если есть готовый Verifier-агент** — дёргать его напрямую (это дешевле spawn'а, он уже настроен):
   ```
   communicate({
     to_session: "<verifier_session_id>",
     content: "GStack review of feature-x..."
   })
   ```
3. **Если готового нет** — `communicate { spawn }` субагента `verifier`:
   ```
   communicate({
     spawn: { agent_name: "verifier", title: "GStack review of feature-x" },
     content: "Загрузи .skills/gstack-team/SKILL.md.
     Проверь код в worktree ../feature-x.
     Используй 4 принципа Карпатого (wiki/AGENTS.md):
     1. Think — что в коде не соответствует design doc?
     2. Simplicity — что можно выкинуть без потери функционала?
     3. Surgical — что меняет поведение незаявленно?
     4. Goal-driven — есть ли измеримый критерий успеха, и достигнут ли он?
     + типичные грабли (race conditions, unhandled null, missing
     transactions, hardcoded secrets, no error path, deadlock на lock,
     SSH heredoc, parse_mode Markdown).
     Output: список issues, severity (critical/major/minor),
     конкретные fix-предложения с file:line.
     Не правь код сам — только отчёт."
   })
   ```

**Способ 2 — team-план** для критичных PR (security, prod):
producer пишет review, verifier независимо проверяет review. Стоит дороже (2 агента), использовать только для high-stakes.

**Способ 3 — для security/audit-задач ВСЕГДА использовать team-план** (не spawn). Audit = high-stakes by definition.

**Auto-fix** для очевидного (race condition без последствий, unused imports, лёгкие type mismatch).
**Flag** для остальных — показать пользователю с конкретными предложениями.
**НЕ переписывать молча** flagged areas.

### Phase 6 — QA (только если есть что запустить)

**Skip** для статичных доков / чистого planning. Иначе:
- Happy path
- 3-5 edge cases из failure modes table (Phase 2)
- Каждый fix → regression test (чтоб не повторилось)

**Механика:**
- Если есть test infra (pytest, 1С xUnitFor1C) — прогнать сам через bash.
- Если нет — поднять `team` план: producer пишет тесты, verifier гоняет их.
- Для n8n workflow — поднять sub-agent: «проверь этот workflow против 5 сценариев, отчёт с input/output».

### Phase 7 — ship

**Финальные проверки:**
- Tests pass
- Документация актуальна (CLAUDE.md, README, ARCHITECTURE) — Phase 4 мог добавить функционал которого нет в доке
- Нет leftover debug code, TODO без owner, hardcoded secrets
- Один абзац «что зашиплено, что дальше»

**Сначала** показать пользователю summary, **потом** merge worktree в main через `worktree-management` (`merge → cleanup`).

**После шипа вызвать `wiki-curator`** — зафиксировать новые знания из спринта (ошибки, паттерны, сервисы) в `swzhukov/llm_manifest`.

**Точка остановки:** «зашиплено. Что дальше?» — **не подталкивать** к продолжению.

## Формат вывода

- В каждом сообщении **имя фазы** (Phase 1, Phase 5...) и какой следующий шаг. Никогда не прыгать молча между фазами.
- Конкретные артефакты на каждой фазе (design doc, диаграмма, код, test report) — не стена текста.
- Финальный **sprint log** в workspace: список фаз, решения, отложенное, путь к worktree, ключевые находки (если были).

## 4 принципа Карпатого (жёсткий чек-лист на Phase 5)

1. **Think** — код делает то, чего design doc не просил?
2. **Simplicity** — что можно выкинуть без потери функционала?
3. **Surgical** — изменения, которые влияют на что-то незаявленное?
4. **Goal-driven** — где hardcode вместо config, branch вместо table, копипаста вместо функции? Есть ли измеримый критерий успеха?

## Обработка ошибок

- **Пользователь хочет skip planning** — respect, предупредить риск в 1 предложении, продолжить. Не переспрашивать.
- **Scope меняется посреди спринта** — стоп, рестарт Phase 1 в Reduction, новый design doc, продолжить. **Не патчить старый план in place.**
- **Scope слишком большой для одной сессии** — narrowest wedge, зашипить его, остальное в «Phase 2» backlog.
- **Build показывает что план был неправильный** — surface противоречие, 2 опции, пусть пользователь выберет. Не делать вид что старый план ОК.
- **Review нашёл critical issue** — fix до QA, не откладывать.
- **Пользователь ушёл посреди спринта** — оставить resume note через `memory_topic_append` чтобы следующая сессия подхватила.
- **Sub-agent в Phase 5 завис / не отвечает** — retry один раз через 5 секунд (см. Report-back failure protocol). Если снова fail — написать review сам, но **пометить пользователю** что это self-review, не adversarial.
- **Нет git-репо** — Phase 4 работает в обычном каталоге, atomic commits не нужны, просто писать файлы. Подсказать пользователю: `git init && git add -A && git commit -m "init: project skeleton"`.

## Anti-patterns

- Запускать все 8 фаз ради опечатки. Skill = overhead.
- Skip Phase 1 и сразу кодить. **#1 рецепт «AI построил не то».**
- Phase 4 пилит фичи которых нет в design doc. Scope creep.
- Phase 5 ревью как rubber stamp. Найти ≥ 2 реальных issue или признать что код чист — **не выдумывать**.
- Использовать skill как ceremony. Каждая фаза = реальный артефакт. Если фаза пустая — skip.
- Саморевью в Phase 5 (вот это самая частая грабля — агент смотрит на свой код и говорит «всё ок»). **Всегда spawn verifier'а.**

## Sprint log template (положить в workspace/sprint-log.md)

```markdown
# Sprint log: <task-name>
**Date:** 2026-06-13
**Режим:** Hold Scope
**Worktree:** ../feature-x
**Status:** shipped

## Phases run
- [x] Phase 0 (skip — spec clear)
- [x] Phase 1 (design doc, 1 page)
- [x] Phase 2 (eng review, 5 failure modes, state machine)
- [ ] Phase 3 (skip — no UI)
- [x] Phase 4 (build, 3 atomic commits)
- [x] Phase 5 (review via spawn, 2 issues: critical race + minor naming)
- [x] Phase 6 (qa, 4/4 happy + 3/5 edge pass)
- [x] Phase 7 (ship, merged to main, wiki-curator обновил MISTAKES §3.X)

## Решения
- Использовал n8n HTTP-request node для интеграции с 1С (нужны retries)
- ЮKassa через polling, не webhook (нет публичного URL)
- Пропустил multi-tenant — out of scope per design doc
- Idempotency key = `${user_id}:${slot_id}`

## Отложено (backlog → Phase 2)
- Админ-панель
- Многоязычный UI бота
- Email fallback при ошибке оплаты
- Аналитика (PostHog / Yandex.Metrica)

## Ключевые находки → memory / wiki
- 1С HTTP-service: Basic auth, token TTL=4h, refresh безопасен
  (записано в `gstack-learnings-feature-x/1c-http`)
- n8n error workflow: должен быть idempotent, иначе double-charge
  (записано в `gstack-learnings-feature-x/n8n-idempotency`)
- После шипа wiki-curator обновил `MISTAKES.md §3.16` про новый edge case
```

## Примеры

### Пример 1 — Full sprint, Telegram-бот + ЮKassa + 1С

**Запрос:** «сделай Telegram-бота для записи на услуги с оплатой ЮKassa и хранением в 1С»

**Путь:**
- Phase 0 skip (spec чёткое)
- Phase 1: Hold Scope. Design doc в чате. Вне scope: админ-панель, аналитика, мульти-тенант, email-фоллбек, iOS-приложение. Метрика: 50 уникальных юзеров за 30 дней.
- Phase 2: data flow (user → TG → n8n → 1С → back), state machine (new → awaiting_payment → paid → confirmed → done/no_show/cancelled), 5 failure modes (webhook timeout, double-pay, 1С down, rate limit, invalid signature). Test plan: 4 happy + 5 edge.
- Phase 3 skip (UX бота в Phase 2).
- Phase 4: worktree `../feature-bot`, собрать n8n workflow (5 нод) + 1С HTTP-service (2 endpoint'а). 3 atomic commits. Находка про idempotency в memory.
- Phase 5: spawn verifier. Нашёл race на double-booking + minor naming. Auto-fix critical, flag minor.
- Phase 6: qa flow с тестовым платежом ЮKassa. 4/4 happy pass, 3/5 edge pass.
- Phase 7: merge worktree, **wiki-curator обновил MISTAKES §3.16**, sprint log, ship summary.

### Пример 2 — Skip skill'а (one-shot fix)

**Запрос:** «просто почини баг с дубликатами в отчёте»

**Не применять skill.** Один вызов инструмента, поправил, готово.

### Пример 3 — Audit-only (ship = отчёт)

**Запрос:** «проведи аудит безопасности моего n8n workflow»

**Путь:**
- Phase 0 skip, Phase 1 Hold Scope (audit-only, без изменений кода)
- Phase 2: identify surfaces (webhooks, credentials, file attachments, exposed HTTP triggers, error workflow data leakage)
- Phase 3-4 skip
- **Phase 5: ОБЯЗАТЕЛЬНО через `team`-план** (audit = high-stakes by definition). Producer ищет issues, verifier независимо проверяет находки. OWASP-style checklist + n8n-специфика (credentials в plaintext, error workflow логирует PII).
- Phase 6-7 skip / или «ship = findings report». **wiki-curator обновит MISTAKES §X.Y про новые security-находки.**

### Пример 4 — Resume после ухода

**Прошлая сессия:** Phase 4 шёл, пользователь закрыл чат на середине сборки.

**Resume:** прочитать `memory_topic_append("gstack-learnings-feature-x", "active sprint: feature-x, Phase 4 in progress, 2/3 commits done, current task: add webhook handler. Out of scope per design doc: admin panel, email fallback.")` → Phase 4 продолжается, не перезапускать с нуля.

## Связь с другими skill'ами

- **`wiki-loader`** — в Phase 2 загружает контекст среды пользователя из `swzhukov/llm_manifest` (паттерны из ENVIRONMENT, грабли из MISTAKES).
- **`wiki-curator`** — в Phase 7 фиксирует новые находки из спринта в `swzhukov/llm_manifest` (MISTAKES/ENVIRONMENT/COUNCIL).
- **`worktree-management`** — в Phase 4 для git worktree.
