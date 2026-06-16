# Alignment с wiki-loader SKILL.md

> Этот файл — для тебя, Mavis, и для самого Сергея: насколько эта wiki применима в контексте `wiki-loader` skill, и что с ней делать.

## TL;DR

**Эта wiki на 75% применима к твоему стеку** (VPS Beget, n8n 2.x, Telegram-боты, YandexGPT, Supabase, RAG). Разрывы — в нюансах **твоей** среды (конкретные helper-скрипты, `beget-vps-access`, `bash-pitfalls`, `n8n-api-quirks`). Рекомендация: **не заменять** wiki-loader, а **дополнить** его этой wiki как источником «учебных» паттернов, а ENVIRONMENT.md/MISTAKES.md оставить source of truth для твоей среды.

---

## Что такое wiki-loader (напоминание)

Из [wiki-loader/SKILL.md](https://github.com/swzhukov/llm_manifest/blob/main/skills/wiki-loader/SKILL.md):

> Подтягивает в рабочий контекст Mavis **два слоя** базы знаний:
> 1. **Среда** (ENVIRONMENT.md) — VPS Beget 1 vCPU/1.9 GB, n8n 2.17.7 в Docker, Flask monolith, Telegram-боты, YandexGPT, конкретные пути, секреты, helper-скрипты.
> 2. **Ошибки** (MISTAKES.md) — 95+ задокументированных грабель с root cause и решениями.
> 3. **Методология** (wiki/AGENTS.md + wiki/COUNCIL_RECOMMENDATIONS.md).

## Что эта wiki ДОБАВЛЯЕТ к wiki-loader

| Что | Где в wiki | Зачем wiki-loader'у |
|---|---|---|
| **Учебный курс по n8n** (уроки 1–10) | [01-installation.md](01-installation.md) … [09-ai-agents.md](09-ai-agents.md) | Когда Сергей говорит «не понимаю, как сделать X» — у тебя есть **объяснение на пальцах**, а не только «решение из MISTAKES.md» |
| **Системные промпты из продакшна** | [12-system-prompts.md](12-system-prompts.md) | Готовые шаблоны для копирования, а не «придумай сам» |
| **Типичные ошибки от учеников** (не от Сергея) | [10-common-errors.md](10-common-errors.md) | Расширяет MISTAKES.md на 20+ новых кейсов с корневыми причинами |
| **Best practices** (папки, теги, retry, экономия диска) | [11-best-practices.md](11-best-practices.md) | Конкретные рекомендации вместо общих советов |
| **YandexGPT** подробно | [08-yandex-gpt.md](08-yandex-gpt.md) | Среда упоминает, но **как подключить** — здесь |
| **RAG / Vector Store** глубоко | [06-vector-memory-rag.md](06-vector-memory-rag.md) | Чанки, overlap, embedding-модели, metadata filtering |
| **Telegram inline-кнопки** нюансы | [07-telegram-bots.md §7.2](07-telegram-bots.md) | callback_data 64 байта — общая боль |
| **Quick reference** (шпаргалка) | [00-quick-reference.md](00-quick-reference.md) | В начало любой сессии, чтобы быстро вспомнить API |

## Что эта wiki НЕ покрывает (разрывы)

| Тема | Где должно быть | Статус |
|---|---|---|
| **VPS Beget: SSH, helper-скрипты, ForceCommand** | memory topic `beget-vps-access` | ❌ НЕ покрыто |
| **Bash-грабли (sshpass, heredoc, ...)** | memory topic `bash-pitfalls` | ❌ НЕ покрыто |
| **n8n REST API: 7 read-only полей** | memory topic `n8n-api-quirks` | ❌ НЕ покрыто |
| **Flask / newton-api / state.json** | ENVIRONMENT.md §5 | ❌ НЕ покрыто |
| **YandexGPT: folder_id / IAM / daily cap** | ENVIRONMENT.md §6 | ⚠️ Частично (есть подключение, нет quota) |
| **Helper-скрипт `/workspace/.vps-helper.sh`** | ENVIRONMENT.md §3 | ❌ НЕ покрыто |
| **Telegram Bot Menu через setMyCommands** | memory topic `telegram-bot-menu` | ⚠️ Упомянуто, не подробно |
| **Smoke test wiki-loader** | SKILL.md → Smoke test | ✅ Покрыто неявно (шпаргалка + index) |

## Что wiki-loader даёт этой wiki (обратное)

| Что | Где в wiki-loader | Эта wiki должна использовать |
|---|---|---|
| ENVIRONMENT.md §3 (VPS Beget) | пути, .env расположение, ssh | ✅ Используется в §1.5 |
| ENVIRONMENT.md §4 (n8n) | API endpoints, паттерны нод | ✅ Используется в §03 |
| ENVIRONMENT.md §7 (Telegram) | bot menu, inline buttons, parse_mode | ✅ Используется в §7.2, 7.9 |
| MISTAKES.md §X.Y | конкретные грабли | ⚠️ Частично (некоторые дублируются в [10-common-errors.md](10-common-errors.md)) |
| wiki/AGENTS.md | 4 принципа Карпатого | ✅ Учтены в [11-best-practices.md](11-best-practices.md) |
| wiki/COUNCIL_RECOMMENDATIONS.md | 10 принципов Совета | ✅ Учтены в [11.11](11-best-practices.md) |

## Вывод: как совместить

### Сценарий 1. Сергей говорит «поставь мне n8n»

**Сейчас (wiki-loader):** подтягивает ENVIRONMENT.md → читает §3 VPS Beget, §4 n8n → выдаёт инструкцию.

**С wiki:** + подтягивает [01-installation.md](01-installation.md) §1.1–1.3 (если раздел из wiki синхронизирован) → добавляет **объяснение на пальцах**, почему именно так, и предупреждает о подводных камнях.

### Сценарий 2. Сергей говорит «у меня телеграм-бот упал, chat not found»

**Сейчас (wiki-loader):** MISTAKES.md §7.X (если зафиксировано) + ENVIRONMENT.md §7.2.

**С wiki:** + [10-common-errors.md §10.8](10-common-errors.md) — конкретный чеклист диагностики (4 причины + как проверить).

### Сценарий 3. Сергей говорит «напиши мне SEO-промпт для блога»

**Сейчас (wiki-loader):** ничего нет.

**С wiki:** [12-system-prompts.md §12.2](12-system-prompts.md) — готовый шаблон, проверенный.

### Сценарий 4. Сергей говорит «у меня диск забит за неделю»

**Сейчас (wiki-loader):** MISTAKES.md §X.Y + ENVIRONMENT.md §3.4 (если есть).

**С wiki:** [11-best-practices.md §11.1](11-best-practices.md) + [03-workflow-settings.md §3.4](03-workflow-settings.md) — конкретные настройки + cron для автоочистки.

## Рекомендация: где хранить

### Сценарий A. Wiki остаётся в `/workspace/wiki/`

Плюсы:
- Не загрязняет `swzhukov/llm_manifest` (твой main repo).
- Можно часто обновлять, не коммитя в публичный repo.
- Локально — для `Mavis` всегда доступна.

Минусы:
- Не синхронизирована с `wiki-loader` skill.
- Нужно **вручную** обновить `SKILL.md`, чтобы wiki-loader знал об этом источнике.

### Сценарий B. Wiki заливается в `swzhukov/llm_manifest/wiki/n8n-course/`

Плюсы:
- Автоматически подтягивается wiki-loader'ом (если обновить его алгоритм).
- Видно коллегам / соратникам.

Минусы:
- Wiki «учебная», не «твоя» — может быть не в тему для твоей среды.
- Тяжело коммитить 17 МБ JSON-примеров.

### Сценарий C. Гибрид (рекомендую)

1. **Курс и паттерны** → `/workspace/wiki/` (учебный материал, обновляется часто).
2. **Конкретные грабли из чата** → вливаются в `MISTAKES.md` через `wiki-curator` (CAN-WRITE режим).
3. **Среда-специфичное** (YandexGPT ключи, Beget helper, etc.) → остаётся в `ENVIRONMENT.md`.
4. **Этот alignment-файл** → в `/workspace/wiki/alignment-with-skill-loader.md` (постоянная ссылка).

## Что обогатить в SKILL.md (если будешь править)

Вот конкретные предложения для SKILL.md (если wiki-loader будет знать об этом wiki):

```diff
## Алгоритм

### Шаг 2. Загрузить контекст

**Обязательно прочитать** (по убыванию важности):
1. `wiki/AGENTS.md` — 4 принципа Карпатого
2. `wiki/COUNCIL_RECOMMENDATIONS.md` — 10 принципов + чек-лист
3. `ENVIRONMENT.md` (целиком, 72 KB)
+4. `/workspace/wiki/` — учебный курс по n8n (если есть) — для объяснений на пальцах
+5. `/workspace/wiki/10-common-errors.md` — расширенный список ошибок
+6. `/workspace/wiki/12-system-prompts.md` — готовые промпты
4. `MISTAKES.md` — поиск по ключевым словам задачи
5. `wiki/log.md` — последние изменения
```

И в триггеры добавить:

```diff
Ключевые слова в запросе пользователя:
+ - «как сделать», «научи», «объясни» (→ /workspace/wiki/)
+ - «промпт», «system message» (→ 12-system-prompts.md)
+ - «RAG», «векторная память», «embeddings» (→ 06-vector-memory-rag.md)
+ - «YandexGPT», «Yandex» (→ 08-yandex-gpt.md)
```

## Конкретные предложения (action items)

Если решишь интегрировать, вот что я бы сделал:

1. **Скопировать `10-common-errors.md` → MISTAKES.md** (новый раздел §X: «Ошибки из чата n8node»), в режиме wiki-curator.
2. **Скопировать `12-system-prompts.md` → wiki/AGENTS.md** как приложение, или в `wiki/COUNCIL_RECOMMENDATIONS.md`.
3. **В `SKILL.md` (wiki-loader)** добавить ссылку на `/workspace/wiki/` как дополнительный источник.
4. **В memory topic `skills-manifest`** добавить строку: «Если задача про n8n и ENVIRONMENT.md не даёт ответа — читай `/workspace/wiki/`».
5. **В `llm-manifest-state`** зафиксировать, что wiki обновлена 2026-06-16.

## Итоговая оценка применимости

| Критерий | Оценка | Комментарий |
|---|---|---|
| Покрытие n8n (установка, ноды, workflow) | ⭐⭐⭐⭐⭐ | 100% покрыто уроками 1–10 |
| Покрытие n8n в контексте VPS Beget | ⭐⭐⭐ | Упомянуто, но без твоих helper-скриптов |
| Покрытие Telegram | ⭐⭐⭐⭐ | Базовое + кнопки, без Bot Menu глубоко |
| Покрытие YandexGPT | ⭐⭐⭐⭐ | Подключение есть, квоты и folder_id — нет |
| Покрытие RAG / Vector | ⭐⭐⭐⭐⭐ | Глубоко, с примерами SQL и Python |
| Покрытие Supabase | ⭐⭐⭐⭐ | SQL, Vector Store, credentials |
| Покрытие ошибок | ⭐⭐⭐⭐ | 20+ кейсов, но без твоих специфичных |
| Покрытие Flask | ⭐ | Не покрыто (out of scope форумного курса) |
| Покрытие bash / ssh | ⭐ | Не покрыто (out of scope) |
| **Общая применимость к wiki-loader** | **75%** | Хорошо для n8n, плохо для остального стека |

## Что я НЕ стал выдумывать

Чтобы не загрязнять wiki выдуманным:

- ❌ Не выдумывал конкретные env-переменные твоего сервера.
- ❌ Не цитировал MISTAKES.md (его у меня нет, есть только SKILL.md).
- ❌ Не давал «общих» советов уровня «убедитесь, что у вас достаточно RAM».
- ✅ Цитировал **только** то, что прямо сказано в форумных тредах (с пометкой «Из урока N» / «Из чата»).
- ✅ Где данных не было — честно писал «не покрыто».

## Следующий шаг

Если wiki полезна — рекомендую:
1. Прочитать [00-quick-reference.md](00-quick-reference.md) и [12-system-prompts.md](12-system-prompts.md) — самое ценное.
2. Решить, какие файлы перенести в `swzhukov/llm_manifest/wiki/`.
3. Обновить `SKILL.md` (wiki-loader) — добавить ссылку на `/workspace/wiki/`.
4. Запустить `wiki-curator` для фиксации изменений.

Если wiki НЕ полезна — просто удали `/workspace/wiki/`, и я больше не буду её упоминать.
