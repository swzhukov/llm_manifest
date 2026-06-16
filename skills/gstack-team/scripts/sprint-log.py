#!/usr/bin/env python3
"""
sprint-log.py — генератор sprint-log.md для gstack-team
Использование:
  python3 sprint-log.py \\
    --task "feature-x" \\
    --mode "Hold Scope" \\
    --worktree "../feature-x" \\
    --phases "1:design,2:arch,4:build,5:review,7:ship" \\
    --decisions "Used n8n HTTP node;Webhook polling;Skipped admin" \\
    --deferred "Admin panel;Email fallback" \\
    --learnings "1C: refresh token before request;gstack-learnings/1c-http" \\
    --out sprint-log.md
"""
import argparse
from datetime import date


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, help="Имя задачи (kebab-case)")
    p.add_argument("--mode", required=True,
                   choices=["Expansion", "Selective Expansion", "Hold Scope", "Reduction"])
    p.add_argument("--worktree", default="(no worktree)")
    p.add_argument("--phases", default="",
                   help="Список фаз через запятую: '1:design,2:arch,4:build,5:review,7:ship'")
    p.add_argument("--decisions", default="", help="Решения через ';'")
    p.add_argument("--deferred", default="", help="Отложенное через ';'")
    p.add_argument("--learnings", default="", help="Находки для memory через ';'")
    p.add_argument("--out", default="sprint-log.md", help="Путь к выходному файлу")
    args = p.parse_args()

    today = date.today().isoformat()

    phases_done = []
    for item in args.phases.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            num, name = item.split(":", 1)
            phases_done.append(f"- [x] Phase {num.strip()} ({name.strip()})")
        else:
            phases_done.append(f"- [x] Phase {item.strip()}")
    phases_block = "\n".join(phases_done) if phases_done else "- [ ] Phases не указаны"

    decisions_block = "\n".join(
        f"- {d.strip()}" for d in args.decisions.split(";") if d.strip()
    ) or "- (не заполнено)"

    deferred_block = "\n".join(
        f"- {d.strip()}" for d in args.deferred.split(";") if d.strip()
    ) or "- (не заполнено)"

    learnings_block = "\n".join(
        f"- {l.strip()}" for l in args.learnings.split(";") if l.strip()
    ) or "- (не заполнено)"

    content = f"""# Sprint log: {args.task}
**Date:** {today}
**Mode:** {args.mode}
**Worktree:** {args.worktree}
**Status:** shipped

## Phases run
{phases_block}

## Решения
{decisions_block}

## Отложено (backlog → Phase 2)
{deferred_block}

## Ключевые находки → memory / wiki
{learnings_block}
"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✓ Создан: {args.out}")
    print(f"  Size: {len(content)} bytes")


if __name__ == "__main__":
    main()
