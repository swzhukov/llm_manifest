---
name: wiki-loader
description: "Загружает контекст среды пользователя (VPS Beget, n8n, Flask, Telegram, YandexGPT) и базу ошибок из github.com/swzhukov/llm_manifest в оперативную работу Mavis. Применяй когда задача про деплой, настройку сервисов, интеграции, дебаг автоматизаций, или явно упоминаются n8n / Flask / Telegram / YandexGPT / 1С. НЕ применять для чистых вопросов про LLM-методологию (wiki/COUNCIL_RECOMMENDATIONS.md напрямую), research-задач (web_search), мелких one-shot правок."
---

# wiki-loader

## Что делает

Подтягивает в рабочий контекст **два слоя** базы знаний пользователя:

1. **Среда** (ENVIRONMENT.md) — VPS Beget 1 vCPU/1.9 GB, n8n 2.17.7 в Docker, Flask monolith, Telegram-боты, YandexGPT, конкретные пути, секреты, helper-скрипты.
2. **Ошибки** (MISTAKES.md) — 95+ задокументированных грабель с root cause и решениями.
3. **Методология** (wiki/AGENTS.md + wiki/COUNCIL_RECOMMENDATIONS.md) — 4 принципа Карпатого + 10 принципов Совета.

## Когда срабатывает (триггеры)

Ключевые слова в запросе пользователя:
- «n8n», «workflow», «HTTP Request node», «Webhook node», «Telegram Trigger»
- «Flask», «newton-api», «endpoint», «state.json», «state_store»
- «Telegram-бот», «inline keyboard», «callback_data», «Bot Menu», «parse_mode»
- «YandexGPT», «Yandex», «folder_id», «IAM token», «daily cap»
- «VPS», «Beget», «docker», «systemd», «.env», «ssh», «ForceCommand»
- «1С», «1C», «HTTP-сервис», «обмен с 1С»
- «deploy», «деплой», «задеплой», «разверни», «настрой»
- «не работает», «упало», «ошибка 500», «health check failed»
- «уже пробовал», «раньше работало», «опять сломалось»

**Не срабатывает** на:
- «что такое Karpathy», «расскажи про RLVR», «как работает LLM» (методология → читай wiki/topics/ напрямую, без skill'а)
- «поищи в интернете», «что нового в n8n 2.18» (research → web_search)
- одну команду `pkill -9 python` или переименование файла (overhead)

## Алгоритм

### Шаг 1. Убедиться, что репо актуально

```bash
cd /workspace/llm_manifest
git fetch origin 2>&1 | tail -3
git status  # есть ли локальные незакоммиченные изменения
git log -1 --oneline  # текущий SHA
```

Если есть незакоммиченные изменения от прошлой сессии — **предупреди пользователя** и спроси: коммитить / откатывать / показать.

Если есть расхождение с origin (есть новые коммиты) — `git pull --rebase`.

### Шаг 2. Загрузить контекст

**Обязательно прочитать** (по убыванию важности):
1. `wiki/AGENTS.md` — 4 принципа Карпатого (think/simplicity/surgical/goal-driven)
2. `wiki/COUNCIL_RECOMMENDATIONS.md` — 10 принципов + чек-лист
3. `ENVIRONMENT.md` (целиком, 72 KB) — особенно:
   - §0 «Контекст пользователя» — кто Сергей, какой стек
   - §1 «Архитектурные паттерны» — proven решения
   - §3 «VPS Beget» — пути, ssh, docker
   - §4 «n8n» — API endpoints, паттерны нод, активация workflow
   - §5 «Flask» — структура, endpoint pattern, health check
   - §7 «Telegram» — bot menu, inline buttons, parse_mode
4. `MISTAKES.md` — **поиск по ключевым словам задачи** (не целиком):
   ```bash
   grep -n "### " MISTAKES.md | head -50  # посмотреть оглавление
   grep -B1 -A8 "sshpass\|heredoc\|folder_id\|parse_mode\|deadlock" MISTAKES.md
   ```
5. `wiki/log.md` — последние изменения (понимать, что недавно обновлялось)
6. `wiki/session-summaries.md` — контекст прошлых сессий (если нужно)

**По желанию (ленивая загрузка):**
- `wiki/topics/*` — только если задача про саму методологию LLM
- `wiki/pending.md` — отложенные вопросы

### Шаг 3. Фильтр релевантности

Не втягивай в ответ **всё** из ENVIRONMENT/MISTAKES. Применяй правило:

```
Задача: «inline-кнопка возвращает null в callback_data»

Релевантно:
- ENVIRONMENT.md §7.2 Inline keyboard — формат callback_data
- ENVIRONMENT.md §7.6 Anti-patterns Telegram-бота
- MISTAKES.md §7.2 Inline-кнопки с большим callback_data > 64 байт
- MISTAKES.md §7.3 Inline-кнопка "⬅ Назад" не работает

НЕ релевантно:
- §6 YandexGPT
- §5 Flask state management
- §12 YouTube/Piped
```

### Шаг 4. Сослаться на источник

Когда цитируешь паттерн или правило — **всегда давай ссылку**:

```
[ENVIRONMENT.md §4.5](https://github.com/swzhukov/llm_manifest/blob/main/ENVIRONMENT.md#45) — каскад IF-узлов
[MISTAKES.md §3.6](https://github.com/swzhukov/llm_manifest/blob/main/MISTAKES.md#36) — Connections ссылаются на старое имя
```

Это даёт пользователю возможность проверить и обучает его, что искать.

### Шаг 5. Обновить runtime-кэш

В конце сессии (или при коммите результата) — обнови memory topic `llm-manifest-state`:
- новый SHA после pull
- пометка, что читал ENVIRONMENT/MISTAKES
- какие секции были релевантны (для будущих сессий)

Это не обязательно, но помогает следующему skill'у понять, что уже в контексте.

## Запрещено

- ❌ Делать вид, что я уже знаю содержимое wiki, не прочитав. Среда меняется (юзер сам сказал про `n8n 2.17.7`, это могло обновиться).
- ❌ Цитировать устаревшие уроки (проверять дату в frontmatter).
- ❌ Применять советы из MISTAKES к задачам вне среды (например, советы про Beget к Colab).
- ❌ Пушить изменения в wiki от имени юзера без явного подтверждения (это работа `wiki-curator`, не моя).

## Связь с другими skill'ами

- **`wiki-curator`** — после задачи решает, обновлять ли вики.
- **`gstack-team`** — если задача оказалась multi-file (3+ файлов, архитектурное решение), передать управление ему.
- **`worktree-management`** — если нужны изменения в коде проекта, открыть worktree.

## Smoke test

Чтобы проверить, что skill сработал, должно быть видно в ответе:
- ✅ Конкретная ссылка на `ENVIRONMENT.md §X.Y` или `MISTAKES.md §X.Y`
- ✅ Применён 1 из 4 принципов Карпатого (чаще всего Surgical или Goal-driven)
- ✅ Предложение — opinionated default, не «можно A или B»
- ✅ Нет hedging («возможно», «может быть», «попробуй»)
