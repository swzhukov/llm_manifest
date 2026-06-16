# 07 — Telegram-боты

> Основано на уроках 9–14 + 25 (RAG-бот) + 27 (голосовой ввод) курса + живые Q&A.

## 7.1 Создание бота

```
1. Открыть @BotFather в Telegram
2. /newbot → задать имя → задать username (должен заканчиваться на 'bot')
3. Скопировать TOKEN
4. В n8n: Credentials → New → Telegram API → вставить TOKEN
5. В workflow: Telegram Trigger (выбрать credentials)
```

⚠️ **Подводный камень:** username должен быть **глобально уникальным** и заканчиваться на `bot`. Если «already taken» — придумай другой.

## 7.2 Inline-кнопки и callback_data

### Паттерн: показать кнопки

```
Telegram Trigger
    ↓
Telegram → Send Message
  text: "Что хотите сделать?"
  reply_markup: {
    "inline_keyboard": [
      [{"text": "📦 Заказ", "callback_data": "order"}],
      [{"text": "📞 Контакты", "callback_data": "contacts"}]
    ]
  }
```

### Паттерн: обработать нажатие

```
Telegram Trigger (additionalFields: callback)
    ↓
Switch
  - order    → Send Message "Оформляем заказ..."
  - contacts → Send Message "Телефон: ..."
```

### ⚠️ Подводный камень: `callback_data` > 64 байт

Telegram обрезает `callback_data` до **64 байт**. Длинные строки приходят **пустыми** или с мусором.

✅ **Решение:** маппинг `короткий_код → длинное_значение` через Supabase:
```
callback_data: "ord_42"  # 7 байт
внутри → Supabase SELECT WHERE short_code = 'ord_42' → order_id = 42
```

Подробнее: см. [ENVIRONMENT.md §7.2 в репо swzhukov/llm_manifest].

## 7.3 Webhook vs Polling

| | Webhook (стандарт) | Polling (community) |
|---|---|---|
| Как работает | Telegram шлёт POST на наш URL | n8n сам спрашивает Telegram «есть новое?» |
| Требования | публичный HTTPS, домен | нет требований к домену |
| Когда не работает | n8n за NAT, localhost, нет SSL | всегда |
| Нода | Telegram Trigger (встроенная) | `@mentoster/n8n-nodes-telegram-polling` |
| Задержка | мгновенная | 1–3 сек (интервал опроса) |

Из чата (`671fdf61`):
> «Telegram Trigger + Send Message + DeepSeek — от телеги ответ не доходит до n8n. Бот верный, ключ добавил».

Решение от Патрика:
> «Проверь, какой у тебя адрес webhook в ноде. Когда запускаешь workflow, n8n отправляет в телегу, что на этот адрес нужно кидать сообщения. Соответственно, этот адрес **не должен быть локальным** и должен быть доступен извне».

✅ **Best practice:** для локальной разработки (n8n на `localhost:5678`) — используй **ngrok** или **community polling node**. Для прода — webhook через домен + Caddy (он уже в docker-стеке).

## 7.4 User-bot vs Bot API

| | Обычный бот (Bot API) | User-bot (Telegram Client API) |
|---|---|---|
| Что видит | только то, что ему прислали | все сообщения в чатах, где авторизован |
| Создаётся через | @BotFather | свой аккаунт (риск бана) |
| Может слушать сообщения в группе | только `/команды` и сообщения, где он есть | **все** сообщения |
| Когда использовать | 95% задач (бот-ассистент) | парсинг чатов, автоответы в группе |

Из чата:
> «Мне нужно подключить юзер бота, чтобы он слушал события, без обыкновенного бота»
> «Telegram Copilot не работает автоматизация... в каком уроке это?»

Ответ: в уроке 14 (Telegram — простая логика кнопок) + урок 9 (HTTP-запросы к Telegram API). User-bot требует **отдельной библиотеки** (например, `telethon` для Python) — это не встроенная нода n8n.

## 7.5 Голосовой ввод (транскрибация)

Из урока 27: «Голосовой ввод в Telegram. Как сделать транскрибацию».

```
Telegram Trigger
    ↓
IF (message.voice !== undefined)
    ├─ true  → Telegram → Get File (file_id из voice)
    │             ↓
    │         HTTP Request → скачать .ogg
    │             ↓
    │         HTTP Request → POST на Whisper API / Yandex SpeechKit
    │             ↓
    │         Получить text → передать в основной pipeline
    │
    └─ false → основной pipeline (текст)
```

### Альтернативы Whisper

- **OpenAI Whisper API** — $0.006/мин аудио, отличное качество
- **Yandex SpeechKit** — дешевле, хорошо для русского
- **ElevenLabs** — `ElevenLabs Speech to Text` (см. [08-yandex-gpt.md §8.6](08-yandex-gpt.md))
- **Local Whisper** — self-hosted, бесплатно, но жрёт CPU

Из чата (`0c07158d`, декабрь 2025): «Кто-нибудь пробовал настраивать транскрибацию аудио через ElevenLabs? Получил блок». → У некоторых провайдеров бывают баны по IP/VPN.

## 7.6 Анти-паттерны Telegram-ботов

❌ Inline-кнопка с `callback_data > 64 байт` (молча обрезается).
❌ Бот в группе пытается читать все сообщения через Bot API (нельзя).
❌ Webhook указывает на `http://localhost:5678/...` (извне не достучится).
❌ Бот пишет первым, не дождавшись `/start` (Telegram не доставит).
❌ Использовать Bot Token в URL — это секрет, только в headers.
❌ Один Bot Token на 2 разных сервиса (race conditions).
❌ Цитировать огромный JSON в `text:` (Telegram лимит 4096 символов на сообщение,MarkdownV2 ещё меньше).
❌ parse_mode=HTML без экранирования `<`/`>`/`&` (Telegram вернёт 400).

## 7.7 Memory для Telegram-бота: Window Buffer Memory

Самое частое — бот должен «помнить» о чём говорили.

```
AI Agent
  ├─ Chat Model
  ├─ System Message
  ├─ Memory: Window Buffer Memory
  │     - Session ID: {{$json.message.chat.id}}
  │     - Context Window Length: 10  (последние 10 пар)
  └─ Tool: Supabase Vector Store
```

Окно в 10 пар = 20 сообщений. Если нужно больше — `Window Buffer Memory` не подходит, переходи на **Postgres Chat Memory** (бесконечная история).

⚠️ **Из урока 8:** «С прошлого занятия на нашем workflow добавился большой элемент, который позволит нам давать нашему боту векторные знания. Память + RAG = полноценный агент».

## 7.8 Отправка медиа-группы (альбом фото)

Из чата (октябрь 2025):
> «Хочу, чтобы в Telegram фото приходило в виде галереи, а не раскиданно по диалоговому окну. ИИ говорит, что есть Telegram-узел Media Group, но постоянно ошибка: то "все файлы должны иметь расширение .jpg", то "привязаны к бинарным файлам"».

**Рабочее решение (через HTTP Request к Telegram API):**

```javascript
// В Code-ноде перед отправкой
const items = $input.all();
const media = items.map(item => ({
  type: 'photo',
  media: item.binary.data  // attach://...
}));

return {
  chat_id: $('Telegram Trigger').item.json.message.chat.id,
  media: media
};
```

```
Code (формируем массив media)
    ↓
HTTP Request
  method: POST
  url: https://api.telegram.org/bot{{$env.TELEGRAM_BOT_TOKEN}}/sendMediaGroup
  body: { chat_id, media: [...photos] }
```

⚠️ Не пытайся решить через визуальную ноду `Send Media Group` — она капризная к формату. HTTP Request надёжнее.

## 7.9 Bot Menu (кнопка «Меню» внизу чата)

Отдельная тема — persistent-кнопка `/start` → показывает меню. Настраивается через `setMyCommands` (Telegram Bot API).

```
HTTP Request
  method: POST
  url: https://api.telegram.org/bot{{$env.TELEGRAM_BOT_TOKEN}}/setMyCommands
  body: {
    "commands": [
      {"command": "start", "description": "🚀 Начать"},
      {"command": "help", "description": "❓ Помощь"},
      {"command": "settings", "description": "⚙️ Настройки"}
    ]
  }
```

Запускается **один раз** при старте (или периодически, чтобы обновить).

Подробнее про bot menu — см. memory topic `telegram-bot-menu` (есть в агенте).

## 7.10 Long Polling как fallback

Если домен «глючит» с SSL или webhook не доходит — community-нода:

```
@mentoster/n8n-nodes-telegram-polling
```

Работает по long-polling: сама ходит в Telegram и забирает новые сообщения. Подходит для разработки и для случаев, когда webhook невозможен.

Из чата:
> «Альтернативу можешь использовать community-ноду @mentoster/n8n-nodes-telegram-polling. Она работает по принципу long-polling, с какой-то периодичностью шлёт запрос на сервер телеги и запрашивает "есть ли новые сообщения". В этом случае хост для вебхуков не нужен».
