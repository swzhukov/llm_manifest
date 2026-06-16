# Конвертер Markdown в PDF для Colab

Source: QW | Date: 2025-11-19 | Fragments: 24 | ID: 33a5cde4-01ab-4a7f-b23c-2a5f223f5eb8

---

## USER

Создай код для Google Colab, который конвертирует большие Markdown-файлы в PDF с учетом:

## ТРЕБОВАНИЯ К КОНВЕРТАЦИИ:

### 1. Поддержка контента:
- **Кириллица** - должна отображаться корректно
- **Псевдографика/ASCII-арт** - максимально сохранять форматирование
- **Сложные таблицы** - исправлять разорванные таблицы
- **Специальные символы** - заменять проблемные символы (,  и т.д.) на нормальные Unicode

### 2. Обработка файлов:
- **Любой размер** - обработка больших файлов без падения
- **Автоопределение кодировки** - utf-8, windows-1251, cp1251
- **Предобработка контента** - очистка и исправление форматирования перед конвертацией

### 3. Надежность конвертации:
- **Многоуровневый подход** - несколько методов с fallback'ами
- **Автоматическое исправление ошибок** - предобработка проблемных участков
- **Подробная диагностика** - информация о проблемах для отладки

### 4. Выходные форматы:
- **PDF (приоритет)** - с правильными шрифтами и версткой
- **HTML (резервный)** - с профессиональным CSS для ручной конвертации через браузер

## ТЕХНИЧЕСКИЕ ДЕТАЛИ:

### Установка пакетов:
- pandoc, texlive-xetex, texlive-lang-cyrillic
- Шрифты: DejaVu, Liberation (проверенные, доступные)
- Минимальный вывод при установке

### Обработка контента:
- Замена проблемных символов на нормальные Unicode
- Исправление разорванных таблиц
- Улучшение форматирования заголовков и списков
- Сохранение переносов строк (--wrap=preserve)

### Конвертация:
- Основной метод: XeLaTeX с проверенными шрифтами
- Резервные методы: простые настройки, LuaLaTeX
- HTML альтернатива с профессиональным CSS
- Автоматическое определение успешности конвертации

### Пользовательский интерфейс:
- Простой upload/download через Colab
- Информация о прогрессе и проблемах
- Рекомендации при неудачной конвертации

Код должен быть самодостаточным, обрабатывать edge cases и предоставлять наилучший возможный результат для любого Markdown-файла.

---

## AI

Вот готовый код для Google Colab, который преобразует большие Markdown-файлы в PDF с учетом кириллицы, псевдографики и сложных таблиц.

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка системных пакетов...")
!apt-get update -qq
!apt-get install -qq pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended texlive-latex-extra latexmk
!pip install -q pdfkit pygments weasyprint

print("Установка завершена!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import io
import os
import re
import chardet
import pandas as pd
from google.colab import files
from IPython.display import HTML, display
import codecs

# ======================
# ФУНКЦИИ ПРЕДОБРАБОТКИ
# ======================
def detect_encoding(file_path):
    """Автоопределение кодировки файла"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding'] if result['confidence'] > 0.7 else 'utf-8'
        print(f"Определена кодировка: {encoding} (уверенность: {result['confidence']:.2f})")
        return encoding

def replace_problematic_chars(text):
    """Замена проблемных символов на нормальные Unicode"""
    replacements = {
        '': '→',    # Стрелка вправо
        '': '↑',    # Стрелка вверх  
        '': '↓',    # Стрелка вниз
        '': '•',    # Маркер списка
        '': '│',    # Вертикальная линия
        '': '─',    # Горизонтальная линия
    }
    
    for problematic, replacement in replacements.items():
        text = text.replace(problematic, replacement)
    
    return text

def fix_broken_tables(text):
    """Исправление разорванных таблиц Markdown"""
    # Паттерн для поиска таблиц с разорванными границами
    table_pattern = r'(\|.*\|\n)(?!\|)'
    
    def fix_table(match):
        table_header = match.group(1)
        # Добавляем разделительную строку если её нет
        if '|---' not in table_header:
            cols = table_header.count('|') - 1
            separator = '|' + '---|' * cols + '\n'
            return table_header + separator
        return table_header
    
    text = re.sub(table_pattern, fix_table, text)
    return text

def preprocess_markdown(content):
    """Основная предобработка Markdown контента"""
    print("Начата предобработка контента...")
    
    # Замена проблемных символов
    content = replace_problematic_chars(content)
    
    # Исправление таблиц
    content = fix_broken_tables(content)
    
    # Улучшение форматирования заголовков
    content = re.sub(r'^(#+)\s*(.*?)\s*$', r'\1 \2', content, flags=re.MULTILINE)
    
    # Сохранение псевдографики
    content = re.sub(r'(\+--+\+)', r'```\n\1\n```', content)
    
    print("Предобработка завершена")
    return content

# ======================
# ФУНКЦИИ КОНВЕРТАЦИИ
# ======================
def convert_with_pandoc(md_file, output_pdf, method='xelatex'):
    """Конвертация через Pandoc с выбранным методом"""
    try:
        print(f"Попытка конвертации с {method}...")
        
        if method == 'xelatex':
            cmd = f'pandoc "{md_file}" -o "{output_pdf}" --pdf-engine=xelatex -V mainfont="DejaVu Serif" -V sansfont="DejaVu Sans" -V monofont="DejaVu Sans Mono" -V geometry:margin=2cm --wrap=preserve'
        elif method == 'luatex':
            cmd = f'pandoc "{md_file}" -o "{output_pdf}" --pdf-engine=luatex -V mainfont="DejaVu Serif" -V geometry:margin=2cm --wrap=preserve'
        else:  # simple latex
            cmd = f'pandoc "{md_file}" -o "{output_pdf}" --pdf-engine=pdflatex -V geometry:margin=2cm --wrap=preserve'
        
        result = os.system(cmd)
        
        if result == 0 and os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
            print(f"✓ Успешная конвертация с {method}")
            return True
        else:
            print(f"✗ Ошибка конвертации с {method}")
            return False
            
    except Exception as e:
        print(f"Ошибка при конвертации {method}: {str(e)}")
        return False

def create_html_backup(md_file, output_html):
    """Создание HTML резервной копии с профессиональным CSS"""
    try:
        print("Создание HTML резервной копии...")
        
        css_styles = """
        <style>
            body { 
                font-family: "DejaVu Sans", "Liberation Sans", sans-serif; 
                line-height: 1.6; 
                margin: 2cm;
                color: #333;
            }
            pre, code { 
                font-family: "DejaVu Sans Mono", "Liberation Mono", monospace; 
                background: #f5f5f5;
                padding: 0.5em;
                border-radius: 3px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            blockquote {
                border-left: 4px solid #ddd;
                padding-left: 1em;
                margin-left: 0;
                color: #666;
            }
        </style>
        """
        
        # Конвертируем markdown в HTML через pandoc
        html_content = os.popen(f'pandoc "{md_file}" -t html').read()
        
        # Добавляем CSS стили
        full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css_styles}</head><body>{html_content}</body></html>"
        
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(full_html)
            
        print("✓ HTML резервная копия создана")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка создания HTML: {str(e)}")
        return False

def multi_stage_conversion(uploaded_file):
    """Многоуровневая конвертация с fallback'ами"""
    original_filename = uploaded_file.name
    base_name = os.path.splitext(original_filename)[0]
    
    print(f"Начата обработка файла: {original_filename}")
    
    # Шаг 1: Определение кодировки и чтение файла
    temp_input = "temp_input.md"
    with open(temp_input, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    encoding = detect_encoding(temp_input)
    
    try:
        with codecs.open(temp_input, 'r', encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        print("Ошибка чтения с определенной кодировкой, пробуем utf-8...")
        with codecs.open(temp_input, 'r', encoding='utf-8') as f:
            content = f.read()
    
    # Шаг 2: Предобработка контента
    processed_content = preprocess_markdown(content)
    
    processed_file = "processed.md"
    with open(processed_file, 'w', encoding='utf-8') as f:
        f.write(processed_content)
    
    results = {}
    
    # Шаг 3: Попытки конвертации в PDF
    pdf_outputs = [
        (f"{base_name}_xelatex.pdf", 'xelatex'),
        (f"{base_name}_luatex.pdf", 'luatex'), 
        (f"{base_name}_simple.pdf", 'simple')
    ]
    
    for pdf_file, method in pdf_outputs:
        if convert_with_pandoc(processed_file, pdf_file, method):
            results['pdf'] = pdf_file
            break
    
    # Шаг 4: Создание HTML резервной копии
    html_file = f"{base_name}_backup.html"
    if create_html_backup(processed_file, html_file):
        results['html'] = html_file
    
    # Очистка временных файлов
    for temp_file in [temp_input, processed_file]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    return results

# ======================
# ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС
# ======================
def main():
    """Основная функция с пользовательским интерфейсом"""
    print("=" * 60)
    print("🔄 КОНВЕРТЕР MARKDOWN В PDF ДЛЯ GOOGLE COLAB")
    print("=" * 60)
    print("\nПоддерживаемые функции:")
    print("✓ Корректное отображение кириллицы")
    print("✓ Сохранение псевдографик

---

## USER

А вот такой код посмотри: 
# Установка правильных пакетов
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended > /dev/null 2>&1

import os
import subprocess
import re
from google.colab import files

def fix_markdown_formatting(content):
    """
    Исправляем проблемы форматирования в Markdown
    """
    # Заменяем проблемные символы
    symbol_replacements = {
        '': '•',    # Заменяем на обычный маркер
        '': '→',    # Стрелка вправо
        '': '⇒',   # Двойная стрелка
        '00': '◉',   # Заполненный круг  
        '0': '○',    # Пустой круг
    }
    
    for old, new in symbol_replacements.items():
        content = content.replace(old, new)
    
    # Исправляем разорванные таблицы
    content = re.sub(r'ЧЁРНОВИКИ\s+ОБЩИЕ\s+УНИКАЛЬНЫЕ\s+РЕКОМЕНДУЕМЫЕ\s+НЕРЕКОМЕНД', 
                    '| ЧЕРНОВИКИ | ОБЩИЕ | УНИКАЛЬНЫЕ | РЕКОМЕНДУЕМЫЕ | НЕРЕКОМЕНДУЕМЫЕ |\n|-----------|-------|------------|---------------|-----------------|', 
                    content)
    
    # Исправляем другие таблицы
    content = re.sub(r'_{5,}', '---', content)
    content = re.sub(r'={5,}', '===', content)
    
    # Улучшаем форматирование заголовков
    content = re.sub(r'^#\s+(.*?)\s*$', r'# \1\n', content, flags=re.MULTILINE)
    content = re.sub(r'^##\s+(.*?)\s*$', r'## \1\n', content, flags=re.MULTILINE)
    
    return content

def create_robust_latex_template():
    """Создаем надежный LaTeX шаблон"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{russian}
\setotherlanguage{english}
\usepackage[margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{graphicx}

% Используем системные шрифты, которые точно есть
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Настройки для списков
\setlist{nosep, leftmargin=*}

% Улучшенное оформление
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries}{\thesubsection}{1em}{}

\begin{document}
$body$
\end{document}"""

def convert_markdown_robust(input_path, output_path=None):
    """
    Надежная конвертация Markdown в PDF
    """
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '_final.pdf'
    
    try:
        # Читаем и обрабатываем файл
        with open(input_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        print("Обрабатываем форматирование...")
        processed_content = fix_markdown_formatting(original_content)
        
        # Сохраняем обработанную версию
        processed_file = input_path + '_fixed.md'
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        # Создаем надежный шаблон
        template_file = 'robust_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(create_robust_latex_template())
        
        # Конвертируем с надежными настройками
        print("Конвертируем в PDF...")
        cmd = [
            'pandoc', processed_file,
            '-o', output_path,
            '--pdf-engine=xelatex',
            '--template=' + template_file,
            '-V', 'geometry:margin=1in',
            '--variable', 'mainfont=DejaVu Serif',
            '--variable', 'monofont=DejaVu Sans Mono',
            '--wrap=preserve',
            '--standalone'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Удаляем временные файлы
        os.remove(processed_file)
        os.remove(template_file)
        
        print("✓ Конвертация завершена успешно!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка конвертации: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr[:500]}")
    except Exception as e:
        print(f"Общая ошибка: {e}")
    
    # Удаляем временные файлы в случае ошибки
    for temp_file in [input_path + '_fixed.md', 'robust_template.tex']:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    return False

def create_html_alternative(input_path):
    """
    Создаем HTML версию как запасной вариант
    """
    html_file = os.path.splitext(input_path)[0] + '_formatted.html'
    
    try:
        # Читаем и обрабатываем файл
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        processed_content = fix_markdown_formatting(content)
        
        # Сохраняем обработанную версию
        temp_md = input_path + '_temp.md'
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        # Конвертируем в HTML
        cmd = [
            'pandoc', temp_md,
            '-o', html_file,
            '-t', 'html5',
            '--standalone',
            '--wrap=preserve'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Читаем HTML и добавляем CSS
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # CSS для улучшения внешнего вида
        css = """
        <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 8px;
        }
        h3 {
            color: #465c7a;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        code, pre {
            font-family: 'Courier New', monospace;
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre {
            padding: 15px;
            overflow-x: auto;
        }
        ul, ol {
            padding-left: 20px;
        }
        li {
            margin: 5px 0;
        }
        .header-anchor {
            color: inherit;
            text-decoration: none;
        }
        .header-anchor:hover {
            text-decoration: underline;
        }
        </style>
        """
        
        # Вставляем CSS в head
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', css + '</head>')
        else:
            # Если нет тега head, создаем его
            html_content = f'<head><meta charset="UTF-8">{css}</head>\n<body>\n{html_content}\n</body>'
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        os.remove(temp_md)
        return html_file
        
    except Exception as e:
        print(f"Ошибка создания HTML: {e}")
        # Удаляем временный файл
        if os.path.exists(input_path + '_temp.md'):
            os.remove(input_path + '_temp.md')
        return None

# Основной процесс
print("Загрузите ваш Markdown файл:")
uploaded = files.upload()

if not uploaded:
    print("Файл не загружен!")
else:
    md_file = list(uploaded.keys())[0]
    print(f"Загружен файл: {md_file}")
    
    # Показываем информацию о файле
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Размер файла: {len(content)} символов")
    
    # Сначала пробуем PDF конвертацию
    print("\nПробуем конвертацию в PDF...")
    success = convert_markdown_robust(md_file)
    
    if success:
        # Находим созданный PDF
        base_name = os.path.splitext(md_file)[0]
        pdf_files = [f for f in os.listdir('.') if f.startswith(base_name) and f.endswith('_final.pdf')]
        
        if pdf_files:
            pdf_file = pdf_files[0]
            print(f"✓ PDF успешно создан: {pdf_file}")
            files.download(pdf_file)
        else:
            print("PDF файл не найден, создаем HTML версию...")
            success = False
    
    # Если PDF не удался, создаем HTML версию
    if not success:
        print("\nСоздаем HTML версию...")
        html_file = create_html_alternative(md_file)
        
        if html_file and os.path.exists(html_file):
            print(f"✓ Создан HTML файл: {html_file}")
            files.download(html_file)
            print("\nРекомендация:")
            print("1. Откройте HTML файл в браузере")
            print("2. Используйте 'Печать' → 'Сохранить как PDF'")
            print("3. Это даст лучший контроль над вёрсткой")
        else:
            print("✗ Не удалось создать HTML файл")

Есть что взять из него для твоего идеального решения?

---

## AI

Отличный код! Я вижу несколько полезных идей, которые можно интегрировать в улучшенную версию. Вот что стоит взять из вашего кода:

## 🔥 Сильные стороны вашего кода:

1. **Кастомный LaTeX шаблон** - более контролируемая верстка
2. **Лучшая обработка таблиц** - конкретные паттерны для исправления
3. **Улучшенный CSS для HTML** - более профессиональный дизайн
4. **Конкретные замены символов** - целевые исправления проблемных символов

## 🚀 Улучшенная версия с интеграцией лучших практик:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка системных пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended texlive-latex-extra latexmk > /dev/null 2>&1
!pip install -q chardet

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
import chardet
import subprocess
from google.colab import files
import io
import codecs

# ======================
# УЛУЧШЕННЫЕ ФУНКЦИИ ПРЕДОБРАБОТКИ
# ======================
def detect_encoding(file_path):
    """Автоопределение кодировки файла с улучшенной логикой"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    # Пробуем несколько методов определения кодировки
    result = chardet.detect(raw_data)
    
    # Приоритет кодировок для русских текстов
    if result['confidence'] > 0.7:
        encoding = result['encoding']
    else:
        # Пробуем определить по содержимому
        for test_encoding in ['utf-8', 'windows-1251', 'cp1251', 'iso-8859-1']:
            try:
                raw_data.decode(test_encoding)
                encoding = test_encoding
                break
            except:
                continue
        else:
            encoding = 'utf-8'
    
    print(f"Определена кодировка: {encoding} (уверенность: {result.get('confidence', 'N/A')})")
    return encoding

def create_advanced_latex_template():
    """Создаем улучшенный LaTeX шаблон на основе вашего кода"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{russian}
\setotherlanguage{english}
\usepackage[margin=1.5cm]{geometry}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{enumitem}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{xcolor}

% Настройки шрифтов с fallback'ами
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Улучшенные настройки для списков
\setlist{nosep, leftmargin=*, topsep=2pt}

% Настройки для таблиц
\usepackage{multirow}
\usepackage{array}
\newcolumntype{L}{>{\raggedright\arraybackslash}p{0.2\textwidth}}
\newcolumntype{R}{>{\raggedleft\arraybackslash}p{0.15\textwidth}}

% Стили для кода
\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single,
    backgroundcolor=\color{gray!10}
}

% Улучшенное оформление заголовков
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries\sffamily}{\thesection}{1em}{}
\titleformat{\subsection}{\large\bfseries\sffamily}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\bfseries\sffamily}{\thesubsubsection}{1em}{}

\begin{document}
\raggedbottom
$body$
\end{document}"""

def fix_markdown_formatting_advanced(content):
    """
    Улучшенная функция предобработки Markdown
    """
    print("Применяем улучшенную предобработку...")
    
    # Расширенный словарь замены символов (из вашего кода + дополнения)
    symbol_replacements = {
        '': '•',      # Маркер списка
        '': '→',      # Стрелка вправо  
        '': '↓',      # Стрелка вниз
        '': '•',      # Альтернативный маркер
        '': '│',      # Вертикальная линия
        '': '─',      # Горизонтальная линия
        '00': '◉',     # Заполненный круг
        '0': '○',      # Пустой круг
        '': '•',      # Еще один вариант маркера
    }
    
    for old, new in symbol_replacements.items():
        content = content.replace(old, new)
    
    # Исправление специфических таблиц (из вашего кода)
    table_fixes = [
        (r'ЧЁРНОВИКИ\s+ОБЩИЕ\s+УНИКАЛЬНЫЕ\s+РЕКОМЕНДУЕМЫЕ\s+НЕРЕКОМЕНД', 
         '| ЧЕРНОВИКИ | ОБЩИЕ | УНИКАЛЬНЫЕ | РЕКОМЕНДУЕМЫЕ | НЕРЕКОМЕНДУЕМЫЕ |\n|-----------|-------|------------|---------------|-----------------|'),
    ]
    
    for pattern, replacement in table_fixes:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Улучшенное исправление таблиц
    content = fix_tables_advanced(content)
    
    # Исправление заголовков (из вашего кода)
    content = re.sub(r'^#\s+(.*?)\s*$', r'# \1\n', content, flags=re.MULTILINE)
    content = re.sub(r'^##\s+(.*?)\s*$', r'## \1\n', content, flags=re.MULTILINE)
    content = re.sub(r'^###\s+(.*?)\s*$', r'### \1\n', content, flags=re.MULTILINE)
    
    # Сохранение псевдографики в блоках кода
    content = protect_ascii_art(content)
    
    # Нормализация переносов строк
    content = re.sub(r'\r\n', '\n', content)
    content = re.sub(r'\r', '\n', content)
    
    return content

def fix_tables_advanced(content):
    """Улучшенное исправление таблиц"""
    # Исправляем разорванные разделители (из вашего кода)
    content = re.sub(r'_{5,}', '---', content)
    content = re.sub(r'={5,}', '===', content)
    
    # Автоматическое добавление разделительных строк для таблиц
    lines = content.split('\n')
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith('|') and '---' not in lines[i]:
            # Проверяем следующую строку
            if i + 1 < len(lines) and lines[i + 1].startswith('|'):
                # Нашли таблицу без разделителя - добавляем его
                cols = lines[i].count('|') - 1
                separator = '|' + ' --- |' * cols
                lines.insert(i + 1, separator)
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    return '\n'.join(lines)

def protect_ascii_art(content):
    """Защита ASCII-арта и псевдографики"""
    # Паттерны для псевдографики
    ascii_patterns = [
        r'\+-+\+',  # Боксы типа +---+
        r'\|\s*\|',  # Вертикальные линии
        r'┌[─┬┐]*┐',  # Unicode псевдографика
        r'├[─┼┤]*┤',
    ]
    
    for pattern in ascii_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            art = match.group()
            # Оборачиваем в блок кода
            protected = f"\n```\n{art}\n```\n"
            content = content.replace(art, protected)
    
    return content

# ======================
# УЛУЧШЕННЫЕ ФУНКЦИИ КОНВЕРТАЦИИ
# ======================
def convert_with_custom_template(md_file, output_pdf, method='xelatex'):
    """Конвертация с кастомным LaTeX шаблоном"""
    try:
        print(f"Пробуем метод: {method} с кастомным шаблоном...")
        
        # Создаем кастомный шаблон
        template_content = create_advanced_latex_template()
        template_file = 'custom_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        if method == 'xelatex':
            cmd = [
                'pandoc', md_file, '-o', output_pdf,
                '--pdf-engine=xelatex',
                f'--template={template_file}',
                '--wrap=preserve',
                '--standalone',
                '-V', 'geometry:margin=1.5cm'
            ]
        elif method == 'luatex':
            cmd = [
                'pandoc', md_file, '-o', output_pdf,
                '--pdf-engine=luatex', 
                f'--template={template_file}',
                '--wrap=preserve',
                '--standalone'
            ]
        else:  # pdflatex fallback
            cmd = [
                'pandoc', md_file, '-o', output_pdf,
                '--pdf-engine=pdflatex',
                '--wrap=preserve',
                '--standalone',
                '-V', 'geometry:margin=1.5cm'
            ]
        
        result = subprocess.ru

---

## USER

Ой, что-то ерунда какая-то получилась. По крайней мере, в таблицах. И зачем мне две версии вообще?

---

## AI

Согласен! Давайте сделаем один надежный вариант без лишних сложностей. Вот упрощенный и улучшенный код:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended > /dev/null 2>&1

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files

# ======================
# ПРОСТАЯ И ЭФФЕКТИВНАЯ ПРЕДОБРАБОТКА
# ======================
def clean_markdown(content):
    """
    Простая и эффективная очистка Markdown
    """
    print("Очищаем Markdown...")
    
    # Только самые необходимые замены символов
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
        '': '│',
        '': '─',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Простое исправление таблиц - только самое важное
    lines = content.split('\n')
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Если это строка с заголовком таблицы, а следующая строка не разделитель
        if line.startswith('|') and '---' not in line:
            cleaned_lines.append(line)
            # Проверяем следующую строку
            if i + 1 < len(lines) and lines[i + 1].startswith('|'):
                # Добавляем стандартный разделитель
                col_count = line.count('|') - 1
                separator = '|' + ' --- |' * col_count
                cleaned_lines.append(separator)
            i += 1
        else:
            cleaned_lines.append(line)
            i += 1
    
    return '\n'.join(cleaned_lines)

# ======================
# ПРОСТОЙ И НАДЕЖНЫЙ ШАБЛОН LaTeX
# ======================
def create_simple_template():
    """Простой и надежный LaTeX шаблон"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{russian}
\setotherlanguage{english}
\usepackage[margin=2cm]{geometry}
\usepackage{booktabs}
\usepackage{array}

% Простые надежные шрифты
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Минимальные настройки для таблиц
\newcolumntype{L}{>{\raggedright}p{0.2\textwidth}}
\newcolumntype{C}{>{\centering}p{0.15\textwidth}}
\newcolumntype{R}{>{\raggedleft}p{0.15\textwidth}}

\begin{document}
\raggedbottom
$body$
\end{document}"""

# ======================
# ОСНОВНАЯ ФУНКЦИЯ КОНВЕРТАЦИИ
# ======================
def convert_markdown_to_pdf(md_file):
    """
    Простая и надежная конвертация Markdown в PDF
    """
    base_name = os.path.splitext(md_file)[0]
    pdf_output = base_name + '.pdf'
    
    try:
        # Читаем исходный файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Очищаем контент
        cleaned_content = clean_markdown(content)
        
        # Сохраняем очищенную версию
        cleaned_file = 'cleaned.md'
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Создаем простой шаблон
        template_file = 'simple_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(create_simple_template())
        
        print("Конвертируем в PDF...")
        
        # Простая команда конвертации
        cmd = f"""
        pandoc "{cleaned_file}" -o "{pdf_output}" \
            --pdf-engine=xelatex \
            --template="{template_file}" \
            --wrap=preserve \
            --standalone
        """
        
        result = os.system(cmd)
        
        # Удаляем временные файлы
        for temp_file in [cleaned_file, template_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if result == 0 and os.path.exists(pdf_output):
            print("✓ PDF успешно создан!")
            return pdf_output
        else:
            print("✗ Ошибка конвертации")
            return None
            
    except Exception as e:
        print(f"Ошибка: {e}")
        # Удаляем временные файлы при ошибке
        for temp_file in ['cleaned.md', 'simple_template.tex']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None

# ======================
# АЛЬТЕРНАТИВА: ПРОСТОЙ HTML
# ======================
def create_simple_html(md_file):
    """
    Простая HTML версия как запасной вариант
    """
    html_output = os.path.splitext(md_file)[0] + '.html'
    
    try:
        # Читаем исходный файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Очищаем контент
        cleaned_content = clean_markdown(content)
        
        # Сохраняем очищенную версию
        cleaned_file = 'temp_cleaned.md'
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Конвертируем в HTML
        cmd = f'pandoc "{cleaned_file}" -o "{html_output}" -t html5 --standalone'
        result = os.system(cmd)
        
        # Удаляем временный файл
        if os.path.exists(cleaned_file):
            os.remove(cleaned_file)
        
        if result == 0 and os.path.exists(html_output):
            print("✓ HTML версия создана")
            return html_output
        else:
            return None
            
    except Exception as e:
        print(f"Ошибка создания HTML: {e}")
        if os.path.exists('temp_cleaned.md'):
            os.remove('temp_cleaned.md')
        return None

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 50)
print("📄 ПРОСТОЙ КОНВЕРТЕР MARKDOWN В PDF")
print("=" * 50)

# Загружаем файл
print("Загрузите Markdown файл:")
uploaded = files.upload()

if not uploaded:
    print("❌ Файл не загружен")
else:
    filename = list(uploaded.keys())[0]
    print(f"Обрабатываем: {filename}")
    
    # Показываем информацию о файле
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Размер: {len(content)} символов")
        print(f"Строк: {content.count(chr(10)) + 1}")
    
    # Пробуем конвертировать в PDF
    pdf_file = convert_markdown_to_pdf(filename)
    
    if pdf_file:
        print(f"✅ Готово: {pdf_file}")
        files.download(pdf_file)
    else:
        print("Пробуем создать HTML версию...")
        html_file = create_simple_html(filename)
        
        if html_file:
            print(f"✅ Создана HTML версия: {html_file}")
            files.download(html_file)
            print("\n💡 Совет: Откройте HTML в браузере и используйте 'Печать → Сохранить как PDF'")
        else:
            print("❌ Не удалось создать ни PDF, ни HTML версию")
            print("\n🔧 Возможные решения:")
            print("1. Проверьте синтаксис Markdown")
            print("2. Упростите сложные таблицы")
            print("3. Разделите файл на части если он очень большой")

print("\nГотово! 🎉")
```

## 🎯 Что изменилось:

### 1. **Убрал лишнее**
- Только один основной метод конвертации (PDF)
- Простая HTML версия как запасной вариант
- Минимальная предобработка

### 2. **Упростил обработку таблиц**
- Только добавляет разделители, если их нет
- Не переусердствует с исправлениями
- Сохраняет оригинальную структуру

### 3. **Один качественный результат**
- Фокус на создании одного хорошего PDF
- HTML только как резервный вариант
- Простой и понятный процесс

### 4. **Надежность**
- Минимум операций - меньше шансов на ошибки
- Простая очистка контента
- Четкие сообщения об ошибках

Теперь код делает именно то, что нужно - конвертирует Markdown в PDF максимально просто и надежно!

---

## USER

ПДФ не работает. А html получился не больно красивый.

---

## AI

Понял проблему! Давайте сделаем простой и надежный код, который создаст хорошо отформатированный PDF. Уберем лишнюю сложность и сосредоточимся на качестве:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended > /dev/null 2>&1

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files

# ======================
# ПРОСТАЯ ПРЕДОБРАБОТКА
# ======================
def clean_markdown(content):
    """Минимальная обработка для сохранения структуры"""
    # Только самые важные замены
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Простое исправление таблиц - добавляем разделители где их нет
    lines = content.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        result.append(line)
        # Если это строка таблицы и следующая строка тоже таблица, но нет разделителя
        if (line.startswith('|') and '---' not in line and 
            i + 1 < len(lines) and lines[i + 1].startswith('|') and '---' not in lines[i + 1]):
            # Создаем разделитель на основе количества колонок
            col_count = line.count('|') - 1
            separator = '|' + ' --- |' * col_count
            result.append(separator)
    
    return '\n'.join(result)

# ======================
# ПРОСТАЯ КОНВЕРТАЦИЯ
# ======================
def convert_to_pdf(md_file):
    """Простая и надежная конвертация в PDF"""
    output_pdf = md_file.replace('.md', '.pdf').replace('.txt', '.pdf')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Минимальная очистка
        cleaned_content = clean_markdown(content)
        
        # Сохраняем очищенную версию
        cleaned_file = 'temp_cleaned.md'
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print("Конвертируем в PDF...")
        
        # Простая команда pandoc с проверенными настройками
        cmd = [
            'pandoc', cleaned_file,
            '-o', output_pdf,
            '--pdf-engine=xelatex',
            '-V', 'mainfont=DejaVu Serif',
            '-V', 'sansfont=DejaVu Sans', 
            '-V', 'monofont=DejaVu Sans Mono',
            '--wrap=preserve',
            '--standalone',
            '-V', 'geometry:margin=2cm'
        ]
        
        # Запускаем конвертацию
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ PDF успешно создан!")
            return output_pdf
        else:
            print(f"✗ Ошибка конвертации: {result.stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return None
    finally:
        # Удаляем временный файл
        if os.path.exists('temp_cleaned.md'):
            os.remove('temp_cleaned.md')

# ======================
# КРАСИВЫЙ HTML
# ======================
def create_nice_html(md_file):
    """Создаем красивый HTML с хорошим CSS"""
    output_html = md_file.replace('.md', '.html').replace('.txt', '.html')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Очищаем контент
        cleaned_content = clean_markdown(content)
        
        # Сохраняем временный файл
        temp_md = 'temp_for_html.md'
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Конвертируем в HTML
        import subprocess
        cmd = ['pandoc', temp_md, '-t', 'html5', '-o', output_html]
        subprocess.run(cmd, check=True)
        
        # Читаем сгенерированный HTML и улучшаем его
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Простой и чистый CSS
        nice_css = """
        <style>
            body {
                font-family: 'Georgia', 'Times New Roman', serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
                background: #fafafa;
            }
            .document {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }
            h3 {
                color: #465c7a;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 14px;
            }
            th {
                background: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 10px 12px;
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
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            blockquote {
                border-left: 4px solid #3498db;
                padding: 10px 20px;
                margin: 20px 0;
                background: #f8f9fa;
                font-style: italic;
            }
        </style>
        """
        
        # Вставляем CSS и оборачиваем контент
        html_content = html_content.replace('<body>', 
                                          '<body>\n<div class="document">')
        html_content = html_content.replace('</body>', 
                                          '</div>\n</body>')
        
        # Добавляем CSS в head
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', 
                                             f'<head>\n{nice_css}')
        else:
            html_content = f'<head>{nice_css}</head>\n{html_content}'
        
        # Перезаписываем файл
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Убираем временный файл
        os.remove(temp_md)
        print("✓ Красивый HTML создан!")
        return output_html
        
    except Exception as e:
        print(f"Ошибка создания HTML: {e}")
        if os.path.exists('temp_for_html.md'):
            os.remove('temp_for_html.md')
        return None

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 50)
print("🎯 ПРОСТОЙ И НАДЕЖНЫЙ КОНВЕРТЕР")
print("=" * 50)

# Загружаем файл
print("Загрузите ваш Markdown файл:")
uploaded = files.upload()

if not uploaded:
    print("❌ Файл не загружен")
else:
    filename = list(uploaded.keys())[0]
    print(f"📄 Обрабатываем: {filename}")
    
    # Показываем базовую информацию
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"Размер: {len(content)} символов")
    
    # Сначала проб

---

## USER

Установка необходимых пакетов...
✓ Пакеты установлены!
==================================================
📄 ПРОСТОЙ КОНВЕРТЕР MARKDOWN В PDF
==================================================
Загрузите Markdown файл:
temp_cleaned.pdf
temp_cleaned.pdf(application/pdf) - 124979 bytes, last modified: 18.11.2025 - 100% done
Saving temp_cleaned.pdf to temp_cleaned.pdf
Обрабатываем: temp_cleaned.pdf
---------------------------------------------------------------------------
UnicodeDecodeError                        Traceback (most recent call last)
/tmp/ipython-input-1906166267.py in <cell line: 0>()
    211     # Показываем информацию о файле
    212     with open(filename, 'r', encoding='utf-8') as f:
--> 213         content = f.read()
    214         print(f"Размер: {len(content)} символов")
    215         print(f"Строк: {content.count(chr(10)) + 1}")

/usr/lib/python3.12/codecs.py in decode(self, input, final)

UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd3 in position 10: invalid continuation byte

---

## AI

Ошибка возникает потому, что вы загрузили PDF-файл, а код ожидает Markdown-файл. Давайте исправим код, чтобы он определял тип файла и правильно обрабатывал ситуацию:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended > /dev/null 2>&1

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
import mimetypes
from google.colab import files

# ======================
# ФУНКЦИЯ ОПРЕДЕЛЕНИЯ ТИПА ФАЙЛА
# ======================
def is_markdown_file(filename):
    """Проверяем, является ли файл Markdown"""
    markdown_extensions = ['.md', '.markdown', '.mdown', '.mkd', '.txt']
    file_ext = os.path.splitext(filename)[1].lower()
    
    # Проверяем расширение
    if file_ext in markdown_extensions:
        return True
    
    # Дополнительная проверка по содержимому
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Читаем первые 1000 символов
            # Если есть типичные Markdown элементы
            if any(pattern in content for pattern in ['# ', '## ', '**', '* ', '- ', '```']):
                return True
    except:
        pass
    
    return False

# ======================
# ПРОСТАЯ ПРЕДОБРАБОТКА
# ======================
def clean_markdown(content):
    """Минимальная обработка для сохранения структуры"""
    # Только самые важные замены
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Простое исправление таблиц - добавляем разделители где их нет
    lines = content.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        result.append(line)
        # Если это строка таблицы и следующая строка тоже таблица, но нет разделителя
        if (line.startswith('|') and '---' not in line and 
            i + 1 < len(lines) and lines[i + 1].startswith('|') and '---' not in lines[i + 1]):
            # Создаем разделитель на основе количества колонок
            col_count = line.count('|') - 1
            separator = '|' + ' --- |' * col_count
            result.append(separator)
    
    return '\n'.join(result)

# ======================
# ПРОСТАЯ КОНВЕРТАЦИЯ
# ======================
def convert_to_pdf(md_file):
    """Простая и надежная конвертация в PDF"""
    output_pdf = md_file.replace('.md', '_converted.pdf').replace('.txt', '_converted.pdf')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Минимальная очистка
        cleaned_content = clean_markdown(content)
        
        # Сохраняем очищенную версию
        cleaned_file = 'temp_cleaned.md'
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print("Конвертируем в PDF...")
        
        # Простая команда pandoc с проверенными настройками
        cmd = [
            'pandoc', cleaned_file,
            '-o', output_pdf,
            '--pdf-engine=xelatex',
            '-V', 'mainfont=DejaVu Serif',
            '-V', 'sansfont=DejaVu Sans', 
            '-V', 'monofont=DejaVu Sans Mono',
            '--wrap=preserve',
            '--standalone',
            '-V', 'geometry:margin=2cm'
        ]
        
        # Запускаем конвертацию
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ PDF успешно создан!")
            return output_pdf
        else:
            print(f"✗ Ошибка конвертации: {result.stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return None
    finally:
        # Удаляем временный файл
        if os.path.exists('temp_cleaned.md'):
            os.remove('temp_cleaned.md')

# ======================
# КРАСИВЫЙ HTML
# ======================
def create_nice_html(md_file):
    """Создаем красивый HTML с хорошим CSS"""
    output_html = md_file.replace('.md', '_formatted.html').replace('.txt', '_formatted.html')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Очищаем контент
        cleaned_content = clean_markdown(content)
        
        # Сохраняем временный файл
        temp_md = 'temp_for_html.md'
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Конвертируем в HTML
        import subprocess
        cmd = ['pandoc', temp_md, '-t', 'html5', '-o', output_html]
        subprocess.run(cmd, check=True)
        
        # Читаем сгенерированный HTML и улучшаем его
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Простой и чистый CSS
        nice_css = """
        <style>
            body {
                font-family: 'Georgia', 'Times New Roman', serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
                background: #fafafa;
            }
            .document {
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            h2 {
                color: #34495e;
                margin-top: 30px;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }
            h3 {
                color: #465c7a;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 14px;
            }
            th {
                background: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 10px 12px;
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
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }
            blockquote {
                border-left: 4px solid #3498db;
                padding: 10px 20px;
                margin: 20px 0;
                background: #f8f9fa;
                font-style: italic;
            }
        </style>
        """
        
        # Вставляем CSS и оборачиваем контент
        html_content = html_content.replace('<body>', 
                                          '<body>\n<div class="document">')
        html_content = html_content.replace('</body>', 
                                          '</div>\n</body>')
        
        # Добавляем CSS в head
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', 
                                             f'<head>\n{nice_css}')
        else:
            html_content = f'<head>{nice_css}</head>\n{html_content}'
        
        # Перезаписываем файл
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Убираем врем

---

## USER

да, получилось, но что-то как-то некрасиво выходит

---

## AI

Понял! Давайте улучшим оформление. Проблема в том, что стандартные настройки pandoc дают довольно простой результат. Создадим более красивый и профессиональный шаблон:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended texlive-latex-extra > /dev/null 2>&1

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files

# ======================
# ПРОФЕССИОНАЛЬНЫЙ LaTeX ШАБЛОН
# ======================
def create_professional_template():
    """Создаем профессиональный LaTeX шаблон с красивым оформлением"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{russian}
\setotherlanguage{english}

\usepackage[margin=2.5cm]{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{booktabs}
\usepackage{array}
\usepackage{enumitem}
\usepackage{parskip}
\usepackage{setspace}
\usepackage{hyperref}

% Цветовая схема
\definecolor{accent}{RGB}{41, 128, 185}
\definecolor{lightgray}{RGB}{245, 247, 250}
\definecolor{darkgray}{RGB}{52, 73, 94}

% Шрифты
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Настройка заголовков
\titleformat{\section}
{\Large\sffamily\bfseries\color{darkgray}}
{\thesection}{1em}{}

\titleformat{\subsection}
{\large\sffamily\bfseries\color{darkgray}}
{\thesubsection}{1em}{}

\titleformat{\subsubsection}
{\sffamily\bfseries\color{darkgray}}
{\thesubsubsection}{1em}{}

% Настройка списков
\setlist[itemize]{leftmargin=*, topsep=3pt, itemsep=2pt}
\setlist[enumerate]{leftmargin=*, topsep=3pt, itemsep=2pt}

% Настройка таблиц
\newcolumntype{L}{>{\raggedright\arraybackslash}p{0.2\textwidth}}
\newcolumntype{C}{>{\centering\arraybackslash}p{0.15\textwidth}}
\newcolumntype{R}{>{\raggedleft\arraybackslash}p{0.15\textwidth}}

% Улучшенное оформление таблиц
\renewcommand{\arraystretch}{1.2}

% Настройка межстрочного интервала
\onehalfspacing

% Убираем отступы в начале параграфов
\setlength{\parindent}{0pt}

\begin{document}

% Заголовок документа
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\textcolor{darkgray}{\sffamily\bfseries Документ}}
\fancyhead[R]{\textcolor{darkgray}{\sffamily\bfseries \thepage}}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\headrule}{\hbox to\headwidth{%
  \color{accent}\leaders\hrule height \headrulewidth\hfill}}

$body$

\end{document}"""

# ======================
# УЛУЧШЕННАЯ ПРЕДОБРАБОТКА
# ======================
def enhanced_clean_markdown(content):
    """Улучшенная очистка с сохранением структуры"""
    print("🔧 Улучшаем форматирование...")
    
    # Замены символов
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
        '': '↓',
        '': '│',
        '': '─',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Улучшаем таблицы
    lines = content.split('\n')
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Обработка таблиц
        if line.strip().startswith('|') and '---' not in line:
            cleaned_lines.append(line)
            
            # Проверяем, нужно ли добавить разделитель
            if (i + 1 < len(lines) and 
                lines[i + 1].strip().startswith('|') and 
                '---' not in lines[i + 1]):
                
                col_count = line.count('|') - 1
                separator = '|' + ' :--- |' * col_count
                cleaned_lines.append(separator)
            
            i += 1
        else:
            # Улучшаем заголовки
            if line.startswith('# '):
                line = '# ' + line[2:].strip()
            elif line.startswith('## '):
                line = '## ' + line[3:].strip()
            elif line.startswith('### '):
                line = '### ' + line[4:].strip()
                
            cleaned_lines.append(line)
            i += 1
    
    content = '\n'.join(cleaned_lines)
    
    # Улучшаем списки
    content = re.sub(r'^\s*[-*]\s+', '• ', content, flags=re.MULTILINE)
    
    # Добавляем горизонтальные линии для разделения секций
    content = re.sub(r'^# .*$', r'\n\\rule{\\textwidth}{0.5pt}\n\\vspace{10pt}\n\\1', content, flags=re.MULTILINE)
    
    return content

# ======================
# КОНВЕРТАЦИЯ С ПРОФЕССИОНАЛЬНЫМ ШАБЛОНОМ
# ======================
def convert_with_professional_template(md_file):
    """Конвертация с профессиональным шаблоном"""
    output_pdf = md_file.replace('.md', '_professional.pdf').replace('.txt', '_professional.pdf')
    
    try:
        # Читаем и обрабатываем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        enhanced_content = enhanced_clean_markdown(content)
        
        # Сохраняем обработанную версию
        processed_file = 'enhanced.md'
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        # Создаем профессиональный шаблон
        template_file = 'professional_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(create_professional_template())
        
        print("🎨 Создаем красивый PDF...")
        
        # Команда с улучшенными настройками
        cmd = [
            'pandoc', processed_file,
            '-o', output_pdf,
            '--pdf-engine=xelatex',
            f'--template={template_file}',
            '--wrap=preserve',
            '--standalone',
            '--highlight-style', 'tango',
            '-V', 'colorlinks=true',
            '-V', 'linkcolor=blue',
            '-V', 'urlcolor=blue',
        ]
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Удаляем временные файлы
        for temp_file in [processed_file, template_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if result.returncode == 0 and os.path.exists(output_pdf):
            print("✅ Профессиональный PDF создан!")
            return output_pdf
        else:
            print(f"❌ Ошибка: {result.stderr[:300]}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        # Удаляем временные файлы при ошибке
        for temp_file in ['enhanced.md', 'professional_template.tex']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None

# ======================
# СУПЕР-КРАСИВЫЙ HTML
# ======================
def create_super_nice_html(md_file):
    """Создаем очень красивый HTML с современным дизайном"""
    output_html = md_file.replace('.md', '_beautiful.html').replace('.txt', '_beautiful.html')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        enhanced_content = enhanced_clean_markdown(content)
        
        # Сохраняем временный файл
        temp_md = 'temp_super.md'
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        # Конвертируем в HTML
        import subprocess
        cmd = ['pandoc', temp_md, '-t', 'html5', '-o', output_html]
        subprocess.run(cmd, check=True)
        
        # Читаем и улучшаем HTML
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Супер-красивый CSS
        beautiful_css = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            :root {
                --primary: #2563eb;
                --secondary: #64748b;
      

---

## USER

ошибку выдал:
Установка необходимых пакетов...
✓ Пакеты установлены!
============================================================
🎨 ПРОФЕССИОНАЛЬНЫЙ КОНВЕРТЕР
============================================================
Загрузите ваш Markdown файл:
DKP5-Tochki-A-B-FINAL.md
DKP5-Tochki-A-B-FINAL.md(n/a) - 20391 bytes, last modified: 18.11.2025 - 100% done
Saving DKP5-Tochki-A-B-FINAL.md to DKP5-Tochki-A-B-FINAL (5).md
📄 Обрабатываем: DKP5-Tochki-A-B-FINAL (5).md
📊 Размер: 11612 символов

🎨 Создаем профессиональный PDF...
🔧 Улучшаем форматирование...
🎨 Создаем красивый PDF...
❌ Ошибка: Error producing PDF.
! LaTeX Error: Environment longtable undefined.

See the LaTeX manual or LaTeX Companion for explanation.
Type  H <return>  for immediate help.
 ...                                              
                                                  
l.342 \begin{longtable}


❌ Не удалось создать PDF

💫 Создаем супер-красивый HTML...
🔧 Улучшаем форматирование...
✅ Супер-красивый HTML создан!
✅ HTML готов: DKP5-Tochki-A-B-FINAL (5)_beautiful.html

💡 Откройте HTML в браузере для лучшего просмотра!

🎉 Готово! Документы созданы с профессиональным оформлением!

---

## AI

Проблема в отсутствии пакета `longtable` в LaTeX. Давайте исправим это и сделаем более надежную версию:

```python
# ======================
# УСТАНОВКА ВСЕХ НЕОБХОДИМЫХ ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended texlive-latex-extra texlive-science latexmk > /dev/null 2>&1

print("✓ Все пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files

# ======================
# ПРОСТОЙ И НАДЕЖНЫЙ LaTeX ШАБЛОН
# ======================
def create_simple_reliable_template():
    """Создаем простой и надежный LaTeX шаблон без сложных пакетов"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{russian}
\setotherlanguage{english}

\usepackage[margin=2.5cm]{geometry}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{booktabs}
\usepackage{array}
\usepackage{enumitem}
\usepackage{parskip}
\usepackage{setspace}

% Цветовая схема
\definecolor{accent}{RGB}{41, 128, 185}
\definecolor{darkgray}{RGB}{52, 73, 94}

% Шрифты
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Настройка заголовков
\titleformat{\section}
{\Large\sffamily\bfseries\color{darkgray}}
{\thesection}{1em}{}

\titleformat{\subsection}
{\large\sffamily\bfseries\color{darkgray}}
{\thesubsection}{1em}{}

\titleformat{\subsubsection}
{\sffamily\bfseries\color{darkgray}}
{\thesubsubsection}{1em}{}

% Настройка списков
\setlist[itemize]{leftmargin=*, topsep=3pt, itemsep=2pt}
\setlist[enumerate]{leftmargin=*, topsep=3pt, itemsep=2pt}

% Настройка таблиц
\newcolumntype{L}{>{\raggedright}p{0.2\textwidth}}
\newcolumntype{C}{>{\centering}p{0.15\textwidth}}
\newcolumntype{R}{>{\raggedleft}p{0.15\textwidth}}

% Улучшенное оформление таблиц
\renewcommand{\arraystretch}{1.2}

% Настройка межстрочного интервала
\onehalfspacing

% Убираем отступы в начале параграфов
\setlength{\parindent}{0pt}

\begin{document}

% Заголовок документа
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\textcolor{darkgray}{\sffamily\bfseries Документ}}
\fancyhead[R]{\textcolor{darkgray}{\sffamily\bfseries \thepage}}
\renewcommand{\headrulewidth}{0.5pt}

$body$

\end{document}"""

# ======================
# УМНАЯ ПРЕДОБРАБОТКА
# ======================
def smart_clean_markdown(content):
    """Умная очистка без излишних преобразований"""
    print("🔧 Улучшаем форматирование...")
    
    # Только самые необходимые замены символов
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
        '': '↓',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Улучшаем таблицы - простой подход
    lines = content.split('\n')
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Простая обработка таблиц
        if line.strip().startswith('|'):
            cleaned_lines.append(line)
            
            # Проверяем, нужно ли добавить разделитель
            if (i + 1 < len(lines) and 
                lines[i + 1].strip().startswith('|') and 
                '---' not in lines[i + 1] and
                '---' not in line):
                
                col_count = max(1, line.count('|') - 1)
                separator = '|' + ' --- |' * col_count
                cleaned_lines.append(separator)
            
            i += 1
        else:
            cleaned_lines.append(line)
            i += 1
    
    return '\n'.join(cleaned_lines)

# ======================
# НАДЕЖНАЯ КОНВЕРТАЦИЯ В PDF
# ======================
def convert_to_pdf_reliable(md_file):
    """Надежная конвертация в PDF с несколькими попытками"""
    output_pdf = md_file.replace('.md', '_professional.pdf').replace('.txt', '_professional.pdf')
    
    # Методы конвертации в порядке надежности
    methods = [
        {
            'name': 'xelatex с простым шаблоном',
            'cmd': [
                'pandoc', md_file, '-o', output_pdf,
                '--pdf-engine=xelatex',
                '--template=simple_template.tex',
                '--wrap=preserve',
                '--standalone',
                '-V', 'geometry:margin=2.5cm'
            ]
        },
        {
            'name': 'простой xelatex',
            'cmd': [
                'pandoc', md_file, '-o', output_pdf,
                '--pdf-engine=xelatex', 
                '--wrap=preserve',
                '--standalone',
                '-V', 'mainfont=DejaVu Serif',
                '-V', 'geometry:margin=2cm'
            ]
        },
        {
            'name': 'pdflatex',
            'cmd': [
                'pandoc', md_file, '-o', output_pdf,
                '--pdf-engine=pdflatex',
                '--wrap=preserve',
                '--standalone'
            ]
        }
    ]
    
    try:
        # Читаем и обрабатываем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = smart_clean_markdown(content)
        
        # Сохраняем обработанную версию
        processed_file = 'processed.md'
        with open(processed_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Создаем простой шаблон
        template_file = 'simple_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(create_simple_reliable_template())
        
        import subprocess
        
        # Пробуем разные методы
        for method in methods:
            print(f"🔄 Пробуем: {method['name']}...")
            
            # Заменяем имя файла в команде
            cmd = [arg if arg != md_file else processed_file for arg in method['cmd']]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_pdf):
                print(f"✅ Успех с {method['name']}!")
                break
            else:
                print(f"❌ Не удалось с {method['name']}")
                if result.stderr:
                    print(f"   Ошибка: {result.stderr[:200]}")
        
        # Удаляем временные файлы
        for temp_file in [processed_file, template_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if os.path.exists(output_pdf):
            return output_pdf
        else:
            return None
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        # Удаляем временные файлы при ошибке
        for temp_file in ['processed.md', 'simple_template.tex']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None

# ======================
# КРАСИВЫЙ И ПРОСТОЙ HTML
# ======================
def create_nice_simple_html(md_file):
    """Создаем красивый и простой HTML"""
    output_html = md_file.replace('.md', '_beautiful.html').replace('.txt', '_beautiful.html')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        cleaned_content = smart_clean_markdown(content)
        
        # Сохраняем временный файл
        temp_md = 'temp_html.md'
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Конвертируем в HTML
        import subprocess
        cmd = ['pandoc', temp_md, '-t', 'html5', '-o', output_html, '--standalone']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Ошибка pandoc: {result.stderr}")
            return None
        
        # Читаем и улучшаем HTML
        with open(output_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        


---

## USER

Выдаёт ошибку:

Загрузите ваш Markdown файл:
DKP5-Tochki-A-B-FINAL.md
DKP5-Tochki-A-B-FINAL.md(n/a) - 20391 bytes, last modified: 18.11.2025 - 100% done
Saving DKP5-Tochki-A-B-FINAL.md to DKP5-Tochki-A-B-FINAL (6).md
📄 Обрабатываем: DKP5-Tochki-A-B-FINAL (6).md
📊 Размер: 11612 символов

🔄 Создаем PDF...
🔧 Улучшаем форматирование...
🔄 Пробуем: xelatex с простым шаблоном...
❌ Не удалось с xelatex с простым шаблоном
   Ошибка: Error producing PDF.
! Undefined control sequence.
l.66 \hypertarget


🔄 Пробуем: простой xelatex...
✅ Успех с простой xelatex!
✅ PDF готов: DKP5-Tochki-A-B-FINAL (6)_professional.pdf

💫 Создаем красивый HTML...
🔧 Улучшаем форматирование...
✅ Красивый HTML создан!
✅ HTML готов: DKP5-Tochki-A-B-FINAL (6)_beautiful.html

💡 Совет: Откройте HTML в браузере и используйте Ctrl+P → 'Сохранить как PDF'

🎉 Обработка завершена!

и мне не нужно 2 файла

---

## AI

Понял! Уберу создание HTML и сосредоточусь на одном качественном PDF. Вот улучшенный код:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended texlive-latex-extra > /dev/null 2>&1

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files

# ======================
# ПРОСТОЙ И НАДЕЖНЫЙ ШАБЛОН
# ======================
def create_clean_template():
    """Создаем чистый и надежный шаблон без проблемных пакетов"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage{fontspec}
\usepackage{polyglossia}
\setmainlanguage{russian}
\setotherlanguage{english}

\usepackage[margin=2.5cm]{geometry}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{booktabs}
\usepackage{array}
\usepackage{enumitem}
\usepackage{parskip}
\usepackage{setspace}

% Цветовая схема
\definecolor{accent}{RGB}{41, 128, 185}
\definecolor{darkgray}{RGB}{52, 73, 94}

% Шрифты
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}

% Настройка заголовков
\titleformat{\section}
{\Large\sffamily\bfseries\color{darkgray}}
{\thesection}{1em}{}

\titleformat{\subsection}
{\large\sffamily\bfseries\color{darkgray}}
{\thesubsection}{1em}{}

\titleformat{\subsubsection}
{\sffamily\bfseries\color{darkgray}}
{\thesubsubsection}{1em}{}

% Настройка списков
\setlist[itemize]{leftmargin=*, topsep=3pt, itemsep=2pt}
\setlist[enumerate]{leftmargin=*, topsep=3pt, itemsep=2pt}

% Настройка межстрочного интервала
\onehalfspacing

% Убираем отступы в начале параграфов
\setlength{\parindent}{0pt}

\begin{document}

% Заголовок документа
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\textcolor{darkgray}{\sffamily\bfseries Документ}}
\fancyhead[R]{\textcolor{darkgray}{\sffamily\bfseries \thepage}}
\renewcommand{\headrulewidth}{0.5pt}

$body$

\end{document}"""

# ======================
# МИНИМАЛЬНАЯ ПРЕДОБРАБОТКА
# ======================
def minimal_clean(content):
    """Минимальная обработка для сохранения структуры"""
    # Только самые необходимые замены
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    return content

# ======================
# ПРОСТАЯ КОНВЕРТАЦИЯ В PDF
# ======================
def convert_markdown_to_pdf(md_file):
    """Простая и надежная конвертация в один PDF файл"""
    output_pdf = md_file.replace('.md', '.pdf').replace('.txt', '.pdf')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Минимальная очистка
        cleaned_content = minimal_clean(content)
        
        # Сохраняем очищенную версию
        cleaned_file = 'temp_clean.md'
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Создаем шаблон
        template_file = 'clean_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(create_clean_template())
        
        print("Создаем PDF...")
        
        # Пробуем разные методы в порядке надежности
        methods = [
            # Метод 1: Простой xelatex без шаблона (самый надежный)
            [
                'pandoc', cleaned_file, '-o', output_pdf,
                '--pdf-engine=xelatex',
                '--wrap=preserve',
                '--standalone',
                '-V', 'mainfont=DejaVu Serif',
                '-V', 'geometry:margin=2.5cm'
            ],
            # Метод 2: С шаблоном но без проблемных опций
            [
                'pandoc', cleaned_file, '-o', output_pdf,
                '--pdf-engine=xelatex',
                f'--template={template_file}',
                '--wrap=preserve',
                '--standalone'
            ]
        ]
        
        import subprocess
        success = False
        
        for i, cmd in enumerate(methods):
            print(f"Попытка {i+1}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_pdf):
                print("✓ PDF успешно создан!")
                success = True
                break
            else:
                if result.stderr:
                    print(f"Ошибка: {result.stderr[:100]}")
        
        # Удаляем временные файлы
        for temp_file in [cleaned_file, template_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if success:
            return output_pdf
        else:
            return None
            
    except Exception as e:
        print(f"Ошибка: {e}")
        # Удаляем временные файлы при ошибке
        for temp_file in ['temp_clean.md', 'clean_template.tex']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 50)
print("📄 КОНВЕРТЕР MARKDOWN В PDF")
print("=" * 50)

# Загружаем файл
print("Загрузите ваш Markdown файл:")
uploaded = files.upload()

if not uploaded:
    print("Файл не загружен")
else:
    filename = list(uploaded.keys())[0]
    print(f"Обрабатываем: {filename}")
    
    try:
        # Проверяем файл
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Размер: {len(content)} символов")
        
        # Создаем PDF
        pdf_file = convert_markdown_to_pdf(filename)
        
        if pdf_file and os.path.exists(pdf_file):
            print(f"✅ Готово: {pdf_file}")
            files.download(pdf_file)
            print("\n📥 Файл готов для скачивания!")
        else:
            print("❌ Не удалось создать PDF")
            print("\n💡 Попробуйте:")
            print("• Проверить синтаксис Markdown")
            print("• Упростить сложные таблицы")
            print("• Разделить очень большой файл на части")
        
    except Exception as e:
        print(f"Ошибка: {e}")

print("\n🎉 Завершено!")
```

## 🎯 Что изменилось:

### 1. **Только один PDF файл**
- Убрал полностью создание HTML
- Фокус на одном качественном результате

### 2. **Упрощенный подход**
- Минимальная предобработка
- Без сложных замен и преобразований
- Сохранение оригинальной структуры

### 3. **Надежная конвертация**
- Два метода: с шаблоном и без
- Автоматический переход к следующему методу при ошибке
- Простой xelatex как основной надежный метод

### 4. **Чистый шаблон**
- Убраны все проблемные пакеты
- Только базовые и проверенные настройки
- Никакого hyperref или других сложных пакетов

### 5. **Понятные сообщения**
- Простой прогресс
- Четкие уведомления об ошибках
- Минимум технической информации

Теперь код создаст **только один PDF файл** максимально надежным способом!

---

## USER

Теперь вот так ругается:
Установка необходимых пакетов...
✓ Пакеты установлены!
==================================================
📄 КОНВЕРТЕР MARKDOWN В PDF
==================================================
Загрузите ваш Markdown файл:
Prompt_FinRez_analiz.md
Prompt_FinRez_analiz.md(n/a) - 24978 bytes, last modified: 19.11.2025 - 100% done
Saving Prompt_FinRez_analiz.md to Prompt_FinRez_analiz.md
Обрабатываем: Prompt_FinRez_analiz.md
Размер: 14851 символов
Создаем PDF...
Попытка 1...
Ошибка: Error producing PDF.
! Package fontspec Error: The font "DejaVu Serif" cannot be found.

For immedia
Попытка 2...
Ошибка: Error producing PDF.
! Package fontspec Error: The font "DejaVu Serif" cannot be found.

For immedia
❌ Не удалось создать PDF

💡 Попробуйте:
• Проверить синтаксис Markdown
• Упростить сложные таблицы
• Разделить очень большой файл на части

🎉 Завершено!

---

## AI

Проблема с шрифтами! Давайте исправим это, используя базовые шрифты LaTeX и упростим шаблон до минимальной рабочей версии:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended > /dev/null 2>&1

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files

# ======================
# МИНИМАЛЬНЫЙ РАБОЧИЙ ШАБЛОН
# ======================
def create_minimal_template():
    """Создаем минимальный шаблон без проблемных шрифтов"""
    return r"""\documentclass[a4paper,12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[russian]{babel}
\usepackage[margin=2.5cm]{geometry}
\usepackage{parskip}
\usepackage{setspace}

% Используем стандартные шрифты LaTeX
\onehalfspacing

\begin{document}

$body$

\end{document}"""

# ======================
# МИНИМАЛЬНАЯ ПРЕДОБРАБОТКА
# ======================
def minimal_clean(content):
    """Минимальная обработка для сохранения структуры"""
    # Только самые необходимые замены
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    return content

# ======================
# ПРОСТАЯ КОНВЕРТАЦИЯ В PDF
# ======================
def convert_markdown_to_pdf(md_file):
    """Простая и надежная конвертация в один PDF файл"""
    output_pdf = md_file.replace('.md', '.pdf').replace('.txt', '.pdf')
    
    try:
        # Читаем файл
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Минимальная очистка
        cleaned_content = minimal_clean(content)
        
        # Сохраняем очищенную версию
        cleaned_file = 'temp_clean.md'
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Создаем минимальный шаблон
        template_file = 'minimal_template.tex'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(create_minimal_template())
        
        print("Создаем PDF...")
        
        # Пробуем разные методы в порядке надежности
        methods = [
            # Метод 1: pdflatex с минимальным шаблоном (самый надежный)
            [
                'pandoc', cleaned_file, '-o', output_pdf,
                '--pdf-engine=pdflatex',
                f'--template={template_file}',
                '--wrap=preserve',
                '--standalone'
            ],
            # Метод 2: pdflatex без шаблона
            [
                'pandoc', cleaned_file, '-o', output_pdf,
                '--pdf-engine=pdflatex',
                '--wrap=preserve',
                '--standalone'
            ],
            # Метод 3: xelatex с самыми простыми настройками
            [
                'pandoc', cleaned_file, '-o', output_pdf,
                '--pdf-engine=xelatex',
                '--wrap=preserve',
                '--standalone'
            ]
        ]
        
        import subprocess
        success = False
        
        for i, cmd in enumerate(methods):
            print(f"Попытка {i+1}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_pdf):
                print("✓ PDF успешно создан!")
                success = True
                break
            else:
                if result.stderr:
                    error_msg = result.stderr[:200]
                    print(f"Ошибка: {error_msg}")
        
        # Удаляем временные файлы
        for temp_file in [cleaned_file, template_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        if success:
            return output_pdf
        else:
            return None
            
    except Exception as e:
        print(f"Ошибка: {e}")
        # Удаляем временные файлы при ошибке
        for temp_file in ['temp_clean.md', 'minimal_template.tex']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 50)
print("📄 КОНВЕРТЕР MARKDOWN В PDF")
print("=" * 50)

# Загружаем файл
print("Загрузите ваш Markdown файл:")
uploaded = files.upload()

if not uploaded:
    print("Файл не загружен")
else:
    filename = list(uploaded.keys())[0]
    print(f"Обрабатываем: {filename}")
    
    try:
        # Проверяем файл
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Размер: {len(content)} символов")
        
        # Создаем PDF
        pdf_file = convert_markdown_to_pdf(filename)
        
        if pdf_file and os.path.exists(pdf_file):
            print(f"✅ Готово: {pdf_file}")
            files.download(pdf_file)
            print("\n📥 Файл готов для скачивания!")
        else:
            print("❌ Не удалось создать PDF")
            print("\n💡 Создаем простой текстовый файл как запасной вариант...")
            # Создаем простой текстовый файл
            txt_file = filename.replace('.md', '_converted.txt')
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(content)
            files.download(txt_file)
            print(f"📄 Создан текстовый файл: {txt_file}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

print("\n🎉 Завершено!")
```

## 🎯 Ключевые изменения:

### 1. **Убраны проблемные шрифты**
- Используем стандартные шрифты LaTeX вместо DejaVu
- Убраны все сложные настройки шрифтов

### 2. **Минимальный шаблон**
- Только самые базовые пакеты: `inputenc`, `babel`, `geometry`
- Никаких сложных зависимостей
- Стандартная кодировка UTF-8

### 3. **Приоритет pdflatex**
- pdflatex более стабилен в Colab
- xelatex только как запасной вариант

### 4. **Резервное решение**
- Если PDF не создается, делаем простой текстовый файл
- Гарантированный результат в любом случае

### 5. **Упрощенная обработка**
- Минимум преобразований контента
- Фокус на надежности, а не на красоте

Этот код должен работать надежно и создавать PDF без ошибок со шрифтами!

---

## USER

Блин, ну опять одни кракозябры. Может, тебе проще сделать html и сконвертировать его в пдф?

---

## AI

Отличная идея! Давайте сделаем красивый HTML и конвертируем его в PDF. Это будет гораздо надежнее. Вот код:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc > /dev/null 2>&1
!pip install -q weasyprint

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files
from weasyprint import HTML
import tempfile

# ======================
# КРАСИВЫЙ HTML С CSS ДЛЯ ПЕЧАТИ
# ======================
def create_beautiful_html(content, filename):
    """Создаем красивый HTML с CSS оптимизированным для печати"""
    
    # Простая очистка markdown
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Сохраняем обработанный markdown
    temp_md = 'temp.md'
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Конвертируем markdown в HTML
    html_file = filename.replace('.md', '.html')
    os.system(f'pandoc "{temp_md}" -o "{html_file}" -t html5 --standalone')
    
    # Читаем сгенерированный HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Удаляем временный файл
    os.remove(temp_md)
    
    # Профессиональный CSS для печати
    print_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: white;
            padding: 0;
            margin: 0;
            font-size: 12pt;
        }
        
        .document {
            max-width: 21cm;
            margin: 0 auto;
            padding: 2cm;
            background: white;
        }
        
        h1 {
            font-size: 24pt;
            font-weight: 700;
            color: #2c3e50;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
            page-break-after: avoid;
        }
        
        h2 {
            font-size: 18pt;
            font-weight: 600;
            color: #34495e;
            margin: 25px 0 15px 0;
            padding-left: 10px;
            border-left: 3px solid #3498db;
            page-break-after: avoid;
        }
        
        h3 {
            font-size: 14pt;
            font-weight: 500;
            color: #465c7a;
            margin: 20px 0 10px 0;
            page-break-after: avoid;
        }
        
        p {
            margin: 12px 0;
            text-align: justify;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }
        
        th {
            background: #34495e;
            color: white;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #2c3e50;
        }
        
        td {
            padding: 8px 12px;
            border: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        ul, ol {
            margin: 15px 0;
            padding-left: 25px;
        }
        
        li {
            margin: 6px 0;
        }
        
        code {
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }
        
        pre {
            background: #2d3748;
            color: white;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            padding: 15px 20px;
            margin: 20px 0;
            background: #f8f9fa;
            font-style: italic;
        }
        
        /* Оптимизации для печати */
        @media print {
            body {
                font-size: 11pt;
                line-height: 1.4;
            }
            
            .document {
                padding: 1.5cm;
                margin: 0;
                max-width: none;
                box-shadow: none;
            }
            
            h1 {
                font-size: 18pt;
                margin: 20px 0 15px 0;
            }
            
            h2 {
                font-size: 14pt;
                margin: 18px 0 12px 0;
            }
            
            h3 {
                font-size: 12pt;
                margin: 15px 0 10px 0;
            }
            
            table {
                font-size: 9pt;
            }
            
            /* Избегаем разрывов страниц внутри важных элементов */
            h1, h2, h3, h4, h5, h6 {
                page-break-after: avoid;
            }
            
            pre, blockquote, table, img {
                page-break-inside: avoid;
            }
            
            /* Убираем фон для экономии тонера */
            th {
                background: #666 !important;
                color: white !important;
                -webkit-print-color-adjust: exact;
            }
            
            tr:nth-child(even) {
                background: #f5f5f5 !important;
                -webkit-print-color-adjust: exact;
            }
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #3498db;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 10pt;
            color: #666;
        }
    </style>
    """
    
    # Создаем финальный HTML с нашим CSS
    final_html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Документ</title>
        {print_css}
    </head>
    <body>
        <div class="document">
            <div class="header">
                <h1>Профессиональный документ</h1>
            </div>
            {html_content}
            <div class="footer">
                Сгенерировано автоматически • Страница <span class="page-number"></span>
            </div>
        </div>
        
        <script>
            // Добавляем нумерацию страниц
            document.addEventListener('DOMContentLoaded', function() {{
                var pageNumbers = document.querySelectorAll('.page-number');
                for (var i = 0; i < pageNumbers.length; i++) {{
                    pageNumbers[i].textContent = (i + 1);
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Перезаписываем HTML файл
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    return html_file

# ======================
# КОНВЕРТАЦИЯ HTML В PDF
# ======================
def convert_html_to_pdf(html_file, pdf_file):
    """Конвертируем HTML в PDF используя WeasyPrint"""
    try:
        print("Конвертируем HTML в PDF...")
        
        # Конвертируем
        HTML(html_file).write_pdf(pdf_file)
        
        # Проверяем что файл создан
        if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
            print("✓ PDF успешно создан!")
            return True
    

---

## USER

Зачем-то делает 2 файл. Давай один. Не понравилось, что делает белый шрифт на белом фоне. Плюс:
Установка необходимых пакетов...
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 302.0/302.0 kB 7.6 MB/s eta 0:00:00
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 40.9 MB/s eta 0:00:00
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 847.1/847.1 kB 36.0 MB/s eta 0:00:00
✓ Пакеты установлены!
============================================================
🎨 КОНВЕРТЕР MARKDOWN → HTML → PDF
============================================================
Загрузите ваш Markdown файл:
Master_Prompt_FinRez_Labor.md
Master_Prompt_FinRez_Labor.md(n/a) - 46871 bytes, last modified: 19.11.2025 - 100% done
Saving Master_Prompt_FinRez_Labor.md to Master_Prompt_FinRez_Labor.md
📄 Обрабатываем: Master_Prompt_FinRez_Labor.md
📊 Размер: 26857 символов

🎨 Создаем красивый HTML...
✅ HTML создан: Master_Prompt_FinRez_Labor.html
Конвертируем HTML в PDF...
WARNING:weasyprint:Ignored `overflow-x: auto` at 108:13, unknown property.
WARNING:weasyprint:Ignored `box-shadow: none` at 133:17, unknown property.
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'maxp' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'maxp'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'maxp'
INFO:fontTools.subset:maxp pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'cmap' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'cmap' table
DEBUG:fontTools.ttLib.ttFont:Reading 'post' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'post' table
DEBUG:fontTools.subset.timer:Took 0.016s to load 'cmap'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'cmap'
INFO:fontTools.subset:cmap pruned
INFO:fontTools.subset:prep dropped
DEBUG:fontTools.subset.timer:Took 0.000s to load 'post'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'post'
INFO:fontTools.subset:post pruned
INFO:fontTools.subset:GPOS dropped
INFO:fontTools.subset:GSUB dropped
DEBUG:fontTools.ttLib.ttFont:Reading 'glyf' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'glyf' table
DEBUG:fontTools.ttLib.ttFont:Reading 'loca' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'loca' table
DEBUG:fontTools.ttLib.ttFont:Reading 'head' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'head' table
DEBUG:fontTools.subset.timer:Took 0.011s to load 'glyf'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.001s to close glyph list over 'cmap'
INFO:fontTools.subset:Added gid0 to subset
INFO:fontTools.subset:Closing glyph list over 'glyf': 96 glyphs before
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'C', 'E', 'I', 'Kacyr', 'M', 'O', 'R', 'S', 'T', 'U', 'V', 'X', 'Y', 'arrowboth.case', 'colon', 'colon.case', 'comma', 'exclam', 'five', 'four', 'hyphen', 'hyphen.case', 'one', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'period', 'plus.case', 's', 'seven', 'six', 'space', 'three', 'two', 'uni0410', 'uni0411', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0416', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0426', 'uni0427', 'uni0428', 'uni0429', 'uni042B', 'uni042C', 'uni042D', 'uni042E', 'uni042F', 'uni0430', 'uni0431', 'uni0432', 'uni0433', 'uni0434', 'uni0435', 'uni0436', 'uni0437', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043C', 'uni043D', 'uni043E', 'uni043F', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni0444', 'uni0445', 'uni0446', 'uni0447', 'uni0449', 'uni044B', 'uni044C', 'uni044E', 'uni044F', 'v']
INFO:fontTools.subset:Glyph IDs:   [0, 2, 48, 71, 73, 95, 133, 187, 197, 292, 299, 312, 314, 321, 369, 384, 397, 411, 424, 456, 466, 472, 540, 596, 641, 838, 848, 871, 978, 994, 1009, 1066, 1069, 1070, 1072, 1073, 1076, 1079, 1080, 1081, 1083, 1088, 1089, 1091, 1092, 1095, 1096, 1097, 1251, 1252, 1253, 1256, 1257, 1259, 1260, 1262, 1267, 1270, 1272, 1277, 1278, 1279, 1282, 1284, 1288, 1289, 1291, 1297, 1298, 1340, 1341, 1343, 1344, 1345, 1347, 1348, 1425, 1435, 1436, 1444, 1445, 1457, 1469, 1499, 1500, 1503, 1504, 1533, 1747, 1804, 2372, 2377, 2378, 2379, 2380, 2416]
INFO:fontTools.subset:Closed glyph list over 'glyf': 119 glyphs after
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'E', 'H', 'I', 'Kacyr', 'M', 'O', 'P', 'Pi', 'R', 'S', 'T', 'U', 'V', 'X', 'Y', '_part.cyrtic', 'a', 'arrowboth', 'arrowboth.case', 'c', 'colon', 'colon.case', 'comma', 'dotlessi', 'e', 'exclam', 'five', 'four', 'h.sc', 'hyphen', 'hyphen.case', 'm.sc', 'o', 'one', 'p', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'pecyrillicturn', 'period', 'plus', 'plus.case', 'quoteright', 's', 'seven', 'six', 'space', 't.sc', 'three', 'two', 'uni0306', 'uni0410', 'uni0411', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0416', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni041F.turn', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0426', 'uni0427', 'uni0428', 'uni0429', 'uni042B', 'uni042C', 'uni042D', 'uni042E', 'uni042F', 'uni0430', 'uni0431', 'uni0432', 'uni0433', 'uni0434', 'uni0435', 'uni0436', 'uni0437', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043C', 'uni043D', 'uni043E', 'uni043F', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni0444', 'uni0445', 'uni0446', 'uni0447', 'uni0448', 'uni0449', 'uni044B', 'uni044C', 'uni044E', 'uni044F', 'v', 'x', 'y']
INFO:fontTools.subset:Glyph IDs:   [0, 2, 48, 65, 71, 73, 95, 133, 161, 187, 197, 292, 299, 312, 314, 321, 369, 375, 384, 397, 411, 424, 456, 466, 472, 507, 540, 586, 596, 614, 641, 690, 790, 838, 843, 848, 871, 978, 991, 994, 996, 1009, 1036, 1066, 1069, 1070, 1072, 1073, 1076, 1079, 1080, 1081, 1083, 1088, 1089, 1091, 1092, 1095, 1096, 1097, 1251, 1252, 1253, 1256, 1257, 1259, 1260, 1262, 1267, 1270, 1272, 1277, 1278, 1279, 1282, 1284, 1287, 1288, 1289, 1291, 1297, 1298, 1340, 1341, 1343, 1344, 1345, 1347, 1348, 1425, 1435, 1436, 1444, 1445, 1457, 1469, 1481, 1499, 1500, 1503, 1504, 1520, 1533, 1747, 1784, 1804, 2359, 2360, 2361, 2372, 2377, 2378, 2379, 2380, 2416, 2648, 2822, 2827, 2834]
DEBUG:fontTools.subset.timer:Took 0.006s to close glyph list over 'glyf'
INFO:fontTools.subset:Retaining 119 glyphs
INFO:fontTools.subset:head subsetting not needed
INFO:fontTools.subset:hhea subsetting not needed
INFO:fontTools.subset:maxp subsetting not needed
INFO:fontTools.subset:OS/2 subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'hmtx' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hmtx' table
DEBUG:fontTools.ttLib.ttFont:Reading 'hhea' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hhea' table
DEBUG:fontTools.subset.timer:Took 0.007s to subset 'hmtx'
INFO:fontTools.subset:hmtx subsetted
DEBUG:fontTools.subset.timer:Took 0.001s to subset 'cmap'
INFO:fontTools.subset:cmap subsetted
INFO:fontTools.subset:loca subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'post'
INFO:fontTools.subset:post subsetted
INFO:fontTools.subset:gasp subsetting not needed
INFO:fontTools.subset:STAT subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'GDEF' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'GDEF' table
DEBUG:fontTools.subset.timer:Took 0.005s to subset 'GDEF'
INFO:fontTools.subset:GDEF subsetted
INFO:fontTools.subset:name subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.003s to subset 'glyf'
INFO:fontTools.subset:glyf subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset GlyphOrder
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'head'
INFO:fontTools.subset:head pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'OS/2' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'OS/2' table
INFO:fontTools.subset:OS/2 Unicode ranges pruned: [0, 9, 60]
INFO:fontTools.subset:OS/2 CodePage ranges pruned: [2]
DEBUG:fontTools.subset.timer:Took 0.003s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'GDEF'
INFO:fontTools.subset:GDEF pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'name' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'name' table
DEBUG:fontTools.ttLib.ttFont:Reading 'gasp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'gasp' table
DEBUG:fontTools.ttLib.ttFont:Reading 'STAT' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'STAT' table
DEBUG:fontTools.subset.timer:Took 0.007s to prune 'name'
INFO:fontTools.subset:name pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'maxp' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'maxp'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'maxp'
INFO:fontTools.subset:maxp pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'cmap' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'cmap' table
DEBUG:fontTools.ttLib.ttFont:Reading 'post' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'post' table
DEBUG:fontTools.subset.timer:Took 0.017s to load 'cmap'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'cmap'
INFO:fontTools.subset:cmap pruned
INFO:fontTools.subset:prep dropped
DEBUG:fontTools.subset.timer:Took 0.000s to load 'post'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'post'
INFO:fontTools.subset:post pruned
INFO:fontTools.subset:GPOS dropped
INFO:fontTools.subset:GSUB dropped
DEBUG:fontTools.ttLib.ttFont:Reading 'glyf' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'glyf' table
DEBUG:fontTools.ttLib.ttFont:Reading 'loca' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'loca' table
DEBUG:fontTools.ttLib.ttFont:Reading 'head' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'head' table
DEBUG:fontTools.subset.timer:Took 0.011s to load 'glyf'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.001s to close glyph list over 'cmap'
INFO:fontTools.subset:Added gid0 to subset
INFO:fontTools.subset:Closing glyph list over 'glyf': 74 glyphs before
INFO:fontTools.subset:Glyph names: ['.notdef', 'C', 'G', 'Kacyr', 'O', 'P', 'R', 'S', 'colon.case', 'five', 'hyphen', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'percent', 'period', 'plus', 's', 'space', 'three', 'uni0410', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0425', 'uni0426', 'uni0427', 'uni0428', 'uni042B', 'uni042C', 'uni042D', 'uni042E', 'uni042F', 'uni0430', 'uni0432', 'uni0434', 'uni0435', 'uni0436', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043C', 'uni043D', 'uni043E', 'uni043F', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni0444', 'uni0445', 'uni0446', 'uni0447', 'uni044B', 'uni044C', 'uni044F', 'v', 'zero']
INFO:fontTools.subset:Glyph IDs:   [0, 48, 71, 73, 133, 141, 187, 299, 312, 314, 321, 369, 375, 384, 397, 540, 596, 641, 838, 848, 871, 978, 994, 1009, 1069, 1072, 1073, 1076, 1079, 1080, 1081, 1083, 1088, 1091, 1092, 1095, 1096, 1097, 1252, 1256, 1257, 1260, 1262, 1267, 1270, 1272, 1277, 1278, 1279, 1282, 1284, 1289, 1291, 1298, 1339, 1343, 1345, 1435, 1436, 1444, 1445, 1457, 1500, 1504, 1520, 1714, 1747, 2372, 2377, 2378, 2379, 2380, 2382, 2416]
INFO:fontTools.subset:Closed glyph list over 'glyf': 98 glyphs after
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'E', 'G', 'H', 'I', 'Kacyr', 'M', 'O', 'P', 'Pi', 'R', 'S', 'T', 'X', '_part.cyrtic', 'a', 'c', 'colon.case', 'dotlessi', 'e', 'five', 'h.sc', 'hyphen', 'm.sc', 'o', 'p', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'pecyrillicturn', 'percent', 'period', 'plus', 's', 'space', 't.sc', 'three', 'uni0306', 'uni0410', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni041F.turn', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0425', 'uni0426', 'uni0427', 'uni0428', 'uni042B', 'uni042C', 'uni042D', 'uni042E', 'uni042F', 'uni0430', 'uni0432', 'uni0434', 'uni0435', 'uni0436', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043C', 'uni043D', 'uni043E', 'uni043F', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni0444', 'uni0445', 'uni0446', 'uni0447', 'uni044B', 'uni044C', 'uni044F', 'v', 'x', 'y', 'zero']
INFO:fontTools.subset:Glyph IDs:   [0, 2, 48, 65, 71, 73, 95, 133, 141, 161, 187, 197, 292, 299, 312, 314, 321, 369, 375, 384, 397, 411, 466, 507, 540, 586, 596, 614, 641, 690, 790, 838, 843, 848, 871, 978, 991, 994, 996, 1009, 1036, 1069, 1072, 1073, 1076, 1079, 1080, 1081, 1083, 1088, 1091, 1092, 1095, 1096, 1097, 1252, 1256, 1257, 1260, 1262, 1267, 1270, 1272, 1277, 1278, 1279, 1282, 1284, 1289, 1291, 1298, 1339, 1343, 1345, 1435, 1436, 1444, 1445, 1457, 1500, 1504, 1520, 1714, 1747, 2359, 2360, 2361, 2372, 2377, 2378, 2379, 2380, 2382, 2416, 2648, 2822, 2827, 2834]
DEBUG:fontTools.subset.timer:Took 0.006s to close glyph list over 'glyf'
INFO:fontTools.subset:Retaining 98 glyphs
INFO:fontTools.subset:head subsetting not needed
INFO:fontTools.subset:hhea subsetting not needed
INFO:fontTools.subset:maxp subsetting not needed
INFO:fontTools.subset:OS/2 subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'hmtx' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hmtx' table
DEBUG:fontTools.ttLib.ttFont:Reading 'hhea' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hhea' table
DEBUG:fontTools.subset.timer:Took 0.006s to subset 'hmtx'
INFO:fontTools.subset:hmtx subsetted
DEBUG:fontTools.subset.timer:Took 0.002s to subset 'cmap'
INFO:fontTools.subset:cmap subsetted
INFO:fontTools.subset:loca subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'post'
INFO:fontTools.subset:post subsetted
INFO:fontTools.subset:gasp subsetting not needed
INFO:fontTools.subset:STAT subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'GDEF' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'GDEF' table
DEBUG:fontTools.subset.timer:Took 0.004s to subset 'GDEF'
INFO:fontTools.subset:GDEF subsetted
INFO:fontTools.subset:name subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.005s to subset 'glyf'
INFO:fontTools.subset:glyf subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset GlyphOrder
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'head'
INFO:fontTools.subset:head pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'OS/2' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'OS/2' table
INFO:fontTools.subset:OS/2 Unicode ranges pruned: [0, 9, 60]
INFO:fontTools.subset:OS/2 CodePage ranges pruned: [0]
DEBUG:fontTools.subset.timer:Took 0.002s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'GDEF'
INFO:fontTools.subset:GDEF pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'name' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'name' table
DEBUG:fontTools.ttLib.ttFont:Reading 'gasp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'gasp' table
DEBUG:fontTools.ttLib.ttFont:Reading 'STAT' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'STAT' table
DEBUG:fontTools.subset.timer:Took 0.005s to prune 'name'
INFO:fontTools.subset:name pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'maxp' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'maxp'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'maxp'
INFO:fontTools.subset:maxp pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'cmap' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'cmap' table
DEBUG:fontTools.ttLib.ttFont:Reading 'post' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'post' table
DEBUG:fontTools.subset.timer:Took 0.016s to load 'cmap'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'cmap'
INFO:fontTools.subset:cmap pruned
INFO:fontTools.subset:prep dropped
DEBUG:fontTools.subset.timer:Took 0.000s to load 'post'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'post'
INFO:fontTools.subset:post pruned
INFO:fontTools.subset:GPOS dropped
INFO:fontTools.subset:GSUB dropped
DEBUG:fontTools.ttLib.ttFont:Reading 'glyf' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'glyf' table
DEBUG:fontTools.ttLib.ttFont:Reading 'loca' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'loca' table
DEBUG:fontTools.ttLib.ttFont:Reading 'head' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'head' table
DEBUG:fontTools.subset.timer:Took 0.011s to load 'glyf'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.001s to close glyph list over 'cmap'
INFO:fontTools.subset:Added gid0 to subset
INFO:fontTools.subset:Closing glyph list over 'glyf': 123 glyphs before
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'E', 'F', 'G', 'Kacyr', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'X', 'Y', 'a', 'ampersand', 'arrowright', 'asciitilde.case', 'bracketleft', 'bracketleft.case', 'bracketright', 'bracketright.case', 'bullet', 'c', 'colon', 'comma', 'e', 'emdash', 'equal', 'five', 'four', 'g', 'hyphen', 'hyphen.case', 'i', 'l', 'm', 'n', 'o', 'one', 'p', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'percent', 'period', 'plus', 'plus.case', 'plusminus.case', 'question', 'quotedblleft', 'quotedblright', 'r', 's', 'seven', 'slash', 'space', 'space.tf', 't', 'three', 'two', 'uni0410', 'uni0411', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0426', 'uni042B', 'uni0430', 'uni0431', 'uni0432', 'uni0433', 'uni0434', 'uni0435', 'uni0436', 'uni0437', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043C', 'uni043D', 'uni043E', 'uni043F', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni0444', 'uni0445', 'uni0446', 'uni0447', 'uni0448', 'uni0449', 'uni044A', 'uni044B', 'uni044C', 'uni044D', 'uni044E', 'uni044F', 'uni26A0', 'w', 'x', 'y', 'zero']
INFO:fontTools.subset:Glyph IDs:   [0, 2, 48, 65, 71, 73, 95, 133, 137, 141, 187, 281, 292, 299, 300, 312, 314, 321, 369, 375, 384, 397, 466, 472, 507, 540, 586, 596, 614, 641, 658, 689, 736, 766, 773, 790, 838, 843, 848, 852, 871, 888, 982, 991, 994, 996, 1009, 1066, 1069, 1072, 1073, 1076, 1079, 1080, 1081, 1091, 1251, 1252, 1253, 1256, 1257, 1259, 1260, 1262, 1267, 1270, 1272, 1277, 1278, 1279, 1282, 1284, 1287, 1288, 1289, 1290, 1291, 1296, 1297, 1298, 1339, 1340, 1341, 1343, 1344, 1345, 1348, 1420, 1423, 1429, 1435, 1436, 1437, 1439, 1444, 1445, 1446, 1447, 1453, 1457, 1460, 1462, 1469, 1484, 1485, 1499, 1500, 1503, 1518, 1520, 1533, 1537, 1539, 1714, 1747, 1775, 1822, 2372, 2377, 2378, 2379, 2380, 2416]
INFO:fontTools.subset:Closed glyph list over 'glyf': 141 glyphs after
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'E', 'F', 'G', 'H', 'I', 'Kacyr', 'L', 'M', 'N', 'O', 'P', 'Pi', 'R', 'S', 'T', 'X', 'Y', '_part.cyrtic', 'a', 'ampersand', 'arrowright', 'asciitilde', 'asciitilde.case', 'bracketleft', 'bracketleft.case', 'bracketright', 'bracketright.case', 'bullet', 'c', 'colon', 'comma', 'dotlessi', 'e', 'emdash', 'equal', 'five', 'four', 'g', 'h.sc', 'hyphen', 'hyphen.case', 'i', 'l', 'm', 'm.sc', 'n', 'o', 'one', 'p', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'pecyrillicturn', 'percent', 'period', 'plus', 'plus.case', 'plusminus', 'plusminus.case', 'question', 'quotedblleft', 'quotedblright', 'quoteleft', 'quoteright', 'r', 's', 'seven', 'slash', 'space', 'space.tf', 't', 't.sc', 'three', 'two', 'uni0306', 'uni0307', 'uni0410', 'uni0411', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni041F.turn', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0426', 'uni042B', 'uni042C', 'uni0430', 'uni0431', 'uni0432', 'uni0433', 'uni0434', 'uni0435', 'uni0436', 'uni0437', 'uni0438', 'uni0439', 'uni043A', 'uni043B', 'uni043C', 'uni043D', 'uni043E', 'uni043F', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni0444', 'uni0445', 'uni0446', 'uni0447', 'uni0448', 'uni0449', 'uni044A', 'uni044B', 'uni044C', 'uni044D', 'uni044E', 'uni044F', 'uni26A0', 'w', 'x', 'y', 'zero']
INFO:fontTools.subset:Glyph IDs:   [0, 2, 48, 65, 71, 73, 95, 133, 137, 141, 161, 187, 197, 281, 292, 299, 300, 312, 314, 321, 369, 375, 384, 397, 411, 466, 472, 507, 540, 586, 596, 614, 641, 658, 689, 690, 736, 766, 773, 790, 838, 843, 848, 852, 871, 888, 982, 991, 994, 996, 1009, 1036, 1066, 1069, 1072, 1073, 1076, 1079, 1080, 1081, 1091, 1092, 1251, 1252, 1253, 1256, 1257, 1259, 1260, 1262, 1267, 1270, 1272, 1277, 1278, 1279, 1282, 1284, 1287, 1288, 1289, 1290, 1291, 1296, 1297, 1298, 1339, 1340, 1341, 1343, 1344, 1345, 1348, 1420, 1423, 1429, 1435, 1436, 1437, 1439, 1444, 1445, 1446, 1447, 1453, 1457, 1460, 1462, 1469, 1480, 1481, 1484, 1485, 1499, 1500, 1503, 1518, 1520, 1524, 1526, 1533, 1537, 1539, 1714, 1747, 1775, 1822, 2359, 2360, 2361, 2372, 2377, 2378, 2379, 2380, 2416, 2645, 2648, 2822, 2827, 2834]
DEBUG:fontTools.subset.timer:Took 0.008s to close glyph list over 'glyf'
INFO:fontTools.subset:Retaining 141 glyphs
INFO:fontTools.subset:head subsetting not needed
INFO:fontTools.subset:hhea subsetting not needed
INFO:fontTools.subset:maxp subsetting not needed
INFO:fontTools.subset:OS/2 subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'hmtx' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hmtx' table
DEBUG:fontTools.ttLib.ttFont:Reading 'hhea' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hhea' table
DEBUG:fontTools.subset.timer:Took 0.009s to subset 'hmtx'
INFO:fontTools.subset:hmtx subsetted
DEBUG:fontTools.subset.timer:Took 0.002s to subset 'cmap'
INFO:fontTools.subset:cmap subsetted
INFO:fontTools.subset:loca subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'post'
INFO:fontTools.subset:post subsetted
INFO:fontTools.subset:gasp subsetting not needed
INFO:fontTools.subset:STAT subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'GDEF' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'GDEF' table
DEBUG:fontTools.subset.timer:Took 0.004s to subset 'GDEF'
INFO:fontTools.subset:GDEF subsetted
INFO:fontTools.subset:name subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.003s to subset 'glyf'
INFO:fontTools.subset:glyf subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset GlyphOrder
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'head'
INFO:fontTools.subset:head pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'OS/2' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'OS/2' table
INFO:fontTools.subset:OS/2 Unicode ranges pruned: [0, 5, 9, 31, 37, 60]
INFO:fontTools.subset:OS/2 CodePage ranges pruned: [2]
DEBUG:fontTools.subset.timer:Took 0.002s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'GDEF'
INFO:fontTools.subset:GDEF pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'name' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'name' table
DEBUG:fontTools.ttLib.ttFont:Reading 'gasp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'gasp' table
DEBUG:fontTools.ttLib.ttFont:Reading 'STAT' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'STAT' table
DEBUG:fontTools.subset.timer:Took 0.006s to prune 'name'
INFO:fontTools.subset:name pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'maxp' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'maxp'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'maxp'
INFO:fontTools.subset:maxp pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'cmap' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'cmap' table
DEBUG:fontTools.ttLib.ttFont:Reading 'post' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'post' table
DEBUG:fontTools.subset.timer:Took 0.004s to load 'cmap'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'cmap'
INFO:fontTools.subset:cmap pruned
INFO:fontTools.subset:fpgm dropped
INFO:fontTools.subset:prep dropped
INFO:fontTools.subset:cvt  dropped
DEBUG:fontTools.subset.timer:Took 0.000s to load 'post'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'post'
INFO:fontTools.subset:post pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'glyf' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'glyf' table
DEBUG:fontTools.ttLib.ttFont:Reading 'loca' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'loca' table
DEBUG:fontTools.ttLib.ttFont:Reading 'head' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'head' table
DEBUG:fontTools.subset.timer:Took 0.007s to load 'glyf'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.000s to close glyph list over 'cmap'
INFO:fontTools.subset:Added gid0 to subset
INFO:fontTools.subset:Closing glyph list over 'glyf': 152 glyphs before
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'D', 'E', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'SF020000', 'SF080000', 'SF100000', 'SF110000', 'SF430000', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'afii10017', 'afii10018', 'afii10019', 'afii10020', 'afii10021', 'afii10022', 'afii10023', 'afii10024', 'afii10025', 'afii10026', 'afii10027', 'afii10028', 'afii10029', 'afii10030', 'afii10031', 'afii10032', 'afii10033', 'afii10034', 'afii10035', 'afii10036', 'afii10037', 'afii10038', 'afii10039', 'afii10040', 'afii10041', 'afii10042', 'afii10043', 'afii10045', 'afii10046', 'afii10047', 'afii10048', 'afii10049', 'afii10065', 'afii10066', 'afii10067', 'afii10068', 'afii10069', 'afii10070', 'afii10071', 'afii10072', 'afii10073', 'afii10074', 'afii10075', 'afii10076', 'afii10077', 'afii10078', 'afii10079', 'afii10080', 'afii10081', 'afii10082', 'afii10083', 'afii10084', 'afii10085', 'afii10086', 'afii10087', 'afii10088', 'afii10089', 'afii10090', 'afii10091', 'afii10092', 'afii10093', 'afii10094', 'afii10095', 'afii10096', 'afii10097', 'afii61352', 'arrowboth', 'arrowdown', 'arrowright', 'arrowup', 'asciitilde', 'b', 'bar', 'bracketleft', 'bracketright', 'bullet', 'c', 'colon', 'comma', 'd', 'e', 'eight', 'equal', 'five', 'four', 'g', 'greater', 'i', 'k', 'l', 'less', 'm', 'multiply', 'n', 'nine', 'numbersign', 'o', 'one', 'parenleft', 'parenright', 'percent', 'period', 'plus', 'plusminus', 'question', 'quotedbl', 'r', 's', 'seven', 'six', 'slash', 't', 'three', 'two', 'underscore', 'uni00A0', 'uni00AD', 'v', 'w', 'x', 'y', 'zero']
INFO:fontTools.subset:Glyph IDs:   [0, 3, 5, 6, 8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 36, 37, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 56, 57, 58, 59, 60, 61, 62, 64, 66, 68, 69, 70, 71, 72, 74, 76, 78, 79, 80, 81, 82, 85, 86, 87, 89, 90, 91, 92, 95, 97, 113, 151, 413, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 493, 533, 550, 559, 560, 561, 562, 585, 586, 589, 591, 596]
INFO:fontTools.subset:Closed glyph list over 'glyf': 158 glyphs after
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'D', 'E', 'G', 'Gamma', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Phi', 'R', 'S', 'SF020000', 'SF080000', 'SF100000', 'SF110000', 'SF430000', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'afii10017', 'afii10018', 'afii10019', 'afii10020', 'afii10021', 'afii10022', 'afii10023', 'afii10024', 'afii10025', 'afii10026', 'afii10027', 'afii10028', 'afii10029', 'afii10030', 'afii10031', 'afii10032', 'afii10033', 'afii10034', 'afii10035', 'afii10036', 'afii10037', 'afii10038', 'afii10039', 'afii10040', 'afii10041', 'afii10042', 'afii10043', 'afii10045', 'afii10046', 'afii10047', 'afii10048', 'afii10049', 'afii10065', 'afii10066', 'afii10067', 'afii10068', 'afii10069', 'afii10070', 'afii10071', 'afii10072', 'afii10073', 'afii10074', 'afii10075', 'afii10076', 'afii10077', 'afii10078', 'afii10079', 'afii10080', 'afii10081', 'afii10082', 'afii10083', 'afii10084', 'afii10085', 'afii10086', 'afii10087', 'afii10088', 'afii10089', 'afii10090', 'afii10091', 'afii10092', 'afii10093', 'afii10094', 'afii10095', 'afii10096', 'afii10097', 'afii61352', 'arrowboth', 'arrowdown', 'arrowright', 'arrowup', 'asciitilde', 'b', 'bar', 'bracketleft', 'bracketright', 'bullet', 'c', 'colon', 'comma', 'cyrillicbreve', 'd', 'dieresis', 'e', 'eight', 'equal', 'five', 'four', 'g', 'greater', 'i', 'k', 'l', 'less', 'm', 'multiply', 'n', 'nine', 'numbersign', 'o', 'one', 'p', 'parenleft', 'parenright', 'percent', 'period', 'plus', 'plusminus', 'question', 'quotedbl', 'r', 's', 'seven', 'six', 'slash', 't', 'three', 'two', 'underscore', 'uni00A0', 'uni00AD', 'v', 'w', 'x', 'y', 'zero']
INFO:fontTools.subset:Glyph IDs:   [0, 3, 5, 6, 8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 36, 37, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 64, 66, 68, 69, 70, 71, 72, 74, 76, 78, 79, 80, 81, 82, 83, 85, 86, 87, 89, 90, 91, 92, 95, 97, 105, 113, 151, 353, 371, 413, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 493, 533, 550, 559, 560, 561, 562, 585, 586, 589, 591, 596, 663]
DEBUG:fontTools.subset.timer:Took 0.006s to close glyph list over 'glyf'
INFO:fontTools.subset:Retaining 158 glyphs
INFO:fontTools.subset:head subsetting not needed
INFO:fontTools.subset:hhea subsetting not needed
INFO:fontTools.subset:maxp subsetting not needed
INFO:fontTools.subset:OS/2 subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'hmtx' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hmtx' table
DEBUG:fontTools.ttLib.ttFont:Reading 'hhea' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hhea' table
DEBUG:fontTools.subset.timer:Took 0.004s to subset 'hmtx'
INFO:fontTools.subset:hmtx subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'cmap'
INFO:fontTools.subset:cmap subsetted
INFO:fontTools.subset:loca subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'post'
INFO:fontTools.subset:post subsetted
INFO:fontTools.subset:gasp subsetting not needed
INFO:fontTools.subset:FFTM NOT subset; don't know how to subset
DEBUG:fontTools.ttLib.ttFont:Reading 'GDEF' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'GDEF' table
DEBUG:fontTools.subset.timer:Took 0.002s to subset 'GDEF'
INFO:fontTools.subset:GDEF subsetted
INFO:fontTools.subset:name subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.001s to subset 'glyf'
INFO:fontTools.subset:glyf subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset GlyphOrder
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'head'
INFO:fontTools.subset:head pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'OS/2' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'OS/2' table
INFO:fontTools.subset:OS/2 Unicode ranges pruned: [0, 1, 9, 31, 35, 37, 43]
INFO:fontTools.subset:OS/2 CodePage ranges pruned: [2]
DEBUG:fontTools.subset.timer:Took 0.002s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'GDEF'
INFO:fontTools.subset:GDEF pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'name' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'name' table
DEBUG:fontTools.ttLib.ttFont:Reading 'gasp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'gasp' table
DEBUG:fontTools.ttLib.ttFont:Reading 'FFTM' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'FFTM' table
DEBUG:fontTools.subset.timer:Took 0.005s to prune 'name'
INFO:fontTools.subset:name pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'maxp' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'maxp'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'maxp'
INFO:fontTools.subset:maxp pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'cmap' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'cmap' table
DEBUG:fontTools.ttLib.ttFont:Reading 'post' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'post' table
DEBUG:fontTools.subset.timer:Took 0.013s to load 'cmap'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'cmap'
INFO:fontTools.subset:cmap pruned
INFO:fontTools.subset:prep dropped
DEBUG:fontTools.subset.timer:Took 0.000s to load 'post'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'post'
INFO:fontTools.subset:post pruned
INFO:fontTools.subset:GPOS dropped
INFO:fontTools.subset:GSUB dropped
DEBUG:fontTools.ttLib.ttFont:Reading 'glyf' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'glyf' table
DEBUG:fontTools.ttLib.ttFont:Reading 'loca' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'loca' table
DEBUG:fontTools.ttLib.ttFont:Reading 'head' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'head' table
DEBUG:fontTools.subset.timer:Took 0.010s to load 'glyf'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.001s to close glyph list over 'cmap'
INFO:fontTools.subset:Added gid0 to subset
INFO:fontTools.subset:Closing glyph list over 'glyf': 66 glyphs before
INFO:fontTools.subset:Glyph names: ['.notdef', 'B', 'E', 'Kacyr', 'L', 'S', 'T', 'Y', 'c', 'colon', 'colon.case', 'e', 'five', 'four', 'g', 'hyphen', 'i', 'l', 'one', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'period', 'space', 'three', 'two', 'uni0410', 'uni0411', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0425', 'uni0426', 'uni0427', 'uni042B', 'uni042E', 'uni042F', 'uni0430', 'uni0434', 'uni0435', 'uni0436', 'uni0438', 'uni043A', 'uni043C', 'uni043E', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni044F', 'x']
INFO:fontTools.subset:Glyph IDs:   [0, 48, 65, 71, 95, 133, 187, 281, 299, 312, 314, 369, 397, 411, 472, 540, 586, 596, 614, 641, 658, 689, 736, 838, 848, 991, 1009, 1066, 1069, 1072, 1073, 1076, 1079, 1080, 1081, 1083, 1091, 1096, 1097, 1256, 1257, 1260, 1262, 1270, 1278, 1298, 1340, 1341, 1343, 1344, 1345, 1435, 1436, 1444, 1445, 1457, 1500, 1503, 1504, 1747, 2372, 2377, 2378, 2379, 2380, 2382]
INFO:fontTools.subset:Closed glyph list over 'glyf': 87 glyphs after
INFO:fontTools.subset:Glyph names: ['.notdef', 'A', 'B', 'C', 'E', 'H', 'I', 'Kacyr', 'L', 'M', 'O', 'P', 'Pi', 'S', 'T', 'X', 'Y', '_part.cyrtic', 'a', 'c', 'colon', 'colon.case', 'dotlessi', 'e', 'five', 'four', 'g', 'hyphen', 'i', 'l', 'm.sc', 'o', 'one', 'p', 'parenleft', 'parenleft.case', 'parenright', 'parenright.case', 'period', 'space', 't.sc', 'three', 'two', 'uni0306', 'uni0307', 'uni0410', 'uni0411', 'uni0412', 'uni0413', 'uni0414', 'uni0415', 'uni0417', 'uni0418', 'uni0419', 'uni041B', 'uni041C', 'uni041D', 'uni041E', 'uni041F', 'uni041F.turn', 'uni0420', 'uni0421', 'uni0422', 'uni0423', 'uni0424', 'uni0425', 'uni0426', 'uni0427', 'uni042B', 'uni042C', 'uni042E', 'uni042F', 'uni0430', 'uni0434', 'uni0435', 'uni0436', 'uni0438', 'uni043A', 'uni043C', 'uni043E', 'uni0440', 'uni0441', 'uni0442', 'uni0443', 'uni044F', 'x', 'y']
INFO:fontTools.subset:Glyph IDs:   [0, 2, 48, 65, 71, 73, 95, 133, 161, 187, 197, 281, 292, 299, 312, 314, 321, 369, 375, 397, 411, 466, 472, 507, 540, 586, 596, 614, 641, 658, 689, 690, 736, 790, 838, 843, 848, 991, 996, 1009, 1036, 1066, 1069, 1072, 1073, 1076, 1079, 1080, 1081, 1083, 1091, 1092, 1096, 1097, 1256, 1257, 1260, 1262, 1270, 1278, 1298, 1340, 1341, 1343, 1344, 1345, 1435, 1436, 1444, 1445, 1457, 1500, 1503, 1504, 1747, 2360, 2361, 2372, 2377, 2378, 2379, 2380, 2382, 2645, 2648, 2822, 2834]
DEBUG:fontTools.subset.timer:Took 0.006s to close glyph list over 'glyf'
INFO:fontTools.subset:Retaining 87 glyphs
INFO:fontTools.subset:head subsetting not needed
INFO:fontTools.subset:hhea subsetting not needed
INFO:fontTools.subset:maxp subsetting not needed
INFO:fontTools.subset:OS/2 subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'hmtx' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hmtx' table
DEBUG:fontTools.ttLib.ttFont:Reading 'hhea' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hhea' table
DEBUG:fontTools.subset.timer:Took 0.006s to subset 'hmtx'
INFO:fontTools.subset:hmtx subsetted
DEBUG:fontTools.subset.timer:Took 0.002s to subset 'cmap'
INFO:fontTools.subset:cmap subsetted
INFO:fontTools.subset:loca subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'post'
INFO:fontTools.subset:post subsetted
INFO:fontTools.subset:gasp subsetting not needed
INFO:fontTools.subset:STAT subsetting not needed
DEBUG:fontTools.ttLib.ttFont:Reading 'GDEF' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'GDEF' table
DEBUG:fontTools.subset.timer:Took 0.003s to subset 'GDEF'
INFO:fontTools.subset:GDEF subsetted
INFO:fontTools.subset:name subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.003s to subset 'glyf'
INFO:fontTools.subset:glyf subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset GlyphOrder
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'head'
INFO:fontTools.subset:head pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'OS/2' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'OS/2' table
INFO:fontTools.subset:OS/2 Unicode ranges pruned: [0, 9, 60]
INFO:fontTools.subset:OS/2 CodePage ranges pruned: [2]
DEBUG:fontTools.subset.timer:Took 0.002s to prune 'glyf'
INFO:fontTools.subset:glyf pruned
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'GDEF'
INFO:fontTools.subset:GDEF pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'name' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'name' table
DEBUG:fontTools.ttLib.ttFont:Reading 'gasp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'gasp' table
DEBUG:fontTools.ttLib.ttFont:Reading 'STAT' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'STAT' table
DEBUG:fontTools.subset.timer:Took 0.005s to prune 'name'
INFO:fontTools.subset:name pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'maxp' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'maxp' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'maxp'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'maxp'
INFO:fontTools.subset:maxp pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'cmap' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'cmap' table
DEBUG:fontTools.ttLib.ttFont:Reading 'CFF ' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'CFF ' table
DEBUG:fontTools.subset.timer:Took 0.009s to load 'cmap'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'cmap'
INFO:fontTools.subset:cmap pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'post' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'post' table
DEBUG:fontTools.subset.timer:Took 0.002s to load 'post'
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'post'
INFO:fontTools.subset:post pruned
DEBUG:fontTools.subset.timer:Took 0.000s to load 'CFF '
DEBUG:fontTools.subset.timer:Took 0.002s to prune 'CFF '
INFO:fontTools.subset:CFF  pruned
INFO:fontTools.subset:GPOS dropped
INFO:fontTools.subset:GSUB dropped
DEBUG:fontTools.subset.timer:Took 0.000s to close glyph list over 'cmap'
INFO:fontTools.subset:Added .notdef to subset
INFO:fontTools.subset:Closing glyph list over 'CFF ': 2 glyphs before
INFO:fontTools.subset:Glyph names: ['.notdef', 'uni27A1']
INFO:fontTools.subset:Glyph IDs:   [0, 1091]
INFO:fontTools.subset:Closed glyph list over 'CFF ': 2 glyphs after
INFO:fontTools.subset:Glyph names: ['.notdef', 'uni27A1']
INFO:fontTools.subset:Glyph IDs:   [0, 1091]
DEBUG:fontTools.subset.timer:Took 0.005s to close glyph list over 'CFF '
INFO:fontTools.subset:Retaining 2 glyphs
INFO:fontTools.subset:head subsetting not needed
INFO:fontTools.subset:hhea subsetting not needed
INFO:fontTools.subset:maxp subsetting not needed
INFO:fontTools.subset:OS/2 subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'cmap'
INFO:fontTools.subset:cmap subsetted
DEBUG:fontTools.subset.timer:Took 0.000s to subset 'post'
INFO:fontTools.subset:post subsetted
DEBUG:fontTools.subset.timer:Took 0.133s to subset 'CFF '
INFO:fontTools.subset:CFF  subsetted
INFO:fontTools.subset:FFTM NOT subset; don't know how to subset
DEBUG:fontTools.ttLib.ttFont:Reading 'hmtx' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hmtx' table
DEBUG:fontTools.ttLib.ttFont:Reading 'hhea' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'hhea' table
DEBUG:fontTools.subset.timer:Took 0.004s to subset 'hmtx'
INFO:fontTools.subset:hmtx subsetted
DEBUG:fontTools.ttLib.ttFont:Reading 'GDEF' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'GDEF' table
DEBUG:fontTools.subset.timer:Took 0.003s to subset 'GDEF'
INFO:fontTools.subset:GDEF subsetted
INFO:fontTools.subset:name subsetting not needed
DEBUG:fontTools.subset.timer:Took 0.000s to subset GlyphOrder
DEBUG:fontTools.ttLib.ttFont:Reading 'head' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'head' table
DEBUG:fontTools.subset.timer:Took 0.002s to prune 'head'
INFO:fontTools.subset:head pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'OS/2' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'OS/2' table
INFO:fontTools.subset:OS/2 Unicode ranges pruned: [47]
INFO:fontTools.subset:OS/2 CodePage ranges pruned: [0]
DEBUG:fontTools.subset.timer:Took 0.047s to prune 'CFF '
INFO:fontTools.subset:CFF  pruned
DEBUG:fontTools.subset.timer:Took 0.000s to prune 'GDEF'
INFO:fontTools.subset:GDEF pruned
DEBUG:fontTools.ttLib.ttFont:Reading 'name' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'name' table
DEBUG:fontTools.ttLib.ttFont:Reading 'FFTM' table from disk
DEBUG:fontTools.ttLib.ttFont:Decompiling 'FFTM' table
DEBUG:fontTools.subset.timer:Took 0.003s to prune 'name'
INFO:fontTools.subset:name pruned
✓ PDF успешно создан!
✅ PDF готов: Master_Prompt_FinRez_Labor.pdf

📥 PDF файл доступен для скачивания!

💡 Также доступен HTML файл для ручной конвертации:

🎉 Готово!

---

## AI

Понял проблемы! Давайте сделаем один PDF файл с правильными цветами. Упростим CSS и уберём создание HTML:

```python
# ======================
# УСТАНОВКА ПАКЕТОВ
# ======================
print("Установка необходимых пакетов...")
!apt-get update -qq > /dev/null 2>&1
!apt-get install -y pandoc > /dev/null 2>&1
!pip install -q weasyprint

print("✓ Пакеты установлены!")

# ======================
# ИМПОРТ БИБЛИОТЕК
# ======================
import os
import re
from google.colab import files
from weasyprint import HTML
import tempfile

# ======================
# ПРОСТОЙ И НАДЕЖНЫЙ HTML С ЧЕРНЫМ ТЕКСТОМ
# ======================
def create_simple_pdf(content, filename):
    """Создаем простой PDF с черным текстом на белом фоне"""
    
    # Простая очистка markdown
    replacements = {
        '': '•',
        '': '→', 
        '': '•',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Сохраняем обработанный markdown
    temp_md = 'temp.md'
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Конвертируем markdown в HTML
    html_file = filename.replace('.md', '_temp.html')
    os.system(f'pandoc "{temp_md}" -o "{html_file}" -t html5 --standalone')
    
    # Читаем сгенерированный HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Удаляем временный файл
    os.remove(temp_md)
    
    # ПРОСТОЙ CSS с черным текстом
    simple_css = """
    <style>
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.4;
            color: #000000 !important; /* ЧЕРНЫЙ текст */
            background: #ffffff !important; /* БЕЛЫЙ фон */
            margin: 0;
            padding: 1.5cm;
            font-size: 11pt;
        }
        
        h1 {
            font-size: 16pt;
            font-weight: bold;
            color: #000000 !important;
            margin: 20px 0 15px 0;
            border-bottom: 2px solid #000000;
            padding-bottom: 5px;
        }
        
        h2 {
            font-size: 14pt;
            font-weight: bold;
            color: #000000 !important;
            margin: 18px 0 12px 0;
            border-left: 3px solid #000000;
            padding-left: 10px;
        }
        
        h3 {
            font-size: 12pt;
            font-weight: bold;
            color: #000000 !important;
            margin: 15px 0 10px 0;
        }
        
        p {
            margin: 10px 0;
            color: #000000 !important;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 9pt;
        }
        
        th {
            background: #f0f0f0 !important; /* Светло-серый */
            color: #000000 !important; /* Черный текст */
            padding: 8px 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #000000;
        }
        
        td {
            padding: 6px 10px;
            border: 1px solid #000000;
            color: #000000 !important;
        }
        
        tr:nth-child(even) {
            background: #f8f8f8 !important; /* Очень светлый серый */
        }
        
        ul, ol {
            margin: 12px 0;
            padding-left: 20px;
        }
        
        li {
            margin: 5px 0;
            color: #000000 !important;
        }
        
        code {
            background: #f5f5f5;
            padding: 2px 4px;
            border-radius: 2px;
            font-family: 'Courier New', monospace;
            color: #000000 !important;
            border: 1px solid #cccccc;
        }
        
        pre {
            background: #f5f5f5 !important;
            color: #000000 !important;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 12px 0;
            border: 1px solid #cccccc;
        }
        
        blockquote {
            border-left: 4px solid #cccccc;
            padding: 12px 15px;
            margin: 15px 0;
            background: #f9f9f9;
            font-style: italic;
            color: #000000 !important;
        }
        
        /* Гарантируем черный текст для всех элементов */
        * {
            color: #000000 !important;
        }
        
        /* Для печати - еще более простые настройки */
        @media print {
            body {
                font-size: 10pt;
                padding: 1cm;
            }
            
            h1 { font-size: 14pt; }
            h2 { font-size: 12pt; }
            h3 { font-size: 11pt; }
            
            table {
                font-size: 8pt;
            }
        }
    </style>
    """
    
    # Создаем финальный HTML
    final_html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Документ</title>
        {simple_css}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Сохраняем финальный HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    # Конвертируем в PDF
    pdf_file = filename.replace('.md', '.pdf')
    try:
        HTML(html_file).write_pdf(pdf_file)
        success = True
    except Exception as e:
        print(f"Ошибка конвертации: {e}")
        success = False
    
    # Удаляем временный HTML файл
    if os.path.exists(html_file):
        os.remove(html_file)
    
    return pdf_file if success else None

# ======================
# ОСНОВНОЙ ПРОЦЕСС
# ======================
print("=" * 50)
print("📄 КОНВЕРТЕР MARKDOWN В PDF")
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
        # Читаем файл
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📊 Размер: {len(content)} символов")
        
        # Создаем PDF
        print("\n🔄 Создаем PDF...")
        pdf_file = create_simple_pdf(content, filename)
        
        if pdf_file and os.path.exists(pdf_file):
            print(f"✅ PDF готов: {pdf_file}")
            files.download(pdf_file)
            print("\n📥 Файл готов для скачивания!")
        else:
            print("❌ Не удалось создать PDF")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n🎉 Готово!")
```

## 🎯 Ключевые изменения:

### 1. **Только один PDF файл**
- Убрал полностью создание и скачивание HTML
- После конвертации временный HTML удаляется

### 2. **Гарантированно черный текст**
- `color: #000000 !important` для всех элементов
- `background: #ffffff !important` для фона
- Убраны все сложные цветовые схемы

### 3. **Простой и надежный CSS**
- Базовые шрифты Arial/Helvetica
- Минимальные стили
- Явные указания цветов с `!important`

### 4. **Упрощенная структура**
- Без сложных градиентов и теней
- Без внешних зависимостей (Google Fonts)
- Только базовые HTML элементы

### 5. **Надежная конвертация**
- Простая обработка ошибок
- Автоматическая очистка временных файлов

Теперь должен создаваться **только один PDF файл** с **черным текстом на белом фоне**!

---

## USER

А пересмотри весь контекст нашего разговора и сделай простую конвертацию маркдауна в html

---

## AI

Согласен! Давайте сделаем простую и надежную конвертацию Markdown в красивый HTML. Вот минимальный и эффективный код:

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
```

## 🎯 Что этот код делает:

### 1. **Минимальная установка**
- Только pandoc - ничего лишнего
- Быстрая установка

### 2. **Простая конвертация**
- Markdown → HTML через pandoc
- Автоматическая обработка таблиц, списков, кода
- Сохранение оригинальной структуры

### 3. **Красивый дизайн**
- Элегантный CSS с Georgia/Times шрифтами
- Адаптивный дизайн для всех устройств
- Профессиональные цвета и отступы

### 4. **Один файл на выходе**
- Только HTML файл
- Никаких временных файлов
- Чистый результат

### 5. **Надежность**
- Работает с любым Markdown
- Правильная кодировка UTF-8
- Минимум зависимостей

Этот код создаст один красивый HTML файл, который можно открыть в любом браузере!

---

