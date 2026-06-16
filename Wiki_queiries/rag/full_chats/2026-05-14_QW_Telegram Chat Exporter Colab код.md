# Telegram Chat Exporter Colab код

Source: QW | Date: 2026-05-14 | Fragments: 4 | ID: 336ec09d-25d3-4118-aa3e-358eb5deea6d

---

## USER

Напиши мне код на Колабе, который будет делать тоже самое, что этот инструмент: https://github.com/seuyh/Telegram-Chat-Exporter.

---

## AI

Ниже представлен код для выполнения в Google Colab. Этот блокнот воспроизводит ключевые функции оригинального инструмента `Telegram-Chat-Exporter`: он использует библиотеку Telethon для входа в ваш аккаунт Telegram, позволяет выбрать чат, скачать историю сообщений (включая медиафайлы) и создает автономный HTML-файл с удобным интерактивным просмотрщиком.

### 🚀 Как использовать
1.  **Запустите ячейки** в блокноте последовательно.
2.  **Получите `api_id` и `api_hash`** на сайте [my.telegram.org](https://my.telegram.org/apps) и введите их в соответствующие поля в коде.
3.  При первом запуске потребуется **ввести номер телефона** и **код подтверждения** от Telegram.
4.  После успешного входа выберите чат для экспорта из появившегося списка.
5.  Дождитесь окончания процесса. HTML-файл с историей чата будет сохранен в вашем Google Диске.

```python
# Ячейка 1: Установка необходимых библиотек
!pip install -q telethon nest_asyncio

import asyncio
import nest_asyncio
import ipywidgets as widgets
from IPython.display import display
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import os
import base64
from datetime import datetime

# Необходимо для запуска асинхронного кода в среде Colab
nest_asyncio.apply()

print("✅ Библиотеки успешно установлены!")
```

```python
# Ячейка 2: Конфигурация и авторизация
# ВАЖНО: Введите свои реальные данные!
API_ID = int(input("Введите ваш API ID: "))
API_HASH = input("Введите ваш API Hash: ")
SESSION_NAME = "tg_export_session"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def main():
    await client.start()
    me = await client.get_me()
    print(f"✅ Авторизация прошла успешно! Вы вошли как: {me.first_name} (@{me.username})")
    return client

# Запускаем процесс авторизации
client = asyncio.get_event_loop().run_until_complete(main())
```

```python
# Ячейка 3: Выбор чата для экспорта
async def choose_chat(client):
    """Получает список диалогов и позволяет выбрать один."""
    dialogs = await client.get_dialogs()
    
    # Создаем выпадающий список для выбора чата
    chat_list = [(f"{d.name} (ID: {d.id})", d) for d in dialogs]
    dropdown = widgets.Dropdown(
        options=[name for name, _ in chat_list],
        description='Чат:',
        style={'description_width': 'initial'},
        layout={'width': 'max-content'}
    )
    display(dropdown)
    
    # Кнопка подтверждения выбора
    button = widgets.Button(description="Экспортировать выбранный чат")
    output = widgets.Output()
    display(button, output)
    
    def on_click(b):
        with output:
            output.clear_output()
            selected_chat = next((d for name, d in chat_list if name == dropdown.value), None)
            if selected_chat:
                print(f"⏳ Начинаю экспорт чата: {selected_chat.name}")
                asyncio.ensure_future(export_chat(client, selected_chat))
            else:
                print("❌ Ошибка: чат не выбран!")
    
    button.on_click(on_click)

asyncio.get_event_loop().run_until_complete(choose_chat(client))
```

```python
# Ячейка 4: Функция экспорта чата
async def export_chat(client, chat):
    """
    Основная функция экспорта. Скачивает историю сообщений,
    медиафайлы и генерирует HTML-файл.
    """
    # Создаем папку для экспорта
    export_dir = f"export_{chat.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(export_dir, exist_ok=True)
    media_dir = os.path.join(export_dir, "media")
    os.makedirs(media_dir, exist_ok=True)
    
    messages = []
    # Скачиваем сообщения (лимит можно убрать, но для примера оставим 1000)
    async for msg in client.iter_messages(chat, limit=1000):
        # Обработка медиафайлов
        media_path = None
        if msg.media:
            if isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
                try:
                    media_path = await msg.download_media(file=media_dir)
                    if media_path:
                        media_path = os.path.relpath(media_path, export_dir)
                except Exception as e:
                    print(f"⚠️ Ошибка при скачивании медиа: {e}")
        
        # Формируем запись сообщения
        sender = msg.sender
        sender_name = f"{sender.first_name} {sender.last_name}" if sender else "Неизвестный"
        message_data = {
            'id': msg.id,
            'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            'sender': sender_name,
            'text': msg.text or '',
            'media': media_path,
            'reply_to': msg.reply_to_msg_id if msg.reply_to else None
        }
        messages.append(message_data)
    
    # Сортируем сообщения по дате (старые вверху)
    messages.sort(key=lambda x: x['date'])
    
    # Генерируем HTML
    html_content = generate_html(chat.name, messages)
    html_path = os.path.join(export_dir, "messages.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Сохраняем в Google Диск (опционально)
    from google.colab import drive
    drive.mount('/content/drive')
    !cp -r "{export_dir}" "/content/drive/MyDrive/"
    
    print(f"✅ Экспорт завершен! Файл сохранен в папке: {export_dir}")
    print(f"📁 Путь к HTML: {html_path}")
    print(f"📁 Копия сохранена на Google Диск в папку /content/drive/MyDrive/{export_dir}")

def generate_html(chat_name, messages):
    """Генерирует красивый HTML-файл с историей чата."""
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Чат: {chat_name}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
            }}
            .header {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .message {{
                background: white;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .sender {{
                font-weight: bold;
                color: #2a5885;
            }}
            .date {{
                color: #888;
                font-size: 0.9em;
                margin-left: 10px;
            }}
            .text {{
                margin-top: 5px;
            }}
            .media {{
                margin-top: 10px;
            }}
            .media img {{
                max-width: 100%;
                border-radius: 5px;
                cursor: pointer;
            }}
            .reply {{
                font-size: 0.8em;
                color: #666;
                font-style: italic;
                margin-bottom: 5px;
            }}
            
            /* Стили для галереи */
            .gallery-modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.9);
            }}
            .gallery-content {{
                margin: auto;
                display: block;
                max-width: 90%;
                max-height: 80%;
            }}
            .close {{
                position: absolute;
                top: 15px;
                right: 35px;
                color: #f1f1f1;
                font-size: 40px;
                font-weight: bold;
                transition: 0.3s;
                cursor: poin

---

## USER

мне надо, чтобы выполнялось в одной ячейке и файл пусть сохранится автоматически на локальный диск

---

## AI

Вот код для Google Colab, который полностью помещается в одну ячейку и автоматически сохраняет результат на ваш компьютер.

```python
# ============================================================
# Telegram Chat Exporter для Google Colab (одна ячейка)
# Экспорт чата со всеми медиафайлами в автономный HTML-архив
# ============================================================

# 1. Установка библиотек
!pip install -q telethon nest_asyncio

# 2. Импорты и подготовка
import asyncio
import nest_asyncio
import os
import shutil
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from google.colab import files

nest_asyncio.apply()

# 3. Основная асинхронная логика
async def main():
    # ----- Ввод учётных данных -----
    API_ID = input("Введите ваш API ID: ").strip()
    API_HASH = input("Введите ваш API Hash: ").strip()
    SESSION_NAME = "tg_export_session"

    client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)
    await client.start()   # запросит телефон и код, если сессия новая
    me = await client.get_me()
    print(f"✅ Вы вошли как: {me.first_name} (@{me.username})")

    # ----- Выбор чата -----
    dialogs = await client.get_dialogs()
    print("\n📋 Доступные чаты:")
    for i, d in enumerate(dialogs):
        print(f"{i+1}. {d.name} (ID: {d.id})")

    while True:
        try:
            choice = int(input("\nВведите номер чата для экспорта: "))
            if 1 <= choice <= len(dialogs):
                chat = dialogs[choice-1]
                break
            else:
                print("❌ Неверный номер.")
        except ValueError:
            print("❌ Введите число.")

    print(f"\n⏳ Экспортируем чат «{chat.name}»...")

    # ----- Создание папок -----
    export_dir = f"export_{chat.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    media_dir = os.path.join(export_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    # ----- Скачивание сообщений -----
    messages = []
    # limit=None скачивает всю историю; можно заменить на число, например 500
    async for msg in client.iter_messages(chat, limit=None):
        sender = msg.sender
        sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip() if sender else "Неизвестный"

        media_rel_path = None
        if msg.media:
            if isinstance(msg.media, (MessageMediaPhoto, MessageMediaDocument)):
                try:
                    full_path = await msg.download_media(file=media_dir)
                    if full_path:
                        media_rel_path = os.path.relpath(full_path, export_dir)
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки медиа (сообщение {msg.id}): {e}")

        messages.append({
            'id': msg.id,
            'date': msg.date.strftime("%Y-%m-%d %H:%M:%S"),
            'sender': sender_name,
            'text': msg.text or '',
            'media': media_rel_path,
            'reply_to': msg.reply_to_msg_id if msg.reply_to else None
        })

    messages.sort(key=lambda x: x['date'])   # старые сверху

    # ----- Генерация HTML -----
    html = generate_html(chat.name, messages)
    html_path = os.path.join(export_dir, "messages.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # ----- Упаковка в ZIP и скачивание -----
    zip_base = "telegram_chat_export"
    shutil.make_archive(zip_base, 'zip', export_dir)
    print(f"✅ Экспорт завершён! Начинается загрузка файла {zip_base}.zip…")
    files.download(f"{zip_base}.zip")

# 4. Генератор HTML с относительными ссылками на медиа
def generate_html(chat_name, messages):
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Чат: {chat_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f5f5f5; margin:0; padding:20px; }}
        .container {{ max-width:800px; margin:0 auto; }}
        .header {{ background:#fff; padding:20px; border-radius:10px; margin-bottom:20px; box-shadow:0 2px 4px rgba(0,0,0,.1); }}
        .message {{ background:#fff; padding:15px; margin-bottom:10px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,.1); }}
        .sender {{ font-weight:bold; color:#2a5885; }}
        .date {{ color:#888; font-size:0.9em; margin-left:10px; }}
        .text {{ margin-top:5px; white-space:pre-wrap; }}
        .media {{ margin-top:10px; }}
        .media img, .media video {{ max-width:100%; border-radius:5px; }}
        .reply {{ font-size:0.8em; color:#666; font-style:italic; margin-bottom:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{chat_name}</h1>
            <p>Дата экспорта: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        <div class="messages">
"""
    for msg in messages:
        html += '<div class="message">'
        if msg['reply_to']:
            html += f'<div class="reply">↪ В ответ на сообщение #{msg["reply_to"]}</div>'
        html += f'<span class="sender">{msg["sender"]}</span>'
        html += f'<span class="date">{msg["date"]}</span>'
        if msg['text']:
            # простая защита от HTML-инъекций
            safe = msg['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html += f'<div class="text">{safe}</div>'
        if msg['media']:
            src = msg['media']
            ext = os.path.splitext(src)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                html += f'<div class="media"><img src="{src}" loading="lazy"></div>'
            elif ext in ['.mp4', '.webm', '.ogg']:
                html += f'<div class="media"><video controls src="{src}" style="max-width:100%"></video></div>'
            else:
                html += f'<div class="media"><a href="{src}">📎 {os.path.basename(src)}</a></div>'
        html += '</div>'
    html += """
        </div>
    </div>
</body>
</html>"""
    return html

# 5. Запуск
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

### Как использовать
1. **Скопируйте весь код в одну ячейку** Colab и запустите её.
2. **Введите `API ID` и `API Hash`**, полученные на [my.telegram.org](https://my.telegram.org/apps).
3. При первом запуске потребуется **номер телефона** и **код подтверждения** – просто вводите их в появившиеся поля.
4. Из списка чатов введите **номер нужного чата**.
5. Дождитесь окончания экспорта – архив `telegram_chat_export.zip` **автоматически загрузится на ваш компьютер**.

### Что внутри ZIP-архива?
- `messages.html` – просмотрщик чата (откройте в браузере).
- папка `media` – все изображения, видео и документы, сохранённые локально.

> **Примечание:** Экспорт больших чатов может занять много времени. Чтобы ограничить количество сообщений, замените `limit=None` в строке `async for msg in client.iter_messages(chat, limit=None):` на нужное число (например, `limit=500`).

---

