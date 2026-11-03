#!/usr/bin/env bash
# Print the architecture verdict (NEW, TCA, MVVM or MIXED) for an iOS project directory.
# Sweep patterns are defined in references/pattern-detection.md; keep them identical.
set -euo pipefail

dir="${1:?usage: run-sweeps.sh <project-dir>}"

PAT_TCA='@Reducer'
PAT_MVVM_OBSERVABLE='@Observable([^A-Za-z]|$)'
PAT_MVVM_OBJECT='class[^{]*:[^{]*ObservableObject'
PAT_UIKIT='class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*:[[:space:]]*UI[A-Za-z]*ViewController'

files="$(find "$dir" \( -name Pods -o -name Carthage -o -name .build -o -name SourcePackages \
  -o -name '*Tests' -o -name '*Preview*' \) -prune -o -type f -name '*.swift' -print)"

matching() {
  [ -z "$files" ] && return 0
  printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 grep -lE "$1" 2>/dev/null || true
}

tca=$(matching "$PAT_TCA" | wc -l | tr -d ' ')
mvvm=$( { matching "$PAT_MVVM_OBSERVABLE"; matching "$PAT_MVVM_OBJECT"; } | sort -u | wc -l | tr -d ' ')
uikit=$(matching "$PAT_UIKIT" | wc -l | tr -d ' ')

feature=0
if [ -n "$files" ]; then
  while IFS= read -r f; do
    [ "$(basename "$f")" = "ContentView.swift" ] && continue
    grep -q '@main' "$f" && continue
    feature=$((feature + 1))
  done <<< "$files"
fi

total=$((tca + mvvm + uikit))
echo "tca=$tca mvvm=$mvvm uikit=$uikit feature_files=$feature" >&2

if [ "$feature" -eq 0 ]; then
  echo NEW
elif [ "$total" -gt 0 ] && [ $((tca * 10)) -ge $((8 * total)) ]; then
  echo TCA
elif [ "$total" -gt 0 ] && [ $(((mvvm + uikit) * 10)) -ge $((8 * total)) ]; then
  echo MVVM
else
  echo MIXED
fi
