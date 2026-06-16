# RAG-индекс для вики Жукова Сергея

> **Версия:** 1.0 (2026-06-16) · **Назначение:** быстрый поиск по всей вики + raw чатам
> **Метод:** TF-IDF (с биграммами) + cosine similarity, без GPU

## Что это

Это **RAG-индекс** для всей вики и распакованных чатов Сергея. Позволяет Mavis (и любому LLM) за 0.1с найти релевантные фрагменты по любому запросу.

## Покрытие

- **5206 chunks** (511 wiki + 4695 raw chat)
- **117k уникальных токенов** (включая биграммы)
- **23.4 MB** raw чатов + **3.2 MB** wiki = 26.6 MB текста
- **536 из 537** чатов (один пустой)

## Структура

```
wiki/rag/
├── README.md                 ← этот файл
├── all_chats_metadata.json   ← индекс всех 537 чатов (title, date, count, source)
├── build_index.py            ← пересборка индекса
├── search.py                 ← CLI поиск (human-readable)
├── query.py                  ← запрос с форматированием под LLM-контекст
├── index.pkl                 ← TF-IDF матрица (5.5 MB)
├── chunks.json               ← все чанки с метаданными
├── vocab.pkl                 ← словарь (токен → индекс)
├── norms.npy                 ← L2-нормы строк матрицы (для cosine)
└── full_chats/               ← 536 файлов с распакованными чатами
    ├── 2025-06-18_QW_*.md
    ├── 2026-04-11_DS_*.md
    └── ...
```

## Использование

### 1. Из CLI (для Сергея / Mavis в bash)

```bash
# Обычный поиск
python3 wiki/rag/search.py "перспективы с Техинком"
python3 wiki/rag/search.py "кто такой Миша" --kind wiki --top 3
python3 wiki/rag/search.py "БИТ.Управление маркетплейсами" --top 10

# Получить LLM-ready контекст
python3 wiki/rag/query.py "перспективы с Техинком" --top 8 --max-chars 12000
python3 wiki/rag/query.py "кто из менеджеров умнее всех" --output /tmp/context.md
```

### 2. Из Python (для Mavis при ответе)

```python
import sys
sys.path.insert(0, '/workspace/wiki/rag')
from build_index import search

# Поиск с фильтром
results = search("перспективы с Техинком", top_k=8, kind_filter='wiki')
for r in results:
    print(f"[{r['score']:.3f}] {r['source']}: {r['title']}")
    print(f"   {r['content'][:300]}\n")
```

### 3. Сценарий для Mavis

**Когда использовать:** на ЛЮБОЙ вопрос про людей/проекты/клиентов/решения.

```python
# В начале ответа на вопрос пользователя:
context = query("что мы решили по X", top=8, max_chars=10000)
# Потом ответить на основе context, с цитатами
```

## Пересборка индекса

```bash
cd /workspace
python3 wiki/rag/build_index.py
```

Занимает ~10 секунд. Запускать:
- При добавлении новых чатов в `full_chats/`
- При обновлении wiki-файлов
- При желании изменить параметры индекса

## Известные ограничения

- **Без embeddings** — TF-IDF не понимает синонимы и семантику. «разработчик» vs «девелопер» не сматчатся.
- **Без реранкинга** — top-k может не быть оптимальным.
- **Короткие запросы** (<2 слов) дают плохие результаты.
- **Английские слова** в русских текстах не ранжируются идеально (есть свои токенизаторы, но не идеальные).

## Планы

- [ ] Добавить sentence-transformers (multilingual) для embeddings — для семантического поиска
- [ ] Гибридный поиск: TF-IDF + embeddings + re-ranker
- [ ] Веб-интерфейс (Flask) для Сергея
- [ ] Интеграция с n8n (webhook → query → Telegram)
