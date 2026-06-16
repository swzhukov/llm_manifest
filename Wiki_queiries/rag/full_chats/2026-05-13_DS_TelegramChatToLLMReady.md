# TelegramChatToLLMReady

Source: DS | Date: 2026-05-13 | Messages: 4 | ID: 8f89873e-73b9-49eb-b999-d9d261437205

---

## user

Ты — эксперт по Python, Google Colab, обработке данных и интеграции с LLM. Напиши полностью готовый к запуску Python-скрипт (одна ячейка), который преобразует экспорт чата Telegram Desktop в формат, максимально пригодный для анализа современными LLM (ChatGPT, Claude, Gemini, Perplexity Spaces).

## ЦЕЛЬ СКРИПТА
Автоматически извлечь всю информацию из экспортированного Telegram-чата и превратить её в единый самодостаточный Markdown-документ, который LLM может прочитать и понять без необходимости дополнительно загружать какие-либо файлы. Для этого скрипт должен:
- извлечь все текстовые сообщения,
- транскрибировать все аудио/видео/голосовые сообщения (через Newton CLI),
- извлечь текст из офисных документов (PPTX, DOCX, PDF, XLSX) и изображений (OCR),
- сформировать структурированный Markdown с полным контекстом каждого сообщения,
- попутно создать CSV-таблицу для аналитики.

## КОНФИГУРАЦИОННЫЕ ПЕРЕМЕННЫЕ (задаются в начале скрипта)
- `NEWTON_TOKEN = "r-Tt-qYR9-IGhqW7Saaao46V0o8aV9LCVRHmn1-LNQU"` — токен Newton CLI.
- `LOCAL_EXPORT_DIR = ""` — путь к локальной папке или ZIP (если не пусто, используется вместо диалога).
- `AUTO_ARCHIVE_NAME = ""` — точное имя ZIP в `/content/export_uploaded/` для автоматического выбора без запроса (например `"kOLYA.zip"`).
- `MAX_FILE_SIZE_MB = 25` — максимальный размер одного Markdown-тома.
- `NEWTON_ENGINE = "v3"` — движок транскрибации Newton.
- `OUTPUT_DIR = "/content/llm_output"` — папка для результатов.
- `EXPECTED_MEDIA_FILE = ""` — для отладки: имя файла (например `"tmobile-1738749812"`), который обязан присутствовать в экспорте; если не найден, скрипт завершается с ошибкой.
- `ENABLE_OCR = True` — включить ли OCR для изображений (требует `tesseract-ocr`, может быть медленно).
- `OCR_LANG = "rus+eng"` — языки для Tesseract.

## 1. ВХОДНЫЕ ДАННЫЕ И ВЫБОР АРХИВА
- Пользователь может загрузить ZIP-архив через `files.upload()` в Colab.
- Если в `/content/export_uploaded/` уже есть `.zip` файлы, скрипт выводит их список и предлагает выбрать номер (0 — загрузить новый). Выбранный или загруженный архив сохраняется в `/content/export_uploaded/` для будущих запусков.
- Если `LOCAL_EXPORT_DIR` не пуст, используется этот путь (поддерживается и ZIP, и распакованная папка).
- Если задана `AUTO_ARCHIVE_NAME`, скрипт без запроса берёт этот файл из `/content/export_uploaded/`, если он существует.

## 2. СТРУКТУРА ЭКСПОРТА TELEGRAM DESKTOP
- В корне архива/папки рекурсивный поиск `result.json`.
- Медиафайлы лежат в подпапках: `photos`, `videos`, `files`, `voice_messages`, `stickers`, `animations` и т.п.
- Сообщение в JSON — объект с полями `id`, `type` (только `"message"`), `date`, `date_unixtime` (может быть строкой или числом), `from`, `from_id`, `text` (строка или список объектов) и одно из полей медиа: `photo`, `video`, `document`, `sticker`, `animation`, `audio`, `voice_message`.
- `text` как список — склеить все строки и `text`-поля вложенных объектов.
- Медиаполе: может быть строкой (относительный путь) или объектом с ключом `file` (или `path`). Игнорировать строки, начинающиеся с `(File not included...`. Приоритет медиа: photo, video, document, sticker, animation, audio, voice_message.

## 3. ОБРАБОТКА МЕДИА И ИЗВЛЕЧЕНИЕ СОДЕРЖИМОГО

### 3.1. Транскрибация аудио/видео/голосовых/анимаций
- Установка Newton CLI:

---

## user

Ты — эксперт по Python, Google Colab, обработке данных и интеграции с LLM. Напиши полностью готовый к запуску Python-скрипт (одна ячейка), который преобразует экспорт чата Telegram Desktop в формат, максимально пригодный для анализа современными LLM (ChatGPT, Claude, Gemini, Perplexity Spaces).

## ЦЕЛЬ СКРИПТА
Автоматически извлечь всю информацию из экспортированного Telegram-чата и превратить её в единый самодостаточный Markdown-документ, который LLM может прочитать и понять без необходимости дополнительно загружать какие-либо файлы. Для этого скрипт должен:
- извлечь все текстовые сообщения,
- транскрибировать все аудио/видео/голосовые сообщения (через Newton CLI),
- извлечь текст из офисных документов (PPTX, DOCX, PDF, XLSX) и изображений (OCR),
- сформировать структурированный Markdown с полным контекстом каждого сообщения,
- попутно создать CSV-таблицу для аналитики.

## КОНФИГУРАЦИОННЫЕ ПЕРЕМЕННЫЕ (задаются в начале скрипта)
- `NEWTON_TOKEN = "r-Tt-qYR9-IGhqW7Saaao46V0o8aV9LCVRHmn1-LNQU"` — токен Newton CLI.
- `LOCAL_EXPORT_DIR = ""` — путь к локальной папке или ZIP (если не пусто, используется вместо диалога).
- `AUTO_ARCHIVE_NAME = ""` — точное имя ZIP в `/content/export_uploaded/` для автоматического выбора без запроса (например `"kOLYA.zip"`).
- `MAX_FILE_SIZE_MB = 25` — максимальный размер одного Markdown-тома.
- `NEWTON_ENGINE = "v3"` — движок транскрибации Newton.
- `OUTPUT_DIR = "/content/llm_output"` — папка для результатов.
- `EXPECTED_MEDIA_FILE = ""` — для отладки: имя файла (например `"tmobile-1738749812"`), который обязан присутствовать в экспорте; если не найден, скрипт завершается с ошибкой.
- `ENABLE_OCR = True` — включить ли OCR для изображений (требует `tesseract-ocr`, может быть медленно).
- `OCR_LANG = "rus+eng"` — языки для Tesseract.

## 1. ВХОДНЫЕ ДАННЫЕ И ВЫБОР АРХИВА
- Пользователь может загрузить ZIP-архив через `files.upload()` в Colab.
- Если в `/content/export_uploaded/` уже есть `.zip` файлы, скрипт выводит их список и предлагает выбрать номер (0 — загрузить новый). Выбранный или загруженный архив сохраняется в `/content/export_uploaded/` для будущих запусков.
- Если `LOCAL_EXPORT_DIR` не пуст, используется этот путь (поддерживается и ZIP, и распакованная папка).
- Если задана `AUTO_ARCHIVE_NAME`, скрипт без запроса берёт этот файл из `/content/export_uploaded/`, если он существует.

## 2. СТРУКТУРА ЭКСПОРТА TELEGRAM DESKTOP
- В корне архива/папки рекурсивный поиск `result.json`.
- Медиафайлы лежат в подпапках: `photos`, `videos`, `files`, `voice_messages`, `stickers`, `animations` и т.п.
- Сообщение в JSON — объект с полями `id`, `type` (только `"message"`), `date`, `date_unixtime` (может быть строкой или числом), `from`, `from_id`, `text` (строка или список объектов) и одно из полей медиа: `photo`, `video`, `document`, `sticker`, `animation`, `audio`, `voice_message`.
- `text` как список — склеить все строки и `text`-поля вложенных объектов.
- Медиаполе: может быть строкой (относительный путь) или объектом с ключом `file` (или `path`). Игнорировать строки, начинающиеся с `(File not included...`. Приоритет медиа: photo, video, document, sticker, animation, audio, voice_message.

## 3. ОБРАБОТКА МЕДИА И ИЗВЛЕЧЕНИЕ СОДЕРЖИМОГО

### 3.1. Транскрибация аудио/видео/голосовых/анимаций
- Установка Newton CLI:
!curl -sL https://gitlab.com/fadeyev1/newton-cli/-/raw/main/newton -o /usr/local/bin/newton
!chmod +x /usr/local/bin/newton

text
- Передать токен: через `os.environ["NEWTON_TOKEN"]`, `os.environ["NEWTON_API_KEY"]` и `newton config set token` (ошибки `config set` игнорировать).
- Проверить Newton: `newton health`.
- Для любого аудио/видео/голосового/анимации:
1. Конвертировать исходный файл в WAV 16 кГц моно через ffmpeg (временный файл в `tempfile.TemporaryDirectory()`).
2. Выполнить `newton transcribe <wav> --engine v3 --output-format txt`.
3. При успехе — использовать полученный текст. При ошибке — вставить `[тип_медиа]: имя_файла (ошибка транскрибации)` и залогировать ошибку.

- **Документы с аудио/видео-расширениями** (`.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.opus`, `.mp4`, `.webm`, `.mkv`, `.avi`, `.mov` и т.п.) переопределять как `audio`/`video` и транскрибировать аналогично.

### 3.2. Извлечение текста из офисных документов и PDF
Для документов (`document`), не попавших в аудио/видео, если расширение соответствует одному из поддерживаемых форматов, извлечь текст и вставить его в Markdown под упоминанием файла:

- **PPTX**: использовать `python-pptx`. Извлечь текст со всех слайдов (включая заметки). Если есть таблицы — преобразовать в Markdown-таблицы.
- **DOCX**: использовать `python-docx`. Извлечь весь текст (абзацы, таблицы). Таблицы — в Markdown.
- **PDF**: использовать `PyPDF2` (для текстовых PDF) или `pdfplumber`. Извлечь текст. Если текст не извлёкся (скан), при `ENABLE_OCR=True` конвертировать страницы в изображения и применить OCR.
- **XLSX**: использовать `openpyxl` или `pandas`. Для каждого листа создать Markdown-таблицу (первые N строк, например 100, чтобы не раздувать). Добавить имя листа.
- **Изображения (photo, sticker)** — если включён `ENABLE_OCR`, применить Tesseract OCR (`pytesseract`) к файлу и извлечь текст, добавив его в описание. Иначе просто `[photo]: filename`.

В Markdown после строки `[document]: filename` вставить блок с извлечённым содержимым, обрамлённый маркерами:
[document]: report.pptx
Содержимое файла (извлечено автоматически):
...
(текст/таблицы)

text

Если извлечение не удалось — написать `(не удалось извлечь содержимое)`.

### 3.3. Поиск файлов
Файлы ищутся по относительному пути из JSON: `os.path.normpath(os.path.join(extract_root, rel_path))`. Если файл не найден — выводится предупреждение и в Markdown пишется `(файл отсутствует)`.

## 4. ВЫХОДНЫЕ ДАННЫЕ
- Папка `/content/llm_output`.
- **Markdown-файлы**: `telegram_export_<timestamp>.md`. При превышении `MAX_FILE_SIZE_MB` разбивается на тома `_part1`, `_part2`… Формат одного сообщения:
[ДД.ММ.ГГГГ ЧЧ:ММ:СС] Имя (ID: from_id)
текст сообщения (если есть)
[media_type]: filename
<опционально — извлечённое содержимое>
(пустая строка)

text
Транскрибированный текст вставляется как `[voice_message]: расшифровка`.

- **CSV-файл**: `telegram_export_<timestamp>.csv` с колонками:
`timestamp` (ISO), `from`, `from_id`, `text`, `media_type`, `media_file`, `media_description`.
В `media_description` попадает либо расшифровка/извлечённый текст, либо описание ошибки, либо упоминание файла.

- Все сообщения сортируются по `date_unixtime` (безопасное преобразование через `int(float(...))`), затем по `id`.
- Файлы автоматически скачиваются через `files.download()` (только в Colab).
- Временная папка с распакованным экспортом удаляется в `finally`.

## 5. ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ
- Код для одной ячейки Google Colab.
- Установка зависимостей: `apt-get install -y ffmpeg p7zip-full tesseract-ocr tesseract-ocr-rus`, `pip install tqdm python-pptx python-docx PyPDF2 pdfplumber openpyxl pandas pytesseract Pillow`.
- Newton CLI устанавливается как описано выше.
- Использовать только стандартные библиотеки + перечисленные выше.
- Логирование: количество найденных JSON, общее число сообщений, транскрибация каждого файла (имя → результат), извлечение текста из документов (успех/ошибка), создание томов.
- **Обработка ошибок**: битый JSON, отсутствующий файл, сбой ffmpeg/Newton/Tesseract/парсинга документа — проблемное сообщение пропускается с предупреждением, скрипт продолжает работу.
- **Безопасное преобразование чисел**: функция `safe_int(val, default=0)` → `int(float(val))`, при ошибке `default`. Применять к `date_unixtime` и `id`.
- **Отладка**: если `EXPECTED_MEDIA_FILE` не пуст, после распаковки искать этот файл рекурсивно. Если не найден — `print` ошибки и `return`.
- Комментарии в коде краткие, на русском языке.
- Никаких пояснений вне кода. Выведи только готовый скрипт.

---

## user

Hit:1 https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/ InRelease
Hit:2 https://cli.github.com/packages stable InRelease
Hit:3 http://archive.ubuntu.com/ubuntu jammy InRelease
Hit:4 http://security.ubuntu.com/ubuntu jammy-security InRelease
Hit:5 http://archive.ubuntu.com/ubuntu jammy-updates InRelease
Hit:6 http://archive.ubuntu.com/ubuntu jammy-backports InRelease
Hit:7 https://r2u.stat.illinois.edu/ubuntu jammy InRelease
Hit:8 https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy InRelease
Hit:9 https://ppa.launchpadcontent.net/ubuntugis/ppa/ubuntu jammy InRelease
Reading package lists...
W: Skipping acquire of configured file 'main/source/Sources' as repository 'https://r2u.stat.illinois.edu/ubuntu jammy InRelease' does not seem to provide it (sources.list entry misspelt?)
Newton успешно настроен.
Найдены следующие архивы:
1. kOLYA (1).zip
2. kOLYA.zip
0. Загрузить новый архив
Выберите номер архива (или 0 для новой загрузки): 2
Найдено 1 файлов result.json
Найдено 275 сообщений
Создан файл: /content/llm_output/telegram_export_20260513_133017.md
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
/tmp/ipykernel_13012/3289687280.py in <cell line: 0>()
    474             f.write(markdown_content)
    475         print(f"Создан файл: {md_filename}")
--> 476         files.download(md_filename)
    477     else:
    478         # Разделение на части

AttributeError: 'list' object has no attribute 'download'


---

## user

нет-нет, дай полностью код. и ты же помнишь, что мне важны все файл, которые можно автоматически распознать и извлечь текст?

---

