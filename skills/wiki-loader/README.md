# wiki-loader (Mavis skill)

Загружает контекст среды пользователя (VPS Beget, n8n, Flask, Telegram, YandexGPT) и базу ошибок из [github.com/swzhukov/llm_manifest](https://github.com/swzhukov/llm_manifest) в оперативную работу Mavis.

## Состав

- `SKILL.md` — основная инструкция (что, когда, как)
- `references/triggers.md` — таблица «триггер → какие секции wiki читать»

## Когда применяется

Триггер-ключевые слова: `n8n`, `workflow`, `Flask`, `Telegram-бот`, `YandexGPT`, `VPS`, `Beget`, `deploy`, `1С`, `inline keyboard`, `parse_mode`, `folder_id`, `daily cap`, `request/body must NOT have additional properties`, и т.д. (полный список — в `SKILL.md`).

## Где хранится source of truth

Этот скилл — **процедура применения**, не источник знаний. Источник:
- `wiki/AGENTS.md` — 4 принципа Карпатого
- `wiki/COUNCIL_RECOMMENDATIONS.md` — 10 принципов Совета
- `ENVIRONMENT.md` (72 KB) — proven паттерны среды
- `MISTAKES.md` (68 KB) — задокументированные грабли
- memory topics вроде `n8n-api-quirks` — узкие грабли по конкретному сервису

## Связь

- Применяется **перед** `wiki-curator` (загрузил → отработал → обновил)
- Для multi-file работ комбинируется с `gstack-team` (Phase 2 архитектура использует этот скилл)
