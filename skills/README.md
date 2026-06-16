---
title: Mavis-инструкции (skills)
tags: [meta, skills, Mavis]
created: 2026-06-16
status: stable
---
# Skills для Mavis

Эти 3 файла — **инструкции для ИИ-помощника Mavis** (а не для всех LLM). Они живут здесь как часть `llm_manifest`, чтобы:
- версионировались через git
- не потерялись при переезде Mavis
- могли расшариваться с другими Mavis-инстансами

## Состав

| Файл | Назначение |
|------|------------|
| [wiki-loader.md](./wiki-loader.md) | Подтягивает контекст среды (ENVIRONMENT + MISTAKES + AGENTS/COUNCIL) при задачах про автоматизацию |
| [wiki-curator.md](./wiki-curator.md) | После значимой задачи решает, обновлять ли вики, и коммитит напрямую (CAN-WRITE-FULL) |
| [gstack-team.md](./gstack-team.md) | 8-фазный спринт для multi-file/архитектурных работ |

## Как использовать

Mavis автоматически подхватывает файлы из `/workspace/.skills/<name>/SKILL.md` (своя локальная папка). Чтобы обновить:

```bash
# Синхронизировать из репо
cp /workspace/llm_manifest/skills/*.md /workspace/.skills/*/SKILL.md

# Или одной командой после git pull
cd /workspace/llm_manifest && for s in wiki-loader wiki-curator gstack-team; do
  cp skills/$s.md /workspace/.skills/$s/SKILL.md
done
```

## Версия

v1.0 — 2026-06-16
