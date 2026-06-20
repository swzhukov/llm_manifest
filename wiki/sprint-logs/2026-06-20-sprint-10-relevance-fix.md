# Sprint 10 — Relevance-check + inline-кнопки (2026-06-20)

## Sprint 10.0 — _build_investor_prompt v6.0.13 (relevance check)

### Проблема
PM прислал 2 разбора. Видео Мрочковского (релевантное) — ОК. Видео Гильбо про обеднённый уран (off_topic) — бот галлюцинировал actions: «проверить акции атомщиков», «ОФЗ», conf 0.6-0.8. Видео вообще НЕ про инвестиции.

### Root cause
v6.0.6 prompt говорил: «ВИДЕО МОЖЕТ БЫТЬ НЕ ПРО ИНВЕСТИЦИИ — actions всё равно выдавай, привязывай к watchlist». LLM трактовало как «всегда выдавай 3 actions».

### Fix v6.0.13
2-step prompt:
1. **RELEVANCE-CHECK** — явные критерии on_topic vs off_topic
2. **ВЫДАЧА** — on_topic: 5 буллетов + 3 actions; off_topic: 1-2 буллета + actions=[] + conf=0.0

### Test results
- Гильбо (off_topic): `relevance=off_topic, actions=[]` ✅
- Мрочковский (on_topic): `relevance=on_topic, 5 буллетов, 3 actions` ✅ (первый fix давал false negative; после расширения on_topic примерами — OK)

### Files changed
- `/opt/beget/n8n/research-agent/packages/research/routes.py` (_build_investor_prompt)

### Commits
- MISTAKES §3.38
- sprint-10 log
