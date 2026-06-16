# Telegram экспорт в LLM формат

Source: QW | Date: 2026-05-13 | Fragments: 2 | ID: addccfa8-d1de-4c33-b308-7b44c7a21bce

---

## USER

Напиши Python-скрипт для Google Colab (всё в одной ячейке), который преобразует экспорт чата Telegram Desktop в формат для LLM.

### 1. Входные данные
- Пользователь может загрузить ZIP-архив с экспортом через `files.upload()` в Google Colab.
- Если в `/content/export_uploaded/` уже есть `.zip` файлы, скрипт выводит их список и предлагает выбрать номер (0 — загрузить новый).
- Поддержка переменной `LOCAL_EXPORT_DIR`: если в начале скрипта задана непустая строка с путём к папке или ZIP, используется она.
- Если задана `AUTO_ARCHIVE_NAME` (точное имя файла), скрипт автоматически выбирает этот архив из `/content/export_uploaded/` без запроса.
- **Важно**: после загрузки нового ZIP он сохраняется в `/content/export_uploaded/` для будущих запусков.

### 2. Структура экспорта Telegram Desktop
- В корне архива/папки есть один или несколько `result.json`.
- Медиафайлы лежат в подпапках: `photos`, `videos`, `files`, `voice_messages`, `stickers`, `animations` и т.д.
- Формат сообщения в JSON: объект с полями `id`, `type` (учитываем только `"message"`), `date`, `date_unixtime` (строка или число), `from`, `from_id`, `text` (строка или список объектов) и одно из полей медиа: `photo`, `video`, `document`, `sticker`, `animation`, `audio`, `voice_message`.
- Поле `text` может быть списком: нужно склеить все строки и `text`-поля вложенных объектов.
- Медиаполе может быть строкой (путь к файлу) или объектом с ключом `file` (или `path`). Игнорируем строки, начинающиеся с `(File not included...`.
- Приоритет медиа: photo, video, document, sticker, animation, audio, voice_message.

### 3. Обработка медиа
- **Изображения, стикеры, документы** (кроме тех, что являются аудио/видео по расширению) — просто упоминаются в Markdown в формате `[тип_медиа]: имя_файла`.
- **Все аудио, голосовые сообщения, видео, анимации** должны быть транскрибированы через Newton CLI.
- Установка Newton CLI: `curl -sL https://gitlab.com/fadeyev1/newton-cli/-/raw/main/newton -o /usr/local/bin/newton && chmod +x /usr/local/bin/newton`.
- Токен Newton: `r-Tt-qYR9-IGhqW7Saaao46V0o8aV9LCVRHmn1-LNQU`. Передавать через `os.environ["NEWTON_TOKEN"]` и `os.environ["NEWTON_API_KEY"]`, а также через `newton config set token ...` (если поддерживается). Игнорировать ошибки `newton config`.
- Движок транскрибации: `v3` (задаётся переменной `NEWTON_ENGINE`).
- **Конвертация перед отправкой**: любой входной файл (mp3, mp4, ogg, webm и т.д.) конвертируется в WAV 16 кГц моно через ffmpeg. Временный WAV создаётся в `tempfile.TemporaryDirectory()`.
- Команда транскрибации: `newton transcribe <wav_file> --engine v3 --output-format txt`.
- Обработка ошибок транскрибации: при неудаче в Markdown вставляется `[тип_медиа]: имя_файла (ошибка транскрибации)`, в лог выводится подробное сообщение.
- **Документы**: если расширение файла входит в множество аудио- или видео-расширений (`.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.opus`, `.mp4`, `.webm`, `.mkv`, `.avi`, `.mov`, `.flv` и т.д.), он обрабатывается как аудио/видео и транскрибируется.
- **Важно**: скрипт должен корректно находить файлы внутри распакованной структуры по относительному пути из JSON. Использовать `os.path.normpath` и `os.path.isfile`.

### 4. Выходные данные
- Папка `/content/llm_output`.
- **Markdown-файлы**: `telegram_export_<timestamp>.md`. Если размер превышает `MAX_FILE_SIZE_MB` (по умолчанию 25 МБ), разбивается на тома `_part1`, `_part2` и т.д.
  Формат сообщения в Markdown:

---

## AI

```python
# ============================================================
# Конфигурация (можно менять перед запуском)
# ============================================================
LOCAL_EXPORT_DIR = ""          # путь к папке или ZIP-файлу с экспортом; если пусто – берём из /content/export_uploaded/
AUTO_ARCHIVE_NAME = ""         # точное имя архива в /content/export_uploaded/ для автоматического выбора
MAX_FILE_SIZE_MB = 25          # максимальный размер одного выходного .md в мегабайтах
NEWTON_ENGINE = "v3"           # движок Newton
NEWTON_TOKEN = "r-Tt-qYR9-IGhqW7Saaao46V0o8aV9LCVRHmn1-LNQU"

# ============================================================
# Установка зависимостей и Newton CLI
# ============================================================
import subprocess, sys, os, shutil, tempfile, json, zipfile, re, glob
from datetime import datetime
from pathlib import Path

# ffmpeg (обычно уже есть в Colab, но на всякий случай)
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
except:
    print("Устанавливаю ffmpeg...")
    subprocess.run(["apt-get", "update", "-qq"], check=False)
    subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], check=True)

# Newton CLI
if not os.path.exists("/usr/local/bin/newton"):
    print("Устанавливаю Newton CLI...")
    subprocess.run("curl -sL https://gitlab.com/fadeyev1/newton-cli/-/raw/main/newton -o /usr/local/bin/newton", shell=True, check=True)
    subprocess.run(["chmod", "+x", "/usr/local/bin/newton"], check=True)

# Пробуем установить токен через newton config (игнорируем ошибки)
subprocess.run(["newton", "config", "set", "token", NEWTON_TOKEN], capture_output=True)

# Переменные окружения
os.environ["NEWTON_TOKEN"] = NEWTON_TOKEN
os.environ["NEWTON_API_KEY"] = NEWTON_TOKEN

# ============================================================
# Вспомогательные функции
# ============================================================

def find_result_jsons(root_dir):
    """Найти все файлы result.json в дереве каталогов."""
    return list(Path(root_dir).rglob("result.json"))

def extract_text(text_field):
    """Склеить поле text (строка или список) в одну строку."""
    if text_field is None:
        return ""
    if isinstance(text_field, str):
        return text_field
    parts = []
    for item in text_field:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict) and "text" in item:
            parts.append(item["text"])
    return "".join(parts)

def get_media_info(msg):
    """
    Вернуть (media_type, relative_path) или (None, None).
    Приоритет: photo, video, document, sticker, animation, audio, voice_message.
    """
    for media_key in ["photo", "video", "document", "sticker", "animation", "audio", "voice_message"]:
        media_val = msg.get(media_key)
        if not media_val:
            continue
        # media_val может быть строкой или объектом с 'file' (или 'path')
        if isinstance(media_val, str):
            rel_path = media_val
        elif isinstance(media_val, dict):
            rel_path = media_val.get("file") or media_val.get("path") or ""
        else:
            continue
        if not rel_path or rel_path.startswith("(File not included"):
            continue
        return media_key, rel_path.strip()
    return None, None

def is_audio_video_by_ext(file_path):
    """Проверить, является ли файл аудио/видео по расширению."""
    AUDIO_VIDEO_EXT = {
        ".mp3", ".wav", ".ogg", ".m4a", ".flac", ".opus",
        ".mp4", ".webm", ".mkv", ".avi", ".mov", ".flv",
        ".mpeg", ".mpg", ".wmv", ".3gp", ".aac", ".oga"
    }
    return Path(file_path).suffix.lower() in AUDIO_VIDEO_EXT

def should_transcribe(media_type, file_path):
    """Нужна ли транскрибация для этого медиа."""
    # Все audio/video/voice/animation
    if media_type in ("video", "audio", "voice_message", "animation"):
        return True
    # Документы с аудио/видео расширением
    if media_type == "document" and is_audio_video_by_ext(file_path):
        return True
    return False

def transcribe_file(file_path, extract_dir):
    """
    Транскрибировать аудио/видео через Newton.
    Возвращает (transcript_text, error_message).
    """
    full_path = os.path.normpath(os.path.join(extract_dir, file_path))
    if not os.path.isfile(full_path):
        return None, f"Файл не найден: {full_path}"
    tmpdir = tempfile.TemporaryDirectory()
    try:
        wav_path = os.path.join(tmpdir.name, "audio.wav")
        # Конвертация в WAV 16kHz mono
        cmd = [
            "ffmpeg", "-i", full_path,
            "-ac", "1", "-ar", "16000",
            "-y", wav_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        # Транскрибация
        cmd_newton = [
            "newton", "transcribe", wav_path,
            "--engine", NEWTON_ENGINE,
            "--output-format", "txt"
        ]
        result = subprocess.run(cmd_newton, capture_output=True, text=True, check=True)
        transcript = result.stdout.strip()
        return transcript, None
    except subprocess.CalledProcessError as e:
        err_msg = f"Ошибка транскрибации: {e.stderr or e.stdout or str(e)}"
        return None, err_msg
    except Exception as e:
        return None, f"Неизвестная ошибка: {e}"
    finally:
        tmpdir.cleanup()

def format_message_md(msg, idx, extract_dir):
    """Сформировать Markdown-строку для одного сообщения."""
    # Дата
    ts = msg.get("date_unixtime")
    if ts is not None:
        try:
            ts = int(str(ts))
            date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except:
            date_str = msg.get("date", "Неизвестная дата")
    else:
        date_str = msg.get("date", "Неизвестная дата")
    # Отправитель
    sender = msg.get("from", "Unknown")
    sender_id = msg.get("from_id", "?")
    # Текст
    text = extract_text(msg.get("text"))
    # Медиа
    media_type, media_path = get_media_info(msg)
    # Сборка
    lines = []
    header = f"**{sender}** (ID: {sender_id}) *{date_str}*:"
    lines.append(header)
    if text:
        lines.append(text)
    if media_type and media_path:
        if should_transcribe(media_type, media_path):
            transcript, err = transcribe_file(media_path, extract_dir)
            if transcript is not None:
                lines.append(f"[{media_type}]: {os.path.basename(media_path)}")
                lines.append(f'Транскрипт: "{transcript}"')
            else:
                lines.append(f"[{media_type}]: {os.path.basename(media_path)} (ошибка транскрибации)")
                print(f"[!] Ошибка транскрибации {media_path}: {err}", file=sys.stderr)
        else:
            lines.append(f"[{media_type}]: {os.path.basename(media_path)}")
    return "\n".join(lines) + "\n"

def split_and_save(messages_md_list, base_filename, max_mb):
    """Сохранить список Markdown-сообщений в один или несколько файлов."""
    os.makedirs("/content/llm_output", exist_ok=True)
    max_bytes = max_mb * 1024 * 1024
    part = 1
    current_chunk = []
    current_size = 0
    for msg_md in messages_md_list:
        msg_bytes = len(msg_md.encode("utf-8"))
        # Если добавление этого сообщения превысит лимит и chunk не пуст, записываем текущий
        if current_chunk and current_size + msg_bytes > max_bytes:
            filename = f"{base_filename}_part{part}.md"
            with open(os.path.join("/content/llm_output", filename), "w", encoding="utf-8") as f:
                f.write("\n".join(current_chunk) + "\n")
            print(f"Сохранён {filename} ({current_size/1024/1024:.2f} МБ)")
            part += 1
            current_chunk = []
            current_size = 0
        current_chunk.append(msg_md)
        current_size += msg_bytes
    if current_chunk:
        filename = f"{base_filename}_part{part}.md" if part > 1 else f"{base_filename}.md"
        with open(os.path.join("/content/llm_output", filename), "w", encoding="utf

---

