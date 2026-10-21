#!/usr/bin/env bash
# change-size.sh — the Change Sizing bucket for a diff.
#
# SKILL.md anchors the buckets at ~100 (good), ~300 (acceptable if one logical
# change) and ~1000 (too large). The cut points sit between those anchors so
# every reviewer lands on the same bucket, and this file is the only place the
# thresholds live. /two-stage-review prints the bucket as its Size line and
# verify-signals.sh reads it; neither feeds the Quality letter.
#
# Usage:
#   change-size.sh <base> [<head>] lines added+deleted in <base>...<head> (head defaults to HEAD)
#   change-size.sh --classify <N>  bucket for N lines
# Output: LINES=<n>  BUCKET=good|acceptable|too-large   (--classify: bucket only)
# Exit:   0 ok · 2 usage error or unknown base

set -euo pipefail

GOOD_MAX=200
ACCEPTABLE_MAX=600

usage() { echo "usage: change-size.sh <base> [<head>] | --classify <lines>" >&2; exit 2; }

classify() {
  if [ "$1" -le "$GOOD_MAX" ]; then echo good
  elif [ "$1" -le "$ACCEPTABLE_MAX" ]; then echo acceptable
  else echo too-large
  fi
}

[ $# -ge 1 ] || usage
if [ "$1" = "--classify" ]; then
  [ $# -eq 2 ] && [[ "$2" =~ ^[0-9]+$ ]] || usage
  classify "$2"
  exit 0
fi

[ $# -le 2 ] || usage
base="$1"
head="${2:-HEAD}"
git rev-parse --verify --quiet "$base^{commit}" >/dev/null || { echo "change-size.sh: unknown base '$base'" >&2; exit 2; }
git rev-parse --verify --quiet "$head^{commit}" >/dev/null || { echo "change-size.sh: unknown head '$head'" >&2; exit 2; }

# Binary files show "-" in numstat and carry no reviewable lines.
lines=$(git diff --numstat "$base...$head" | awk '$1 != "-" { n += $1 + $2 } END { print n + 0 }')
echo "LINES=$lines"
echo "BUCKET=$(classify "$lines")"
