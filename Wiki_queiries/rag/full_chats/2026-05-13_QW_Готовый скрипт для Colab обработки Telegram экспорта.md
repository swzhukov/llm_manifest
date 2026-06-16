# Готовый скрипт для Colab обработки Telegram экспорта

Source: QW | Date: 2026-05-13 | Fragments: 2 | ID: 88c1ebcd-45a5-40fa-8c97-8f810ebbbecb

---

## USER

Ты — эксперт по Python, Google Colab, обработке данных и интеграции с API (в частности Newton CLI для транскрибации).  
Я дам тебе полное описание задачи, цели, конфигурации и всех подводных камней, с которыми мы столкнулись.  
Твоя задача — написать **оптимальный, полностью готовый к запуску Python-скрипт для одной ячейки Colab**, который решает эту задачу.  
Но перед этим — **подумай о возможных вариантах решения**, предложи лучшие практики и, если видишь более эффективный подход, используй его.

---

## 🎯 ЦЕЛЬ СКРИПТА
Преобразовать экспортированный чат Telegram Desktop (ZIP-архив) в единый самодостаточный Markdown-документ, пригодный для глубокого анализа современными LLM, и попутно создать CSV-таблицу для аналитики.

Скрипт должен уметь:
- извлекать все текстовые сообщения с метаданными (дата, автор, ID);
- **транскрибировать** аудио, видео, голосовые сообщения и анимации со звуком через Newton CLI;
- **извлекать текст** из офисных документов (PPTX, DOCX, PDF, XLSX) и текстовых файлов;
- **распознавать текст** с фотографий и стикеров (OCR);
- формировать структурированный Markdown с полным контекстом каждого сообщения;
- если объём превышает заданный порог — разбивать на тома;
- выгружать результат в `/content/llm_output` и автоматически скачивать.

---

## 📦 КОНФИГУРАЦИОННЫЕ ПЕРЕМЕННЫЕ (задаются в начале скрипта)
| Переменная | Описание |
|------------|----------|
| `NEWTON_TOKEN` | токен Newton CLI |
| `LOCAL_EXPORT_DIR` | если указан, используется локальный путь/ZIP вместо диалога загрузки |
| `AUTO_ARCHIVE_NAME` | имя ZIP в `/content/export_uploaded/` для автовыбора без запроса |
| `MAX_FILE_SIZE_MB` | максимальный размер одного Markdown-тома (по умолчанию 25) |
| `NEWTON_ENGINE` | движок Newton (по умолчанию "v3") |
| `OUTPUT_DIR` | папка для результатов (`/content/llm_output`) |
| `EXPECTED_MEDIA_FILE` | для отладки: имя файла, обязательное для проверки целостности экспорта |
| `ENABLE_OCR` | включать ли OCR для изображений (по умолчанию True) |
| `OCR_LANG` | языки Tesseract (например `"rus+eng"`) |

---

## 📥 ВХОДНЫЕ ДАННЫЕ И ВЫБОР АРХИВА
- Пользователь может загрузить ZIP через `files.upload()` в Colab.
- Если в `/content/export_uploaded/` уже есть `.zip` файлы, скрипт выводит их список и предлагает выбор (номер или загрузка нового).
- Поддерживается как ZIP, так и распакованная папка.
- Автоматический выбор по `AUTO_ARCHIVE_NAME` без запроса.

---

## 🗂 СТРУКТУРА ЭКСПОРТА (ВАЖНО!)
В корне архива/папки рекурсивно ищется `result.json`.  
Медиа-файлы лежат в подпапках: `photos`, `videos` (или `video_files`), `files`, `voice_messages`, `stickers`, `animations` и т.п.

**Формат сообщения в JSON (актуальный для Telegram Desktop 2024+):**
- Поле `type` == `"message"`.
- `date`, `date_unixtime` (может быть строкой или числом).
- `from`, `from_id` (автор).
- `text` — строка или список объектов (нужно склеить все `text`-поля вложенных объектов).
- **Медиа** задаётся через два поля:
  - `media_type` — строка: `"photo"`, `"video"`, `"audio"`, `"voice_message"`, `"document"`, `"sticker"`, `"animation"`, `"audio_file"`, `"video_file"` и т.д.
  - `file` — строка с относительным путём к файлу.
- **Старый формат** (устаревший) мог использовать отдельные ключи `photo`, `video`, `document` и т.п. — скрипт должен поддерживать оба варианта.
- Игнорируем строки, начинающиеся с `(File not included...`.

**Наш реальный опыт:** в одном и том же дампе могут быть как старый, так и новый формат. Также тип `"audio_file"` используется для прикреплённых аудиофайлов (не голосовых), и его обязательно нужно транскрибировать, если есть аудиодорожка.

---

## ⚙️ ОБРАБОТКА МЕДИА И ИЗВЛЕЧЕНИЕ СОДЕРЖИМОГО

### 1. Транскрибация (Newton CLI)
Установка:
```bash
!curl -sL https://gitlab.com/fadeyev1/newton-cli/-/raw/main/newton -o /usr/local/bin/newton
!chmod +x /usr/local/bin/newton
Передача токена: через os.environ["NEWTON_TOKEN"], os.environ["NEWTON_API_KEY"] и newton config set token.

Проверка здоровья: newton health.

Алгоритм для аудио/видео/голосовых/анимаций:

Проверить наличие аудиопотока через ffprobe. Если нет — вернуть [нет аудиодорожки] и не вызывать Newton.

Конвертировать в WAV 16 кГц моно:
ffmpeg -y -i <файл> -ac 1 -ar 16000 -sample_fmt s16 <врем.wav>

Выполнить из рабочей папки временной директории:
newton transcribe <врем.wav> --engine v3
⚠️ Важно: современный Newton CLI не поддерживает флаг --output-format txt и не выводит результат в stdout. Он создаёт файл audio_result.txt в рабочей директории. Поэтому нужно запускать команду с cwd=<tmpdir> и после выполнения прочитать os.path.join(tmpdir, "audio_result.txt").

Если файл существует и не пуст — использовать его содержимое как расшифровку.

Если результат — JSON (может содержать поле text или transcription), корректно извлечь текст.

Документы с аудио/видео-расширениями (.mp3, .wav, .ogg, .m4a, .flac, .opus, .mp4, .webm, .mkv, .avi, .mov и т.п.) — обрабатывать как аудио/видео, даже если media_type = "document" или "file".

2. Извлечение текста из офисных документов и PDF
Для media_type = "document" или "file" (но не аудио/видео):

PPTX: python-pptx, текст со всех слайдов + заметки, таблицы → Markdown.

DOCX: python-docx, абзацы + таблицы → Markdown.

PDF: сначала PyPDF2 + pdfplumber, если нет текста и ENABLE_OCR=True, конвертировать страницы в изображения (pdftoppm) и применить Tesseract.

XLSX: openpyxl, для каждого листа первые 100 строк → Markdown-таблица.

Текстовые форматы (.txt, .md, .csv, .json, .xml, .html) — прочитать как текст.

Извлечённое содержимое вставляется в Markdown после строки с упоминанием файла.

3. OCR изображений
Для media_type = "photo" или "sticker" (при ENABLE_OCR=True) использовать pytesseract с указанным языком. Результат добавляется как OCR:\n<текст>.

🔍 ПОИСК ФАЙЛОВ
Файлы ищутся гибко:

Сначала точное совпадение относительно корня распаковки.

Затем поиск по имени в стандартных папках: voice_messages, video_files, files, photos и т.д.

При необходимости — рекурсивный обход всей распакованной структуры.

Если файл не найден — предупреждение и пометка (файл отсутствует).

📄 ВЫХОДНЫЕ ДАННЫЕ
Markdown (telegram_export_<timestamp>.md). При превышении MAX_FILE_SIZE_MB разбивается на _part1, _part2…
Формат одного сообщения:

text
[ДД.ММ.ГГГГ ЧЧ:ММ:СС] Имя (ID: from_id)
текст сообщения
[media_type]: относительный_путь
расшифровка / извлечённый текст / описание
(пустая строка)
CSV (telegram_export_<timestamp>.csv) с колонками:
timestamp (ISO), from, from_id, text, media_type, media_file, media_description.

Все сообщения сортируются по date_unixtime (через safe_int()), затем по id.

🛡️ ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ И ОПЫТ
Код для одной ячейки Google Colab.

Зависимости: apt-get install -y ffmpeg p7zip-full tesseract-ocr tesseract-ocr-rus poppler-utils, pip install tqdm python-pptx python-docx PyPDF2 pdfplumber openpyxl pandas pytesseract Pillow.

Newton CLI устанавливается как показано выше.

Обработка ошибок: битый JSON, отсутствующий файл, сбой ffmpeg/Newton/Tesseract/парсинга документа — проблемное сообщение пропускается с предупреждением, скрипт продолжает.

Безопасное преобразование чисел: функция safe_int(val, default=0) -> int(float(val)).

Очистка временной папки в finally.

Логирование: количество найденных JSON, общее число сообщений, транскрибаций, OCR, извлечений документов, ошибок.

Отладка: если DEBUG_MODE=True, вывести все уникальные ключи сообщений и примеры медиа-полей.

SHOW_SAMPLE_TRANSCRIPTS=True покажет первые N расшифровок в консоли.

💡 ПОЖАЛУЙСТА, ПОДУМАЙ
Перед тем как писать код, предложи 2–3 альтернативных подхода или улучшений, которые могли бы сделать скрипт ещё лучше (например, использование асинхронности для транскрибации, другой OCR-движок, более умное разбиение на тома). Если твой вариант окажется объективно лучше — используй его.

Затем напиши готовый скрипт, который можно скопировать и запустить, с подробными комментариями на русском языке, учитывая все вышеуказанные требования и исправленные ошибки.

---

## AI

## Возможные улучшения (альтернативные подходы)

1. **Асинхронная / многопоточная обработка медиа**  
   Транскрибация через Newton CLI и OCR – самые затратные по времени этапы. Их можно выполнять параллельно, используя `concurrent.futures.ThreadPoolExecutor` (для вызовов ffmpeg/Newton) или `asyncio` (если Newton имел бы асинхронный API). Это сократило бы общее время в несколько раз, особенно для больших чатов.  
   *Почему не сделано в скрипте*: параллельные внешние процессы требуют аккуратного управления временными папками и могут превысить лимиты Colab. Для надёжности оставлена последовательная схема.

2. **EasyOCR вместо Tesseract**  
   EasyOCR (основан на глубоком обучении) часто точнее распознаёт русский текст на сложном фоне, но требует установки через `pip`, загрузки модели и заметного объёма памяти. В Colab с GPU это может быть оправдано.  
   *Решение*: используется Tesseract как более лёгкий и стабильный вариант; при желании его можно заменить на EasyOCR двумя строчками.

3. **Интеллектуальное разбиение на тома**  
   Вместо жёсткого ограничения размера файла можно разбивать по дням, неделям или авторам, добавляя оглавление. Это сделает документ удобнее для LLM.  
   *В скрипте* реализована простая схема с ограничением в мегабайтах, но код легко расширить.

---

# Готовый скрипт для Google Colab

```python
# ============================================================
#  Конфигурация (задайте значения перед запуском)
# ============================================================
NEWTON_TOKEN        = ""                # Токен Newton CLI
LOCAL_EXPORT_DIR    = None              # Локальный путь к ZIP/папке (если не нужна загрузка)
AUTO_ARCHIVE_NAME   = None              # Имя файла в /content/export_uploaded для автовыбора
MAX_FILE_SIZE_MB    = 25                # Максимальный размер одного Markdown-тома
NEWTON_ENGINE       = "v3"             # Движок Newton
OUTPUT_DIR          = "/content/llm_output"
EXPECTED_MEDIA_FILE = None              # Имя файла для проверки целостности (опционально)
ENABLE_OCR          = True
OCR_LANG            = "rus+eng"         # Языки Tesseract
DEBUG_MODE          = False             # Вывести все уникальные ключи сообщений и примеры медиа
SHOW_SAMPLE_TRANSCRIPTS = True          # Показать первые 3 расшифровки в консоли
SAMPLE_COUNT        = 3                 # Сколько расшифровок показать

# ============================================================
#  Установка системных и Python-зависимостей
# ============================================================
import sys, os, subprocess, json, shutil, zipfile, glob, tempfile, re, csv, time
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

print("⏳ Установка системных пакетов...")
!apt-get -qq update
!apt-get -qq install -y ffmpeg p7zip-full tesseract-ocr tesseract-ocr-rus poppler-utils > /dev/null

print("⏳ Установка Python-пакетов...")
!pip -q install tqdm python-pptx python-docx PyPDF2 pdfplumber openpyxl pandas pytesseract Pillow

# Newton CLI
!curl -sL https://gitlab.com/fadeyev1/newton-cli/-/raw/main/newton -o /usr/local/bin/newton
!chmod +x /usr/local/bin/newton

# Настройка Newton
os.environ["NEWTON_TOKEN"] = NEWTON_TOKEN
os.environ["NEWTON_API_KEY"] = NEWTON_TOKEN
!newton config set token {NEWTON_TOKEN} 2>/dev/null
print("✅ Зависимости установлены")

# Проверка Newton
try:
    result = subprocess.run(["newton", "health"], capture_output=True, text=True, timeout=10)
    print("Newton health:", result.stdout.strip())
except Exception as e:
    print("⚠️ Ошибка при проверке Newton:", e)

# ============================================================
#  Вспомогательные функции
# ============================================================
def safe_int(val, default=0):
    """Безопасное преобразование в int (может быть строка, float, int)."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def extract_text(msg):
    """Извлекает текст из поля 'text' (строка или список)."""
    t = msg.get("text")
    if isinstance(t, str):
        return t
    if isinstance(t, list):
        parts = []
        for item in t:
            if isinstance(item, dict):
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""

def clean_temp_dir(tmpdir):
    """Удаляет временную папку, если существует."""
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir, ignore_errors=True)

def run_ffprobe(file_path):
    """Проверяет наличие аудиопотоков через ffprobe. Возвращает True, если есть аудио."""
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", file_path]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=30).decode()
        return "audio" in out
    except Exception as e:
        print(f"⚠️ ffprobe ошибка для {file_path}: {e}")
        return False

def transcribe_with_newton(media_path):
    """
    Транскрибация аудио/видео через Newton CLI.
    Возвращает текст расшифровки или сообщение об ошибке.
    """
    tmpdir = tempfile.mkdtemp()
    wav_path = os.path.join(tmpdir, "audio.wav")
    try:
        # Конвертация в WAV 16 кГц mono
        subprocess.run([
            "ffmpeg", "-y", "-i", media_path,
            "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
            wav_path
        ], capture_output=True, check=True, timeout=120)

        # Запуск Newton в tmpdir (результат пишется в audio_result.txt)
        result = subprocess.run(
            ["newton", "transcribe", wav_path, "--engine", NEWTON_ENGINE],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=300
        )

        # Чтение результата из файла
        result_file = os.path.join(tmpdir, "audio_result.txt")
        if os.path.exists(result_file) and os.path.getsize(result_file) > 0:
            with open(result_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # Иногда Newton возвращает JSON с полем "text"
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
                elif isinstance(data, dict) and "transcription" in data:
                    return data["transcription"]
            except json.JSONDecodeError:
                pass
            return content

        # Если файл не создан – попробуем stdout (на случай старой версии)
        if result.stdout:
            return result.stdout.strip()

        return f"[нет результата Newton, код возврата {result.returncode}]"
    except subprocess.TimeoutExpired:
        return "[таймаут транскрибации]"
    except Exception as e:
        return f"[ошибка транскрибации: {e}]"
    finally:
        clean_temp_dir(tmpdir)

def extract_document_text(file_path):
    """Извлекает текст из офисных / PDF / текстовых файлов."""
    ext = Path(file_path).suffix.lower()
    try:
        if ext in [".txt", ".md", ".csv", ".json", ".xml", ".html"]:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()[:10000]  # Ограничим объём
        elif ext == ".pptx":
            from pptx import Presentation
            prs = Presentation(file_path)
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        texts.append(shape.text_frame.text)
                    if shape.has_table:
                        table = shape.table
                        rows = []
                        for row in table.rows:
                            cells = [cell.text for cell in row.cells]
                            rows.append(" | ".join(cells))
                        texts.append("\n".join(rows))
                if slide.has_notes_slide and 

---

