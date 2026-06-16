# 08 — YandexGPT и OpenAI-совместимые модели

> Основано на уроке про подключение YandexGPT (в `040508f4`) + обсуждения про экономику и Yandex Cloud.

## 8.1 Зачем YandexGPT

- **Дёшевле**, чем OpenAI для русскоязычных задач (~0.1 ₽ за запрос).
- **Хорошо работает с русским** языком (YandexGPT обучен на русскоязычных данных).
- **OpenAI-совместимый API** — подключается к n8n через стандартную OpenAI-ноду.

## 8.2 Регистрация в Yandex Cloud

```
1. https://cloud.yandex.ru → зарегистрироваться
2. Создать «облако» (Cloud) — выбрать имя
3. Создать платёжный аккаунт (Billing) — даст грант 4 000 ₽ на 60 дней
4. ВАЖНО: привязать облако к платёжному аккаунту, иначе ключи не работают
```

⚠️ **Из урока (Георгий):** «Если потратили грант, можно создать второй платёжный аккаунт на другие данные — вам снова дадут 4 000 ₽. И так можно много раз. Но нужны новые карты и данные плательщика».

## 8.3 Создание сервисного аккаунта

```
1. Cloud Console → выбрать каталог (default)
2. Три точки → «Создать сервисный аккаунт»
3. Имя: например, "n8n-yandex"
4. Роли (ВАЖНО — добавь все нужные):
   - ai.foundationModels.user
   - ai.datasets.admin
   - ai.imageGeneration.user
   - ai.languageModels.user
   - ai.translate.user  (если нужен перевод)
5. Создать
```

## 8.4 Создание API-ключа

```
1. Открыть сервисный аккаунт
2. «Создать новый ключ» → API-ключ
3. Область действия: выбрать всё, что может понадобиться
4. Срок действия: НЕ ставить (по умолчанию бессрочный)
5. Скопировать ключ — больше не покажут!
```

⚠️ **Критично:** есть **API Key** (секрет) и **Account ID** (идентификатор аккаунта). Это **разные** вещи. Если перепутать — в ноде не будет видно список моделей, или будет ошибка авторизации.

## 8.5 Привязка облака к биллингу

⚠️ **Частая ошибка из чата:** «Создал облако, создал ключ, а YandexGPT не подключается».

Решение:
```
1. Cloud Console → иконка организации сверху
2. Billing → «Привязать облако» → выбрать нужное облако
3. Готово
```

## 8.6 Подключение к n8n (через OpenAI-совместимый endpoint)

```
Credentials → New → OpenAI
  API Key: <ваш YandexGPT API key>
  Base URL: https://llm.api.cloud.yandex.net/v1  ← YandexGPT endpoint

В workflow:
AI Agent → Chat Model → OpenAI
  Model: yandexgpt/latest  (или yandexgpt-lite/latest)
```

### Альтернативный endpoint

Для Yandex Cloud также есть Foundation Models API:
```
Base URL: https://llm.api.cloud.yandex.net/foundationModels/v1
```

## 8.7 Стоимость

| Модель | 1к токенов | Пример |
|---|---|---|
| YandexGPT Lite | ~0.04 ₽ | короткие ответы, классификация |
| YandexGPT Pro | ~0.30 ₽ | длинные, сложные ответы |
| YandexGPT 32k (Pro) | ~0.60 ₽ | контекст до 32к токенов |
| OpenAI GPT-4o | ~$5/1M input + $15/1M output | ($5 + $15 = ~₽1500) |
| OpenAI GPT-4o-mini | ~$0.15/1M input + $0.60/1M output | (~₽50) |

**Пример из урока:** «Привет, что ты за модель?» → ответ стоил **10 копеек**.

✅ **Best practice:** для русскоязычных ботов «в продакшн» — **YandexGPT Lite** (дёшево) или **Pro** (если нужно качество). Для английского / программирования — GPT-4o-mini.

## 8.8 Подключение ElevenLabs (голос)

Из чата (декабрь 2025): пользователи пробуют ElevenLabs для синтеза речи.

```
Credentials → ElevenLabs API
  API Key: sk_...

HTTP Request
  POST https://api.elevenlabs.io/v1/text-to-speech/<voice_id>
  Headers: { "xi-api-key": "sk_...", "Content-Type": "application/json" }
  Body: { "text": "...", "model_id": "eleven_multilingual_v2" }
```

Возвращает **mp3** как binary → можно отправить в Telegram через `sendVoice`.

## 8.9 Embeddings (для RAG)

YandexGPT имеет отдельную модель для эмбеддингов:

```
Model: embeddings/latest
Dimension: 256  (меньше, чем у OpenAI 1536)
```

⚠️ **Изменение схемы:** если используешь Yandex embeddings, таблица `documents` должна быть `vector(256)`, а не `vector(1536)`.

## 8.10 Альтернативы через OpenRouter

Из чата (`342d8f51`, февраль 2026): некоторые используют OpenRouter как агрегатор.

```
Base URL: https://openrouter.ai/api/v1
API Key: <openrouter key>
Model: anthropic/claude-3.5-sonnet, openai/gpt-4o, etc.
```

⚠️ **Из чата:** «This service is receiving too many requests from you» — OpenRouter ставит rate-limiter, и при частых запросах даёт временный бан 2–5 минут. Это не баг, это защита.

## 8.11 Рекомендации

| Задача | Модель | Почему |
|---|---|---|
| Русский чат-бот, простые ответы | YandexGPT Lite | дёшево, быстро |
| Русский RAG, фактология | YandexGPT Pro + temperature 0 | точность + русский |
| Код / английский | GPT-4o-mini или Claude 3.5 | лучше с кодом |
| Длинный контекст (>32к) | GPT-4o или YandexGPT 32k | зависит от бюджета |
| Embeddings для RAG | OpenAI text-embedding-3-small | проверено, дешево |
| Голос | ElevenLabs Multilingual v2 | лучшее качество |
