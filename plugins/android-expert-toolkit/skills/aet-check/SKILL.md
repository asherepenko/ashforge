---
name: aet-check
description: "Use when analyzing pattern consistency in an Android codebase — state management, dependency injection, testing, architecture, security, performance, or accessibility. Runs detection sweeps and applies the 80/20 decision matrix. Trigger on 'check patterns', 'which DI is used', 'state management consistency', 'audit Compose patterns', 'aet check'."
argument-hint: "[state | di | testing | architecture | security | performance | accessibility | all] [--fresh]"
metadata:
  short-description: "Detect Android codebase pattern consistency with the 80/20 matrix"
---

# Android Expert Pattern Check

Run pattern detection from `${CLAUDE_PLUGIN_ROOT}/references/pattern-detection.md` against the current codebase. Reports consistency percentages and applies the 80/20 decision matrix.

> **Platform notes:** Pure read-only — uses Grep, Glob, Read, and shell. No subagent dispatch, no interactive prompts. Works identically on Claude and Codex. See `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` only if you need to substitute the shell tool name.

## Pre-flight Context

Run the pre-flight script — all probes parallelize and emit labeled `== section ==` headers:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-}}"
bash "$PLUGIN_ROOT/skills/aet-check/scripts/preflight.sh"
```

The script collects: project hash (shasum over settings.gradle.kts + build.gradle.kts), cached patterns, Kotlin file count, DI fingerprint, state fingerprint, and testing fingerprint.

Use the output to:
1. Skip the cache compute step if the `Project hash` value matches cached `project_hash` (Step 1.5).
2. Decide whether full Grep sweep is needed — if `Kotlin file count` < 50, single-pass detection suffices.
3. Pre-bias detection categories: if `DI fingerprint` shows `@HiltAndroidApp` → skip Koin/Dagger sweeps in the `di` category. Same logic for `Testing fingerprint` (MockK/Test doubles markers) and `State fingerprint` (StateFlow/LiveData counts).

## Invocation

Claude: `/aet-check di` or auto-trigger on natural-language prompts. Codex: state intent naturally.

Examples:
```
aet-check              # Run all categories
aet-check state        # State management only
aet-check di           # Dependency injection only
aet-check testing      # Testing patterns only
aet-check architecture # Architecture patterns only
aet-check security     # Security patterns
aet-check performance  # Performance patterns
aet-check accessibility # Accessibility patterns
aet-check --fresh      # Force re-detection, ignore cache
aet-check di --fresh   # Re-detect specific category
```

## Execution

### 1. Determine Category

Parse the `category` argument. Default to `all` if not provided.

Valid categories: `state`, `di`, `testing`, `architecture`, `security`, `performance`, `accessibility`, `all`

### 1.5. Check Cache

Before running detection, check for a valid cache at `.artifacts/aet/cache/detected-patterns.json`:

1. If `--fresh` flag is present, skip cache and proceed to Step 2
2. If cache file does not exist, proceed to Step 2
3. If cache file exists:
   - Compute current `project_hash`: `cat settings.gradle.kts build.gradle.kts 2>/dev/null | shasum -a 256 | cut -d' ' -f1`
   - Compare `project_hash` in cache with computed hash
   - Check if `timestamp` is less than 24 hours old
   - If both match: **cache hit** — use cached patterns, skip to Step 4 (Report Results)
   - If either differs: **cache stale** — proceed to Step 2

After detection completes (Step 3), write results to `.artifacts/aet/cache/detected-patterns.json` following the schema in `${CLAUDE_PLUGIN_ROOT}/references/pattern-detection.md` § Pattern Detection Cache.

### 2. Run Detection

For each category (or all), use the Grep tool to count pattern occurrences. Summary of what each category sweeps:

| Category | Patterns counted (summary) |
|----------|---------------------------|
| `state` | StateFlow vs LiveData/MutableLiveData vs Flow vs RxJava markers |
| `di` | Hilt vs Koin vs Dagger vs manual DI (`ViewModelProvider.Factory`) markers |
| `testing` | Mockito vs MockK vs test doubles (`Test*`/`Fake*`) vs Turbine usage |
| `architecture` | ViewModels, `@Composable` vs XML layouts, Repository and UseCase classes |
| `security` | network security config, certificate pinning, encrypted storage, hardcoded secrets, ProGuard/R8 config |
| `performance` | Baseline Profiles, missing `remember`, Lazy lists without stable `key`, `GlobalScope`, `stateIn` sharing policy |
| `accessibility` | `contentDescription` coverage, `Modifier.semantics`, touch target sizes, `mergeDescendants` |

Canonical sweep definitions (exact grep patterns, file globs, and counting rules): `${CLAUDE_PLUGIN_ROOT}/references/pattern-detection.md` — read it before running detection; do not improvise patterns from this table.

### 3. Calculate Consistency

For each category, calculate the consistency percentage within that category:
- Find the dominant pattern (highest count)
- Calculate: `dominant_count / total_count * 100`
- Apply 80/20 threshold

### 4. Report Results

Format output as:

```
## Pattern Detection Report

### State Management
| Pattern | Count | Percentage |
|---------|-------|-----------|
| StateFlow | 45 | 82% |
| LiveData | 10 | 18% |

Consistency: 82% → **Match existing pattern (StateFlow)**

### Dependency Injection
| Pattern | Count | Percentage |
|---------|-------|-----------|
| Hilt | 30 | 55% |
| Koin | 25 | 45% |

Consistency: 55% → **Pattern conflict (<80%) — consider standardization**
```

### 5. Apply 80/20 Matrix

For each category:
- **≥80% consistency**: "Match existing pattern — use [dominant] for new code"
- **50-79% consistency**: "Pattern conflict — propose standardization on [recommended]"
- **<50% consistency**: "No dominant pattern — adopt modern best practice: [recommendation]"

Modern best practice recommendations:
- State: StateFlow
- DI: Hilt
- Testing: Test doubles
- Architecture: Compose + MVVM

### 6. Summary

End with an overall summary:
- Categories checked
- Patterns with conflicts
- Recommended actions
- Reference to `${CLAUDE_PLUGIN_ROOT}/references/pattern-detection.md` for full decision framework
