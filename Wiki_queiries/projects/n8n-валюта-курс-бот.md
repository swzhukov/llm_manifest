# n8n Telegram-бот курсов валют

> **Источник:** `raw_imports/39_DS_Currency Rates Telegram Workflow.md` (2026-06-02, 45 сообщений).

---

## Цель

Workflow в n8n, который:
- **Каждый день в 9:00** получает курсы валют (MOEX ISS API).
- **Отправляет** их в Telegram-бот.

---

## Контекст возникновения

Это **второй** workflow Сергея для n8n-телеграм-бота (первый — бот для транскрибации медиа, см. `n8n-телеграм-транскрибация.md`).

---

## Технический стек

| Компонент | Решение |
|-----------|---------|
| **n8n** | self-hosted на Beget (версия 2.17.7) |
| **MCP** | `n8n-mcp` от czlonkowski (https://github.com/czlonkowski/n8n-mcp) |
| **Telegram** | Telegram Bot API |
| **Курсы валют** | ЦБ РФ API (предположительно) |

---

## Проблемы (из чата)

### Проблема 1: Beget VPS — настройка через docker-compose
Сергей **не понимает**, как настроить Beget VPS. Изучал документацию Beget (https://beget.com/ru/kb/how-to/vps/), инструкции по SSH, шаблоны n8n.

**docker-compose файл (частично):**
```yaml
volumes:
  traefik_data:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/traefik_data
  n8n_storage:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/n8n_storage
  db_storage:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/db_storage
  redis_storage:
    driver: local-persist
    driver_opts:
      mountpoint: /opt/beget/n8n/redis_storage

x-shared: &shared
  restart: always
  image: docker.n8n.io/n8nio/n8n:2.17.7
  ...
```

### Проблема 2: Не понимает, как настроить переменные окружения
> «Мне кажется, что в моём плане нет переменных.»

### Проблема 3: n8n версия 2.17.7 — старые ноды
См. также [`n8n-телеграм-транскрибация.md`](./n8n-телеграм-транскрибация.md) — проблема с `executeCommand`.

### Проблема 4: LLM не использует системные инструкции
Сергей указывает: «я говорил, чтобы ты всегда обновлял файл с описанием контекста исполнения». LLM забывает.

---

## Решения (предложенные в чате)

1. **Использовать шаблоны Beget для n8n** (есть готовые).
2. **Документация Beget** по SSH, файловому менеджеру.
3. **LLM должен был обновлять** файл контекста после каждого изменения (не делал).

---

## Что сделано (на 2026-06-02)

- ✅ Workflow создан (в чате 45 сообщений — много итераций).
- ❓ Реально ли работает в продакшне — **неизвестно**.

---

## Оценка Mavis

**Состояние:** среднее. Много итераций, но без end-to-end теста.

**Главный риск:** Beget VPS + docker-compose — это **не для новичков**. Сергей, возможно, недооценивает сложность.

**Что я бы рекомендовал (если бы Сергей спросил):**
- **Платный n8n.cloud** (вместо self-hosted) для тестов. Потом мигрировать на Beget.
- **Managed Postgres** вместо docker-compose с локальным Postgres.
- **Traefik + SSL** — настроить правильно с первого раза (или это будет дыра в безопасности).

---

## Связанные файлы

- [`./n8n-телеграм-транскрибация.md`](./n8n-телеграм-транскрибация.md) — первый бот Сергея
- [`../companies/other.md`](../companies/other.md) (в `other.md`) — хостинг
