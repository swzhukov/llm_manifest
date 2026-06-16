# YouTube → Google Sheets pipeline

> **Источники:** `raw_imports/01_DS_Дипсик и его трепыхания.md` (2026-06-09), `raw_imports/03_DS_Помощь с решением задачи.md` (2026-06-08), `raw_imports/36_QW_YouTube to Google Sheets transcription tool.md` (2026-06-08, 48 сообщений).

---

## Цель

Colab-скрипт (Python), который:
1. Принимает URL видео или канала на YouTube.
2. Собирает **метаданные** видео (название, описание, длительность, просмотры, теги, дата).
3. Скачивает **субтитры** (русские → английские → авто).
4. Если субтитров нет — **транскрибирует аудио** через Newton CLI.
5. Собирает **комментарии** (до 50).
6. Записывает всё в **Google Sheets** (отдельный лист на каждое видео).

---

## Стек

| Компонент | Решение |
|-----------|---------|
| **Среда** | Google Colab |
| **YouTube метаданные + комментарии** | YouTube Data API v3 (`google-api-python-client`) |
| **Субтитры** | `youtube-transcript-api` v1.x (экземпляр → `.list()` → `find_transcript` / `find_generated_transcript`) |
| **Fallback на транскрибацию** | `yt-dlp` + `ffmpeg` + `newton transcribe -e diarize` |
| **Запись в Sheets** | `gspread` + Google Auth |
| **Кэш** | `/content/cache/` (до 5 ГБ, LRU) |

---

## Ключевые технические находки

### 1. Обход блокировок YouTube
**Проблема:** YouTube блокирует запросы с IP-адресов облачных провайдеров (GCP, AWS, Azure).

**Решение:** `yt-dlp` с флагом `--extractor-args youtube:player_client=web` (обход Precondition check).

### 2. НЕ использовать cookies
**Сергей отказался от cookies** (стандартный обходной путь): «я думаю, что куки - опасная вещь, могут заблокировать. мне это нельзя допустить».

**Используемый подход:** `yt-dlp --extractor-args youtube:player_client=web` без cookies.

### 3. youtube-transcript-api v1.x (новый API)
- **v0.x (старая):** модульные вызовы `YouTubeTranscriptApi.get_transcript(...)`
- **v1.x (новая):** создаём **экземпляр** через `ytt = YouTubeTranscriptApi()`, затем `ytt.list(video_id)`, `tlist.find_manually_created_transcript(['ru'])`, `t.fetch()`

**Каскадный fallback** в `get_subtitles()`:
1. ru manual
2. ru auto
3. en auto
4. любой доступный

### 4. Newton CLI как fallback
- Установка: `curl -sL https://gitlab.com/fadeyev1/newton-cli/-/raw/main/newton -o /usr/local/bin/newton && chmod +x /usr/local/bin/newton`
- Скачивание аудио: `yt-dlp -f bestaudio -x --audio-format wav --audio-quality 0 -o {base} --no-playlist --extractor-args youtube:player_client=web {url}`
- Конвертация: `ffmpeg -y -i {raw} -ac 1 -ar 16000 -sample_fmt s16 {clean}`
- Транскрибация: `newton transcribe {clean} -o {out} -e diarize`
- Таймаут: NEWTON_TIMEOUT = 1800 сек, YDLP_TIMEOUT = 300 сек

---

## Структура Google Sheets

### Лист «Видео» (сводка)
| Video ID | URL | Название | Канал | Дата | Длит(с) | Просмотры | Теги | Язык субтитров | Сегментов | Комментариев | Статус |

### Листы «S_{video_id}» (субтитры)
| # | Старт (сек) | Длит (сек) | Текст |

### Листы «C_{video_id}» (комментарии)
| # | Текст |

### Особенности
- **Кэш:** если лист уже создан (`already exists`) → очищаем и перезаписываем.
- **gspread лимит:** 5000 строк за раз → бьём на батчи по 4000.
- **Возобновление:** `resume_mode` ищет лист `safe_YYYYMMDD_*` за сегодня и дописывает в него.

---

## Конфигурация

```python
CACHE_DIR      = Path("/content/cache")
CACHE_DIR.mkdir(exist_ok=True)
MAX_CACHE_GB   = 5
MAX_TEXT_LEN   = 50000
MAX_DESC_LEN   = 1000
BATCH_SIZE     = 10
NEWTON_TIMEOUT = 1800
YDLP_TIMEOUT   = 300
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1Ixd3g6f3iOpMq01KuLDQW6cFPsF3d3Ef7RAndAQxgIw/edit"
NEWTON_BIN = "/usr/local/bin/newton"
```

**Секреты (через `google.colab.userdata`):**
- `YOUTUBE_API_KEY` — обязателен.
- `NEWTON_TOKEN` — опционален (если нет, fallback на субтитры не сработает).

---

## История версий (по чатам)

### v1 (`01_DS_Дипсик и его трепыхания`)
- Работает с v1.x API
- Один лист «Видео» + листы «S_{id}» + «C_{id}»
- **БЕЗ Newton fallback** — только субтитры
- **Проблема:** субтитры для видео «Владимир Харин. Инвентаризация доработок 1С» — `disabled` (YouTube блокирует IP Colab)

### v2 (`03_DS_Помощь с решением задачи`)
- Та же архитектура
- **Добавлен Newton CLI как fallback**
- **Кэширование** на диск
- **Retry decorator** с exponential backoff
- **Возобновление** через `resume_mode`
- **Длинный код, ~600 строк**

### v3 (`36_QW_YouTube to Google Sheets transcription tool`)
- 48 сообщений в чате — самая длинная итерация
- Похоже, что-то ещё доработано (не читал в деталях)

---

## Конкретный кейс из чата

**Видео:** «Владимир Харин. Инвентаризация доработок 1С перед большим обновлением» (`uG68Db4Nv-I`)

**Результат v1:**
```
🎬 Видео: uG68Db4Nv-I
============================================================
▶ uG68Db4Nv-I
  📋 Владимир Харин. Инвентаризация доработок 1С перед большим обновлением
  ⚠️ Субтитры: disabled: YouTube is blocking requests from your IP
  💬 Комментарии: 0
============================================================
✅ Готово!
```

**Урок:** на Colab без cookies YouTube блокирует. Newton CLI может обойти (через `yt-dlp` + `ffmpeg`).

---

## Что НЕ сделано (потенциал)

- **Параллельная обработка** видео в канале (сейчас последовательная).
- **YouTube Shorts** фильтрация (есть в других проектах, тут не упомянуто).
- **Суммаризация видео** через LLM (по транскрипту).
- **Sentiment analysis** комментариев.
- **Перевод субтитров** на другие языки.
- **Интеграция с инвестиционным агентом** — этот pipeline мог бы быть Workflow 4B (YouTube-мониторинг), но в `05_DS` он описан упрощённо.

---

## Оценка Mavis

**Зрелость:** средняя. Работает, но есть что улучшать.

**Главные достижения Сергея:**
- Сам нашёл `player_client=web` обход блокировок.
- Отказался от cookies (зрелое решение, хоть и с trade-off).
- Сам нашёл, что youtube-transcript-api v1.x требует экземпляр.

**Главные риски:**
- YouTube может в любой момент ужесточить блокировки → `player_client=web` перестанет работать.
- Colab **перезапускает VM** → кэш пропадает.
- Google Sheets API имеет квоты (300 запросов/мин на проект).

**Что я бы рекомендовал (если бы Сергей спросил):**
- **Перенести из Colab на свой сервер** (Beget) — там нет лимита на время сессии.
- **Использовать yt-dlp как primary, а не fallback** — он надёжнее youtube-transcript-api для русских видео.
- **Добавить LLM-суммаризацию** — это добавит ценности, иначе просто транскрипты без анализа.
