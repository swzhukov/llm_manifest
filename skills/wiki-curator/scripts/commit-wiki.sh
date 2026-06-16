#!/usr/bin/env bash
# commit-wiki.sh — safe commit+push для swzhukov/llm_manifest
# Использование: bash commit-wiki.sh "<commit-message>" [file1 file2 ...]
# Если файлы не указаны — коммитит все изменения.

set -euo pipefail

REPO_DIR="/workspace/llm_manifest"
cd "$REPO_DIR"

# Проверка remote
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "❌ Remote 'origin' не настроен. Сначала: git remote add origin https://github.com/swzhukov/llm_manifest.git"
  exit 1
fi

# Проверка токена (есть GITHUB_LLM_MANIFEST_TOKEN)
if [[ -z "${GITHUB_LLM_MANIFEST_TOKEN:-}" ]]; then
  echo "⚠️  GITHUB_LLM_MANIFEST_TOKEN не задан. Push может потребовать ручной аутентификации."
fi

# Сообщение коммита
MSG="${1:-wiki: auto-update}"
shift || true

echo "→ git status"
git status --short

# Fetch + rebase чтобы не было конфликтов
echo "→ git fetch origin"
git fetch origin 2>&1 | tail -2

echo "→ git pull --rebase"
if ! git pull --rebase origin main 2>&1 | tail -3; then
  echo "❌ Rebase failed. Возможно remote изменился. Покажи пользователю."
  exit 2
fi

# Добавляем файлы
if [[ $# -gt 0 ]]; then
  echo "→ git add $@"
  git add "$@"
else
  echo "→ git add -A"
  git add -A
fi

# Проверка что есть что коммитить
if git diff --cached --quiet; then
  echo "✓ Нет изменений для коммита."
  exit 0
fi

# Dry-run: показать что будет в коммите
echo ""
echo "=== Содержимое коммита (git diff --cached --stat) ==="
git diff --cached --stat
echo ""

# Коммит
echo "→ git commit -m \"$MSG\""
git commit -m "$MSG"

SHA=$(git rev-parse HEAD)
echo "✓ Commit: $SHA"

# Push с retry
echo "→ git push origin main"
for attempt in 1 2; do
  if git push origin main 2>&1 | tail -5; then
    echo ""
    echo "✅ Запушено: $SHA"
    echo "   https://github.com/swzhukov/llm_manifest/commit/$SHA"
    exit 0
  else
    echo "⚠️  Push failed (попытка $attempt/2). Retry через 5 секунд..."
    sleep 5
  fi
done

echo "❌ Push failed после 2 попыток. Commit остался локально. Покажи пользователю:"
echo "   cd $REPO_DIR && git push origin main"
exit 3
