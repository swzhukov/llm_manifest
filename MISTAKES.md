

### 3.63 ✅ Sprint 21 — retry-storm fix: dedup + immediate 200 OK (2026-06-23)

**Когда:** 2026-06-23 — PM прислал 1 Rutube URL → бот прислал 7-12 одинаковых дайджестов + 2-3 "Понял, обрабатываю Rutube..." за 10 минут.

**Корневая причина:** 
- Telegram webhook **ожидает ответ за 5 сек**, иначе ретраит update_id
- Наш workflow 30-90 сек (YouTube/VK) — Telegram продолжает слать тот же update
- n8n запускает новый execution на каждый retry → 7-12 executions на 1 URL
- Respond to Webhook был только в конце flow → Telegram видел timeout

**Доказательство (exec 1990-2002 за 10 мин):**
- update_id 104907032 → **12 executions** на 1 PM message (msg_id=661, Rutube)
- Каждый exec: 28-32 sec, status=success
- PM получил: 12× "Понял, обрабатываю Rutube..." + 12× дайджест + 12× TL;DR

**Что сделал:**

#### 1. **/send_message (ack) → Respond to Webhook (immediate 200 OK)**
- Ack отправляется в Telegram (~1 сек) → Respond → 200 OK Telegram моментально
- Дальнейшая обработка (30-90 сек) идёт асинхронно, Telegram не ретраит
- IF needs_ack false branch → Respond to Webhook (тоже сразу 200)
- Тест: ack path duration 1 sec (был 30-90)

#### 2. **HTTP /seen_update endpoint (Flask)**
- `POST /seen_update {update_id}` → `{seen: bool, update_id, age}`
- SQLite таблица `seen_updates (update_id PK, ts)` с TTL 5 мин
- Atomic check-then-insert, нет race condition

#### 3. **Code — Parse Command v6.0.27 (новая нода)**
- В начале: HTTP /seen_update с update_id из webhook body
- Если `seen: true` → возвращает `{deduped: true, cmd: 'duplicate', _route: 'help'}`
- Code — Build help/error msg: silent skip при deduped (text=empty, без Telegram send)

#### 4. **HTTP /send_message (help) silent skip**
- jsonBody: `...($json.text ? {} : {text: "(empty)"})` — не отправляет Telegram 400 Bad Request
- Помогает dedup case (text пустой) и не спамит

#### 5. **n8n staticData bug**
- `$getWorkflowStaticData('global')` имеет per-execution scope, не делится между executions
- Поэтому staticData dedup не работает. Нужен HTTP /seen_update.

**Тест 3 retry YouTube (update_id 104910006):**
- exec 2042 (08:30:05 → 08:30:30): cmd=fetch, обрабатывает 25 сек
- exec 2043 (08:30:08 → 08:30:10): cmd=duplicate, deduped=True, 2 сек
- exec 2044 (08:30:12 → 08:30:13): cmd=duplicate, deduped=True, 2 сек
- **PM получил 1 дайджест** вместо 3

**Reusable lesson 3.63.1:** **Telegram webhook timeout = 5 сек**. Если workflow > 5 сек — ОБЯЗАТЕЛЬНО Respond to Webhook сразу после ack. Иначе retry storm.

**Reusable lesson 3.63.2:** **n8n `$getWorkflowStaticData('global')`** имеет per-execution scope. Не работает для dedup между executions. Используй HTTP/Flask + SQLite.

**Reusable lesson 3.63.3:** **n8n Code node с `await this.helpers.httpRequest(...)`** — современный API. Не `this.helpers.httpRequest(...)` без await (потеряется response). С `returnFullResponse: false` возвращает parsed JSON.

**Reusable lesson 3.63.4:** **n8n Code node cache** — `jsCode` иногда не обновляется через PUT. Workaround: переименовать `node.id` (suffix `-v6-0-27-seen-update`) → n8n видит как новую ноду.

**Reusable lesson 3.63.5:** При **переименовании ноды** в n8n — ВСЕ `$('Old Name')` в jsCode других нод надо обновить. Иначе silent fail: "Referenced node doesn't exist" в HTTP Request nodes.

**Дата:** 23.06.2026.
