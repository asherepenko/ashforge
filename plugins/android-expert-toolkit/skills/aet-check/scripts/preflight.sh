#!/usr/bin/env bash
# Pre-flight context for the aet-check skill.
# Output is labeled with `== section ==` headers. Probes run in parallel,
# each captured to its own temp file, then printed serially so section
# blocks never interleave on shared stdout.
# Use the output to:
#   1. Skip the cache compute step if hash matches cached project_hash (Step 1.5)
#   2. Decide whether full Grep sweep is needed (skip if file count < 50)
#   3. Pre-bias detection categories (e.g., DI fingerprint suggests Hilt → skip Koin/Dagger sweeps)
set -uo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

(
  echo "== Project hash =="
  if [ -f settings.gradle.kts ] || [ -f build.gradle.kts ]; then
    cat settings.gradle.kts build.gradle.kts 2>/dev/null \
      | shasum -a 256 | cut -d' ' -f1
  else
    echo "NO_GRADLE_FILES"
  fi
) > "$tmp/01" 2>&1 &

(
  echo "== Cached patterns =="
  if [ -f .artifacts/aet/cache/detected-patterns.json ]; then
    head -30 .artifacts/aet/cache/detected-patterns.json
  else
    echo "NO_CACHE"
  fi
) > "$tmp/02" 2>&1 &

(
  echo "== Kotlin file count =="
  find . -name '*.kt' \
    -not -path '*/build/*' -not -path '*/.gradle/*' 2>/dev/null \
    | wc -l | tr -d ' '
) > "$tmp/03" 2>&1 &

(
  echo "== DI fingerprint =="
  grep -rln --include='*.kt' \
    -E '@HiltAndroidApp|@HiltViewModel|startKoin\(|@Component' . 2>/dev/null \
    | head -5 || echo "NO_DI_MARKERS"
) > "$tmp/04" 2>&1 &

(
  echo "== State fingerprint (StateFlow|LiveData|MutableLiveData counts) =="
  grep -rcEh --include='*.kt' \
    '(StateFlow<|LiveData<|MutableLiveData<)' . 2>/dev/null \
    | awk -F: '{s+=$1} END{print s+0}'
) > "$tmp/05" 2>&1 &

(
  echo "== Testing fingerprint =="
  grep -rln --include='*.kt' \
    -E '@Test|mockk<|class Test[A-Z]|class Fake' . 2>/dev/null \
    | head -5 || echo "NO_TEST_MARKERS"
) > "$tmp/06" 2>&1 &

wait
cat "$tmp"/*
