#!/usr/bin/env bash
# Pre-flight context for the council-code-review skill.
# Output is labeled with `== section ==` headers. All probes parallelize.
# Use the output to bound review scope before Step 1 — if working tree is
# clean and no commits ahead, there is no `--diff` to review.
set -uo pipefail

resolve_base() {
  git merge-base HEAD origin/main 2>/dev/null \
    || git merge-base HEAD main 2>/dev/null \
    || git merge-base HEAD master 2>/dev/null \
    || echo ""
}

(
  echo "== Current branch =="
  git branch --show-current 2>/dev/null || echo "NOT_A_REPO"
) &

(
  echo "== Working tree status =="
  git status -s 2>/dev/null | head -40 || echo "NO_REPO"
) &

(
  echo "== Diff stat (vs base) =="
  BASE="$(resolve_base)"
  if [ -z "$BASE" ]; then
    echo "NO_BASE"
  else
    git diff --stat "$BASE"...HEAD 2>/dev/null | tail -30
  fi
) &

(
  echo "== Commits ahead =="
  BASE="$(resolve_base)"
  if [ -z "$BASE" ]; then
    echo "NONE"
  else
    git log --oneline "$BASE"..HEAD 2>/dev/null | head -20
  fi
) &

(
  echo "== Project markers =="
  ls build.gradle.kts package.json pyproject.toml go.mod Cargo.toml settings.gradle.kts 2>/dev/null \
    || echo "NO_MARKERS"
) &

(
  echo "== Recent reviews =="
  ls -1t .artifacts/reviews/*.md 2>/dev/null | head -5 || echo "NO_REVIEWS"
) &

wait
