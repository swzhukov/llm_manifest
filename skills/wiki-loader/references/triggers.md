# Triggers → Context map (wiki-loader)

Этот файл — быстрый справочник: **триггер-слово из запроса пользователя → какие секции wiki/ENVIRONMENT/MISTAKES читать**.

Используй его как **предварительный фильтр**, чтобы не тянуть в контекст 140 KB текста.

## VPS / инфраструктура

| Триггер | Секции |
|---|---|
| VPS, Beget, ssh, ForceCommand, deploy, деплой | `ENVIRONMENT §0, §3` |
| docker, контейнер, systemd | `ENVIRONMENT §3.4` |
| .env, секреты, env, secret | `ENVIRONMENT §2.6` |
| pkill, kill -9, restart сервиса | `ENVIRONMENT §3.5`, `MISTAKES §2.5-2.6` |

## n8n (workflows)

| Триггер | Секции |
|---|---|
| n8n, workflow, HTTP Request, Webhook | `ENVIRONMENT §4`, `MISTAKES §3` |
| Telegram Trigger, Telegram node | `MISTAKES §3.3, §3.13`, `ENVIRONMENT §4.3` |
| IF-каскад, Switch, expression | `ENVIRONMENT §4.5`, `MISTAKES §3.8` |
| inline button, reply_markup, callback | `ENVIRONMENT §4.7`, `MISTAKES §9.1` |
| PUT workflow, /activate, credentials | `MISTAKES §3.1-3.2, §3.13`, **memory: `n8n-api-quirks`** |

## Flask / Python / state

| Триггер | Секции |
|---|---|
| Flask, newton-api, endpoint, route | `ENVIRONMENT §5` |
| state.json, state_store, persistence | `ENVIRONMENT §8` |
| deadlock, lock, threading | `MISTAKES §5.2` |
| pytest, тесты, тестирование | `ENVIRONMENT §10`, `MISTAKES §10` |

## Telegram

| Триггер | Секции |
|---|---|
| Telegram-бот, бот упал, bot, Bot Menu | `ENVIRONMENT §7`, `MISTAKES §7` |
| callback_data, inline keyboard | `ENVIRONMENT §7.2`, `MISTAKES §7.2-7.3` |
| parse_mode, markdown в боте | `ENVIRONMENT §7.3`, `MISTAKES §7.1` |
| setWebhook, allowed_updates | `ENVIRONMENT §7.4`, `MISTAKES §7.5` |

## YandexGPT

| Триггер | Секции |
|---|---|
| YandexGPT, Yandex, folder_id, IAM | `ENVIRONMENT §6`, `MISTAKES §6.1-6.2` |
| daily cap, лимит токенов | `ENVIRONMENT §6.4`, `MISTAKES §6.6` |
| ответ пришёл как json блок | `MISTAKES §6.4` |

## 1С

| Триггер | Секции |
|---|---|
| 1С, 1C, HTTP-сервис, обмен с 1С | `ENVIRONMENT §1.3` (если есть паттерны), `wiki/topics/loop-engineering.md` |
| регистры, проведение документов | спрашивать пользователя (нет в wiki) |

## Process / orchestration

| Триггер | Секции |
|---|---|
| team plan, spawn verifier | `MISTAKES §11.1` |
| ничего не работает, всё упало | `MISTAKES §11.5, §11.8` |
| memory topics, persistent memory | `MISTAKES §11.4`, `ENVIRONMENT §9.4` |

## Методология (не про среду, а про LLM)

| Триггер | Секции |
|---|---|
| Karpathy, 4 принципа, agentic | `wiki/AGENTS.md`, `wiki/topics/from-vibe-to-agentic.md` |
| Council, 10 принципов, 5 сценариев | `wiki/COUNCIL_RECOMMENDATIONS.md` |
| LLM Wiki, контекстная инженерия | `wiki/topics/markdown-knowledge-base.md`, `wiki/topics/context-engineering.md` |
| Loop, Maker-Checker, цикл обратной связи | `wiki/topics/loop-engineering.md` |

## Как использовать

1. Юзер пишет запрос
2. Найди триггер-слово в этой таблице
3. Прочитай **только** указанные секции (не весь 140 KB файл)
4. Дай ответ со ссылками `[ENVIRONMENT §X.Y]` / `[MISTAKES §X.Y]`
5. Если в ячейке **memory:** — читай через `memory_topic_read()` (а не файл)
