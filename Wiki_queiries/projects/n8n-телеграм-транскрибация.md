# n8n Telegram-бот транскрибации медиа

> **Источник:** `raw_imports/08_DS_Повтор контекста приключений.md` (2026-05-28, 12 сообщений).
> **См. также:** [`../companies/other.md`](../companies/other.md) (хостинг)

---

## Цель

Telegram-бот, который принимает от пользователя:
- Голосовые сообщения
- Аудиофайлы
- Видеофайлы
- Документы (с аудио)
- Ссылки на YouTube/другие

И возвращает **транскрипцию** (текст) с диаризацией (разделение по спикерам).

---

## Стек

| Компонент | Решение |
|-----------|---------|
| **Telegram-бот** | Telegram Trigger |
| **Workflow automation** | n8n self-hosted на Beget |
| **ASR-движок** | Newton CLI (GigaAM v3, русский) + диаризация |
| **API-обёртка** | newton-api.py (Python, на :8080) |
| **Хранилище** | `/opt/newton-tmp/` на сервере |

---

## Сервер

- **Хост:** `root@wxvwmvycks:/opt/beget/n8n` (Beget VPS)
- **n8n:** self-hosted
- **Путь к Newton API:** `/opt/beget/n8n/newton-api.py`
- **Порт:** `:8080`
- **Проверка работы:** `curl -s -X POST http://127.0.0.1:8080/transcribe -H "Content-Type: application/json" -d '{"file": "1.mp3"}'`

---

## Workflow (n8n JSON, рабочий)

Сергей сам прислал **полностью валидный JSON** этого workflow. Вот его узлы:

1. **Telegram Trigger** — `updates: ["message"]`
2. **Code: Normalize Input** — JavaScript, нормализует вход (voice/audio/video/document/url)
3. **Switch: Input Type** — на 3 ветки (media / url / unsupported)
4. **Telegram: Get File** — скачивает файл из Telegram
5. **Write Media to Disk** — сохраняет в `/opt/newton-tmp/tg_input_{timestamp}.bin`
6. **Newton Transcribe Local** — `newton transcribe $INFILE --diarization`
7. **Newton Transcribe URL** — `newton transcribe {url} --diarization`
8. **Code: Parse OUTFILE** — парсит `OUTFILE=...` из stdout
9. **Read Transcript File** — читает результат
10. **Telegram: Send Document** — отправляет файл транскрипта
11. **Telegram: Send Error** — отправляет сообщение об ошибке (для unsupported)

См. полный JSON в `raw_imports/08_DS_Повтор контекста приключений.md`.

---

## Проблема, которую Сергей решил (важно!)

**Первый workflow, который прислал LLM, НЕ загружался** в n8n:
> «Problem running workflow. Unrecognized node type: n8n-nodes-base.executeCommand»

**Причина:** на версии n8n Сергея **нет ноды `executeCommand`**.

**Симптом:** «загрузилось, но остались одни узлы без параметров, без связей, без типа даже, кажется».

**Решение:** Сергей нашёл **рабочий JSON** в другом чате (видимо, свой предыдущий workflow), где `executeCommand` присутствует, и попросил LLM «сформулировать задачу, для которой ты составлял json». То есть по сути — **валидировать архитектуру через собственный успешный пример**.

**Извлечённый урок:** версия n8n на сервере критична. Не все ноды, которые генерирует LLM, доступны. Нужно **заранее знать**, какие nodes есть.

---

## Newton API

### Newton CLI
- Путь: `/usr/local/bin/newton`
- Проверка: `newton version`
- Команда: `newton transcribe {file} --diarization -e v3 -o {output}`
- Токен: переменная окружения `NEWTON_TOKEN`

### Newton API (обёртка)
- Python-скрипт: `newton-api.py`
- Запуск: `nohup python3 newton-api.py > /tmp/newton-api.log 2>&1 &`
- Endpoint: `POST http://127.0.0.1:8080/transcribe` с JSON `{"file": "1.mp3"}`

### Тест
```bash
export NEWTON_TOKEN="r-Tt-qYR9-IGhqW7Saaao46V0o8aV9LCVRHmn1-LNQU"
newton transcribe 1.mp3 -e v3 -o /tmp/test_out.txt
# READY 100% 82%
# Результат сохранён: /tmp/test_out.txt
```

Работает. API-обёртка — тоже (после `nohup` запуска и проверки `ss -tlnp | grep 8080`).

---

## Статус (на 2026-05-28)

- ✅ Newton API работает
- ✅ Telegram Trigger работает
- ✅ Рабочий JSON workflow на руках
- ❓ **Загружен ли в n8n и протестирован end-to-end** — **неизвестно**

---

## Что НЕ сделано / что может быть нужно

- **End-to-end тест:** отправить голосовое в бот → получить транскрипцию
- **Обработка ошибок:** что если Newton API упадёт? Что если файл больше X?
- **Ограничение размера файлов** (Telegram Bot API имеет лимит 20 МБ на скачивание)
- **YouTube ссылки** — отдельная ветка workflow (есть в JSON, но не тестировалась)
- **Модерация** — никто не проверяет, что бот делает с чужими голосовыми

---

## Связь с другими проектами

- **«Подготовка экспорта из TG для LLM»** (QW 2026-05-20, 101 сообщение) — вероятно, для обработки больших Telegram-экспортов, не для бота.
- **«YouTube → Google Sheets»** — другой проект, см. `../projects/youtube-sheets-pipeline.md`.

---

## Оценка Mavis

**Состояние:** 80% готово. JSON на руках, API работает, осталось end-to-end тестирование.

**Главный риск:** нода `executeCommand` в n8n может быть deprecated в будущих версиях → мигрировать на Code node или HTTP Request.

**Что я бы рекомендовал (если бы Сергей спросил):**
- **Сделать end-to-end тест** с реальным голосовым.
- **Добавить обработку ошибок:** если Newton API упал → отправить пользователю «обработка не удалась, попробуйте позже».
- **Зафиксировать версию n8n** в документации workflow (чтобы не повторять ошибку с неподдерживаемыми нодами).
- **Подумать про ограничения:** 20 МБ на файл, 50 МБ на отправку, таймауты Newton (NEWTON_TIMEOUT = 1800 сек в похожем проекте).
