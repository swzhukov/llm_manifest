# Многофайловая конвертация Markdown в DOCX

Source: QW | Date: 2026-01-21 | Fragments: 2 | ID: 110c015b-ce51-4f43-a84f-cdef697fe208

---

## USER

# ======================
# УСТАНОВКА PANDOC
# ======================
print("Установка pandoc...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc > /dev/null 2>&1
print("✓ Pandoc установлен!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
from google.colab import files

# ======================
# ПРОСТАЯ КОНВЕРТАЦИЯ MARKDOWN → HTML
# ======================
def convert_markdown_to_html(md_file):
    """Простая конвертация Markdown в красивый HTML"""

    # Читаем Markdown файл
    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Создаем временный Markdown файл для pandoc
    temp_md = "temp_input.md"
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    # Конвертируем в базовый HTML с помощью pandoc
    html_file = md_file.replace('.md', '.html')
    os.system(f'pandoc "{temp_md}" -o "{html_file}" -t html5 --standalone')

    # Удаляем временный файл
    os.remove(temp_md)

    # Читаем сгенерированный HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Простой и элегантный CSS
    beautiful_css = """
    <style>
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
            background: #fafafa;
        }

        .document {
            background: white;
            padding: 50px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            font-size: 2.2em;
        }

        h2 {
            color: #34495e;
            margin-top: 35px;
            padding-left: 15px;
            border-left: 4px solid #3498db;
        }

        h3 {
            color: #465c7a;
            margin-top: 25px;
        }

        p {
            margin: 16px 0;
            text-align: justify;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }

        th {
            background: #34495e;
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
        }

        td {
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
        }

        tr:nth-child(even) {
            background: #f8f9fa;
        }

        code {
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }

        pre {
            background: #2d3748;
            color: white;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 20px 0;
        }

        pre code {
            background: none;
            padding: 0;
            border: none;
            color: inherit;
        }

        blockquote {
            border-left: 4px solid #3498db;
            padding: 15px 20px;
            margin: 20px 0;
            background: #f8f9fa;
            font-style: italic;
        }

        ul, ol {
            padding-left: 25px;
            margin: 15px 0;
        }

        li {
            margin: 8px 0;
        }

        a {
            color: #3498db;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            body {
                padding: 20px 10px;
            }

            .document {
                padding: 30px 20px;
            }

            h1 {
                font-size: 1.8em;
            }

            table {
                font-size: 12px;
            }
        }
    </style>
    """

    # Создаем финальный HTML с нашим CSS
    final_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_file.replace('.md', '')}</title>
    {beautiful_css}
</head>
<body>
    <div class="document">
        {html_content}
    </div>
</body>
</html>"""

    # Сохраняем финальный HTML файл
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(final_html)

    return html_file

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 50)
print("📄 ПРОСТОЙ КОНВЕРТЕР MARKDOWN → HTML")
print("=" * 50)

# Загружаем файл
print("Загрузите ваш Markdown файл:")
uploaded = files.upload()

if not uploaded:
    print("❌ Файл не загружен")
else:
    filename = list(uploaded.keys())[0]
    print(f"📄 Обрабатываем: {filename}")

    try:
        # Проверяем что это Markdown файл
        if not filename.lower().endswith(('.md', '.markdown')):
            print("⚠️  Внимание: файл может не быть Markdown")

        # Показываем информацию о файле
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"📊 Размер: {len(content)} символов")

        # Конвертируем в HTML
        print("\n🎨 Создаем красивый HTML...")
        html_file = convert_markdown_to_html(filename)

        if html_file and os.path.exists(html_file):
            print(f"✅ HTML готов: {html_file}")
            files.download(html_file)
            print("\n📥 Файл доступен для скачивания!")
            print("\n💡 Откройте файл в браузере для просмотра")
        else:
            print("❌ Не удалось создать HTML файл")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n🎉 Готово!")

нужно, чтобы код делал тоже самое, но: а) чтобы мог обрабатывать несколько файлов; б) на выходе получался docx

---

## AI

Вот обновленный код, который обрабатывает несколько файлов и конвертирует их в DOCX:

```python
# ======================
# УСТАНОВКА PANDOC
# ======================
print("Установка pandoc...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc > /dev/null 2>&1
print("✓ Pandoc установлен!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import zipfile
from google.colab import files

# ======================
# КОНВЕРТАЦИЯ MARKDOWN → DOCX
# ======================
def convert_markdown_to_docx(md_file, output_file=None):
    """Конвертация Markdown в DOCX с использованием pandoc"""
    
    if output_file is None:
        output_file = md_file.replace('.md', '.docx')
    
    # Используем pandoc для конвертации
    cmd = f'pandoc "{md_file}" -o "{output_file}"'
    result = os.system(cmd)
    
    if result == 0:
        return output_file
    else:
        print(f"⚠️  Ошибка при конвертации {md_file}")
        return None

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 60)
print("📄 КОНВЕРТЕР MARKDOWN → DOCX (МНОГОФАЙЛОВЫЙ)")
print("=" * 60)

# Загружаем файлы
print("Загрузите ваши Markdown файлы (можно несколько):")
uploaded = files.upload()

if not uploaded:
    print("❌ Файлы не загружены")
else:
    md_files = []
    converted_files = []
    
    # Сохраняем все загруженные файлы
    for filename, content in uploaded.items():
        with open(filename, 'wb') as f:
            f.write(content)
        
        # Проверяем, что это Markdown файл
        if filename.lower().endswith(('.md', '.markdown', '.txt')):
            md_files.append(filename)
            print(f"✓ Загружен: {filename} ({len(content)} байт)")
        else:
            print(f"⚠️  Пропущен: {filename} (не Markdown формат)")
    
    if not md_files:
        print("❌ Нет файлов Markdown для обработки")
    else:
        print(f"\n📊 Найдено {len(md_files)} Markdown файлов для обработки")
        
        # Конвертируем каждый файл
        for md_file in md_files:
            print(f"\n🔄 Конвертируем: {md_file}")
            try:
                docx_file = convert_markdown_to_docx(md_file)
                if docx_file and os.path.exists(docx_file):
                    converted_files.append(docx_file)
                    print(f"✅ Создан: {docx_file}")
                    
                    # Скачиваем каждый файл отдельно
                    print(f"📥 Скачиваем {docx_file}...")
                    files.download(docx_file)
                else:
                    print(f"❌ Ошибка при создании DOCX для {md_file}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        # Предлагаем скачать все файлы одним архивом
        if len(converted_files) > 1:
            print("\n" + "=" * 60)
            print("🗂️  СОЗДАНИЕ АРХИВА ВСЕХ ФАЙЛОВ")
            print("=" * 60)
            
            zip_filename = "converted_docs.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for docx_file in converted_files:
                    zipf.write(docx_file)
            
            print(f"✅ Создан архив: {zip_filename} ({os.path.getsize(zip_filename)} байт)")
            print("📥 Скачиваем архив со всеми документами...")
            files.download(zip_filename)
        
        print("\n" + "=" * 60)
        print("📋 ИТОГИ КОНВЕРТАЦИИ")
        print("=" * 60)
        print(f"Обработано файлов: {len(md_files)}")
        print(f"Успешно конвертировано: {len(converted_files)}")
        
        if len(converted_files) > 0:
            print("\n✅ Конвертация завершена успешно!")
            print("\n💡 Откройте DOCX файлы в Microsoft Word, LibreOffice или Google Docs")
        else:
            print("\n⚠️  Не удалось конвертировать ни одного файла")

# ======================
# ДОПОЛНИТЕЛЬНЫЕ ВОЗМОЖНОСТИ
# ======================
print("\n" + "=" * 60)
print("🎯 ДОПОЛНИТЕЛЬНЫЕ ВОЗМОЖНОСТИ")
print("=" * 60)

print("""
Для дополнительной настройки DOCX вы можете:

1. Использовать шаблон DOCX:
   pandoc input.md -o output.docx --reference-doc template.docx

2. Установить тему документа:
   pandoc input.md -o output.docx --metadata theme=default

3. Добавить нумерацию страниц:
   pandoc input.md -o output.docx --number-sections

4. Использовать стили pandoc:
   pandoc input.md -o output.docx -s
""")

print("\n🎉 Работа завершена!")
```

**Основные изменения:**

1. **Многофайловая обработка**: Теперь можно загружать и обрабатывать несколько Markdown файлов одновременно.

2. **Конвертация в DOCX**: Используется команда `pandoc input.md -o output.docx` для конвертации в формат Word.

3. **Пакетная обработка**: 
   - Каждый файл конвертируется отдельно
   - Все DOCX файлы можно скачать по одному
   - Дополнительно создается ZIP-архив со всеми файлами

4. **Информативность**: 
   - Показывается прогресс обработки каждого файла
   - Отображаются итоги конвертации
   - Добавлены подсказки по дополнительным возможностям pandoc

**Как использовать:**
1. Запустите код в Google Colab
2. Загрузите один или несколько Markdown файлов
3. Каждый файл будет автоматически конвертирован в DOCX
4. Файлы можно скачать по отдельности или одним архивом
5. Откройте DOCX файлы в любом редакторе Word

**Примечание:** Pandoc создает стандартные DOCX файлы, которые корректно открываются в Microsoft Word, LibreOffice, Google Docs и других редакторах.

---

