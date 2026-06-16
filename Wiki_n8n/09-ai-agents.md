# 09 — AI Agents

> Основано на уроках 8, 9 + 25 (RAG-бот) + 30 (Function Calling) + обсуждения в чате.

AI Agent — это нода, которая даёт LLM **возможность вызывать инструменты** (tools): читать базу, искать в Google, отправлять email. В отличие от простого Chat Model, агент сам решает, какой инструмент вызвать и в каком порядке.

## 9.1 Архитектура AI Agent

```
AI Agent
  ├─ Chat Model         — «мозги» (YandexGPT / OpenAI / Claude)
  ├─ System Message     — кто он, что умеет, как себя вести
  ├─ Memory             — помнит диалог (Window Buffer / Postgres)
  ├─ Tools              — что он может вызвать
  │     ├─ Supabase Vector Store (RAG)
  │     ├─ HTTP Request (внешний API)
  │     ├─ Calculator (math)
  │     ├─ Calculator Tool
  │     └─ Custom (Function)
  └─ Output Parser      — парсит финальный ответ (опционально)
```

## 9.2 Chat Model: как выбрать

| Требование | Рекомендация |
|---|---|
| Русский, дёшево | YandexGPT Lite |
| Русский, качественно | YandexGPT Pro |
| Код, английский, логика | GPT-4o / Claude 3.5 Sonnet |
| Бюджет = 0 | OpenRouter free-tier (риск: rate limit) |
| Function calling критично | GPT-4o / Claude — лучше всех |
| Длинный контекст (1М токенов) | Gemini 1.5 Pro |

✅ **Best practice из чата:** «Если бесплатные модели в роутере — повыбирайте другие. Не гарантируется работа».

## 9.3 Tools (инструменты) — главная сила агента

### Какие бывают

| Tool | Что делает |
|---|---|
| **Supabase Vector Store** | поиск по документам (RAG) |
| **HTTP Request Tool** | вызов произвольного REST API |
| **Calculator** | математика |
| **Custom Code Tool** | запустить JS/Python, вернуть результат |
| **Workflow Tool** | вызвать sub-workflow (Execute Workflow) |
| **Telegram Tool** | отправить сообщение через бота |
| **Google Calendar Tool** | работа с календарём |
| **Notion / Airtable / Slack** | готовые интеграции |

### Как сделать свой Tool (Function)

В ноде AI Agent → `Add Tool` → выбрать тип. Например, **HTTP Request Tool**:

```
Tool Name: get_weather
Description: "Получить текущую погоду в городе. Input: city (string)"
Method: GET
URL: https://api.weather.com/v1/current?city={{$json.city}}&key=...
```

Из урока 8: «В настройках инструмента есть своя моделька интеллекта. Обычно у вас она работает на GPT-4.1».

## 9.4 Temperature: главная настройка

Из урока 8:
> «Чем больше к единице, тем более творческий подход. Нам не нужна творческая мысль, потому что у нас чёткие данные, от которых нельзя отходить. Ставим **минимальное значение** температуры».

| Задача | Temperature | Почему |
|---|---|---|
| RAG-бот (фактология) | **0.0** | строго по документу |
| Техподдержка | 0.0–0.1 | короткие точные ответы |
| Копирайтинг (SEO) | 0.7–0.9 | нужно «творчество» |
| Перевод | 0.3 | баланс |
| Суммаризация | 0.2 | кратко, без выдумок |
| Brainstorm | 1.0 | максимум вариативности |

## 9.5 System Message: как написать

### Плохо

```
"Ты помощник. Отвечай на вопросы."
```

### Хорошо (из урока 8, бот-техподдержка)

```
Ты специалист технической поддержки компании "ГЭС Телеком".

Правила:
1. Отвечай строго на основе данных из Supabase Vector Store.
2. Если информации нет в базе — скажи "не знаю", не выдумывай.
3. Используй только официальные термины.
4. НЕ используй слова: "возможно", "наверное", "скорее всего".
5. Всегда ссылайся на конкретные лицензии / номера / даты.
6. Если вопрос выходит за рамки техподдержки — перенаправь на оператора.

Главный инструмент: support_tool (Supabase Vector Store).
При любом вопросе клиента СНАЧАЛА вызови support_tool, потом отвечай.
```

### Шаблон (из чата, SEO-копирайтер)

```markdown
You are an expert SEO content writer and subject-matter specialist.

INPUT:
- Russian title
- English title

TASK: Generate a fully written, long-form SEO article.

STRICT OUTPUT RULES (CRITICAL):
- Output ONLY the article text
- NO explanations, comments, notes, confirmations
- NO "this article", "below", "in this text", "here is"
- NO questions
- Output must start immediately with the article content

LANGUAGE:
- Entire output MUST be written ONLY in Russian
- No English words allowed

LENGTH: 2000-3000 words

CONTENT REQUIREMENTS:
- Deep and complete analysis
- Definitions, explanations, context, causes, consequences, applications, examples
- Expert level
- No filler, no repetition

STRUCTURE:
- H1 heading (Russian title)
- Multiple H2 sections
- H3, H4 where needed
- Bullet lists, numbered lists, tables (WordPress-compatible)

STYLE:
- Professional, authoritative
- Neutral expert tone
- No emojis
- No conversational filler

Generate the article now.
```

Полные примеры — [12-system-prompts.md](12-system-prompts.md).

## 9.6 Считаем токены и расходы

Из чата (февраль 2026):
> «Как просчитать токены, расходы на запросы и во сколько будет обходиться полный цикл? Где токены смотреть?»

### Где видно токены

| Способ | Где |
|---|---|
| **В UI Chat Model** | после каждого запуска — usage: input / output tokens |
| **В Execution** | в `data` ноды Chat Model |
| **Через API** | `GET /api/v1/executions/{id}` → поле `data.usageMetadata` |
| **Через community-ноду** | `Vlad-Loop/n8n-nodes-token-usage` |

Из чата (Георгий): «Токены показывает нода мозгов у агента, но эти данные **не передаются дальше**. Их надо вытягивать через ноду API n8n или воспользоваться community-нодой https://github.com/Vlad-Loop/n8n-nodes-token-usage».

### Формула стоимости

```
Стоимость = (input_tokens × $input_price + output_tokens × $output_price) / 1_000_000
```

Пример для GPT-4o-mini:
- input: 1000 токенов × $0.15/1M = $0.00015
- output: 500 токенов × $0.60/1M = $0.0003
- итого: $0.00045 ≈ 0.04 ₽

## 9.7 Анти-паттерны AI Agent

❌ **Слишком много Tools** (>10) — модель путается, какую вызвать.
❌ **Temperature = 1** для фактологии — галлюцинации.
❌ **Один гигантский System Message** на 5 страниц — модель «тонет», лучше модульно.
❌ **Memory не настроена** — бот «забывает» между сообщениями.
❌ **Нет fallback** при ошибке Tool — один сбой = весь workflow упал.
❌ **Production на free-tier моделях** — будут rate limits.

## 9.8 Продвинутый паттерн: Router Agent

Один агент разбирает запрос и **сам решает**, какому sub-агенту передать:

```
Router Agent
  ├─ Tool: "faq_agent" (RAG по документации)
  ├─ Tool: "order_agent" (запрос к CRM)
  └─ Tool: "human_handoff" (позвать живого оператора)
```

Это сложнее, но даёт **масштабируемость** — каждый sub-agent со своей памятью и инструментами.

## 9.9 Чек-лист перед прод-деплоем AI-агента

- [ ] System Message явно говорит, что делать при отсутствии данных
- [ ] Temperature соответствует задаче (0 для фактологии)
- [ ] Memory настроена (Window Buffer или Postgres)
- [ ] Tools описаны понятно для LLM (Description, не «Call API»)
- [ ] Error workflow подключён
- [ ] Rate-limit / cost cap учтены
- [ ] Тест на «галлюцинации»: бот не выдумывает несуществующие тарифы
- [ ] Логи токенов пишутся в БД (для аудита)
