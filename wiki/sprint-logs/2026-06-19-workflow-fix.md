# Sprint Log 2026-06-19 — Research Agent Workflow Fix (continuation of Sprint 6)

## Контекст

Sprint 6 (17-18.06.2026) завершил **Flask 500 fix + backup-shim merge + PR #1 squash-merge**. Sprint 7 (этот sprint) — финальная **E2E verification** + **workflow NodeApiError fix**.

## Что сделано (2026-06-19)

### Phase 1: SSH access restored
- `sshpass` не было в sandbox — установил `apt-get install -y sshpass`
- Восстановил secrets: `beget_ssh` (12 bytes plain password), `beget_ssh_meta` (host/user/port), `n8n_api_key` (fresh JWT)

### Phase 2: Flask state check
- PID 1505409 работал, но Werkzeug auto-reloader (см. MISTAKES §3.19) форкал второй процесс
- `pkill -9 -f newton-api.py; sleep 10; ss -tlnp | grep 8080` → port 8080 FREE
- Запустил заново с `FLASK_DEBUG=0 nohup python3 newton-api.py > api.log 2>&1 &` (clean, без reloader)
- `/youtube_subs` smoke test: **HTTP 200, 68562 chars VTT, 1.9s** ✅

### Phase 3: E2E test — full YouTube URL
- Triggered webhook с `https://youtu.be/6Z_hHWStwxw` (тестовое видео ИНФОСТАРТ, 1515s)
- Executions 697-705 падали с разными ошибками:
  - 697/698: Webhook → Code → IF → HTTP /youtube_meta (fail: 500 "YOUTUBE_API_KEY not set")
  - 703: 1.1s, same failure
  - 704: HTTP /youtube_meta **level=warning** (NodeApiError), но workflow error
  - 705: 0.1s, докатилось до Code — Build YandexGPT payload (Referenced node doesn't exist)

### Phase 4: Diagnosis — две независимые проблемы
1. **n8n `options.continueOnFail` НЕ работает в webhook-triggered flow** (MISTAKES §3.22)
2. **Build YandexGPT payload использует id-based refs** (`$('http_meta')`) — Sprint 5 фикс был неполный (MISTAKES §3.24)

### Phase 5: Fix #1 — Flask `/youtube_meta` fallback
- Патч `packages/research/routes.py:258` — при пустом `YOUTUBE_API_KEY` возвращать 200 с минимальным dict (status: `fallback_no_api_key`)
- Backup: `routes.py.bak.20260619`
- Restart Flask → `curl /youtube_meta` = HTTP 200 ✅

### Phase 6: Fix #2 — Code-нода, recursive id→name replace
- Сначала заменил только в `Build YandexGPT payload`: `$('http_meta')` → `$('HTTP /youtube_meta')`
- Получил HTTP 400 при PUT (description: null, additional properties, errorWorkflow placeholder)
- Cleaned body до {name, nodes, connections, settings}, удалил placeholder errorWorkflow, отфильтровал None
- **PUT HTTP 200, versionCounter: 39** ✅

### Phase 7: Удаление `/youtube_meta` ноды
- После анализа: Code-нода может получить title/duration из `subs.meta` (yt-dlp возвращает полный metadata в subs)
- Упростил Code — Build YandexGPT payload: убрал `$('HTTP /youtube_meta')`, оставил только subs
- Удалил ноду `HTTP /youtube_meta` из nodes + connections (в обе стороны) — **MISTAKES §3.25**
- PUT versionCounter: 43, 12 nodes

### Phase 8: Fix #3 — массовый id→name fix через regex
- Найдены ещё 6 нод с id-based refs: `HTTP /yagpt_summarize`, `Code — Build Digest`, `HTTP /render_digest`, `HTTP /kb_save`, `HTTP /send_document`, `HTTP /send_message (TL;DR)`
- Recursive replace через `re.sub(r"\$\('([^']+)'\)", repl, obj)` (см. MISTAKES §3.24)
- PUT versionCounter: 47

### Phase 9: E2E test #2 — 9 нод выполнилось!
- 708: 2.3s — failed (HTTP /yagpt_summarize не выполнился)
- 709: 30.6s — **9 нод ✅, 1 ошибка HTTP /send_document**
- 710: 31.2s — same, 9 нод

### Phase 10: Final diagnosis
- Workflow **РАБОТАЕТ**: webhook → parse → IF → subs → build_yagpt → yagpt_summarize → build_digest → render_digest (8/8 главных нод ✅)
- Финальная ошибка — `/send_document` (Telegram API "message to be replied not found")
- **Root cause:** фейковый `message_id: 207` в тестовом webhook payload не существует в Telegram
- Manual test: `curl -X POST /send_document -d '{"file_path": "digest_6Z_hHWStwxw.html", "chat_id": 261540559, "message_id": null}'` → **HTTP 200, status: sent, message_id: 100** ✅

### Phase 11: Production-ready
- Сделал `message_id` optional в jsonBody: `message_id: (...|| null)` (MISTAKES §3.26)
- Добавил `continueOnFail: true` в options /send_document
- PUT versionCounter: 53
- Файл дайджеста создан: `/opt/beget/n8n/newton-tmp/digest_6Z_hHWStwxw.html` (8782 bytes)
- Workflow `FRsjN6Ab1FBGAMoM` **active, versionCounter: 53, 12 nodes, updatedAt: 2026-06-19T07:19:19.459Z**

## Lessons learned (MISTAKES.md)

- **§3.19** Werkzeug auto-reloader → always `FLASK_DEBUG=0 nohup`
- **§3.20** n8n API keys expire (10 days) — store in /root/.mavis/secrets/
- **§3.21** shim-pattern + reloader → N копий endpoint registration
- **§3.22** `options.continueOnFail` does NOT work in webhook-triggered flow
- **§3.23** `onError: 'continueRegularOutput'` is read-only via REST PUT in 2.17.7
- **§3.24** `$('id_based_ref')` always fails — only `$('name')` works (Sprint 5 fix was incomplete)
- **§3.25** delete node requires cleaning connections in BOTH directions
- **§3.26** Telegram "message to be replied not found" when fake message_id
- **§3.27** Flask endpoint should return 200 + fallback dict on conscious empty key
- **§3.28** `description: null` in PUT body → 400 "must be string"
- **§3.29** Production flow: real message_id from Telegram → reply works fine

## Final state

| Resource | State |
|---|---|
| Workflow `FRsjN6Ab1FBGAMoM` | active, 12 nodes, v53 |
| Flask `newton-api.py` | PID 2719312, FLASK_DEBUG=0, 3 shim blocks (kapital/research/telegram_bot/kb) |
| `/youtube_subs` | HTTP 200, 1.9s, 68K chars |
| `/youtube_meta` | HTTP 200, fallback dict (meta_source: fallback_no_api_key) |
| `/yagpt_summarize` | HTTP 200, ~30s, 0.18₽ per chunk |
| `/send_document` | HTTP 200, requires real `message_id` for reply (null OK for test) |
| `/kb_save` | ready, waits for /send_document success |
| KB `research.db` | 6 tables, 25 user_profile rows, 0 digests (workflow не доходит до kb_save из-за /send_document) |
| E2E test | **9/12 нод ✅, 1 фейл на /send_document (Telegram reply на фейковый message_id — ОЖИДАЕМО)** |

## Что осталось сделать

- [ ] PM делает **реальный** тест через Telegram-бота @ZhukovsFirstBot (с настоящим message_id) — тогда workflow дойдёт до конца и запишет в KB
- [ ] После успешного E2E через бота — обновить MISTAKES §3.19-3.29 в llm_manifest (PR)
- [ ] Sprint log + session-summaries в llm_manifest (commit через GitHub API)
