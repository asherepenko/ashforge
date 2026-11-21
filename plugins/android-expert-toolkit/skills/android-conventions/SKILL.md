---
name: android-conventions
description: "Use when analyzing pattern consistency in an Android codebase — state management, dependency injection, testing, architecture, security, performance, or accessibility. Runs detection sweeps and applies the 80/20 decision matrix. Trigger on 'check patterns', 'which DI is used', 'state management consistency', 'audit Compose patterns', 'aet check'."
argument-hint: "[state | di | testing | architecture | security | performance | accessibility | all] [--fresh]"
---

# Android Expert Pattern Check

Run pattern detection from [pattern-detection](../../references/pattern-detection.md) against the current codebase. Reports consistency percentages and applies the 80/20 decision matrix. Counting is done by `scripts/detect-patterns.py`.

> **Platform notes:** Read-only apart from the cache file — uses shell and Read. No subagent dispatch, no interactive prompts. Works the same on every runtime (Claude Code, Codex, and others); substitute the runtime's shell tool where this says Bash.

## Pre-flight Context

Run `python3 scripts/preflight.py` from this skill's folder (the folder holding this SKILL.md), with the project root as the working directory. All probes emit labeled `== section ==` headers:

```bash
python3 <this-skill-folder>/scripts/preflight.py
```

The script collects: project hash (content hash of the scanned code and build files at any depth, the same value as `detect-patterns.py --hash`), cached patterns, Kotlin file count, DI fingerprint, state fingerprint, and testing fingerprint.

Use the output to:
1. Skip the cache compute step if the `Project hash` value matches cached `project_hash` (Step 1.5).
2. Sanity-check the counts later: the fingerprints show which markers exist (`@HiltAndroidApp` for DI, MockK or test doubles for testing, StateFlow/LiveData counts for state), so a detection result that contradicts them needs a look.

## Invocation

Claude: `/android-conventions di` or auto-trigger on natural-language prompts. Other runtimes: state intent naturally.

Examples:
```
/android-conventions              # Run all categories
/android-conventions state        # State management only
/android-conventions di           # Dependency injection only
/android-conventions testing      # Testing patterns only
/android-conventions architecture # Architecture patterns only
/android-conventions security     # Security patterns
/android-conventions performance  # Performance patterns
/android-conventions accessibility # Accessibility patterns
/android-conventions --fresh      # Force re-detection, ignore cache
/android-conventions di --fresh   # Re-detect specific category
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
   - Compare `project_hash` in cache with the `Project hash` from pre-flight
   - Check if `timestamp` is less than 24 hours old
   - If both match: **cache hit** — use cached patterns, skip to Step 4 (Report Results)
   - If either differs: **cache stale** — proceed to Step 2

The path and keys are a stable contract read by other tools; don't change them. Schema: [pattern-detection](../../references/pattern-detection.md) (section *Pattern Detection Cache*).

### 2. Run Detection

Run the counting script with the project root as `<project-dir>` and the requested categories (none = all). It also writes the cache, so a stale or missing cache is refreshed here:

```bash
python3 <this-skill-folder>/scripts/detect-patterns.py <project-dir> [category ...] --write-cache
```

Do not recount by hand or improvise patterns. The script holds the sweeps from [pattern-detection](../../references/pattern-detection.md) and prints `== section ==` blocks:

- `files_scanned=` — Kotlin and Java files under the project (build, generated and tooling directories pruned; test source sets kept).
- `decision <key>` — competing patterns in `state`, `di`, `testing` and `architecture`: one `<pattern> files=N share=P%` line each, then `dominant=… consistency=P% verdict=match|conflict|adopt|none`.
- `count <id> files=N` — sweeps that do not compete (every `security`, `performance` and `accessibility` sweep, plus `flow`, `turbine`, `repository`, `usecase`, `activity`, `fragment`).

A count is files with at least one match, not occurrences. Exit 2 means a usage error or a missing directory: fix the call, don't fall back to manual greps.

### 3. Read the Counts

Judgment stays with you:

- `verdict=none` → no evidence of that pattern; say so, don't infer one.
- Overlaps in the reference regexes can inflate a count, for example `@Module` appears in Hilt modules too, and `verify` matches Mockito as well as MockK. When a verdict hinges on one of these, open a few files from the cache `evidence` list or grep the sample before reporting.
- For `security`, `performance` and `accessibility`, read each count as a finding: non-zero `hardcoded_secrets`, `cleartext_traffic`, `global_scope`, `lazy_items_without_key`, `icon_without_content_description` or `image_without_content_description` need a named follow-up; zero `network_security_config`, `proguard_rules` or `baseline_profile_*` is a gap to mention.

### 4. Report Results

Format output as rendered markdown (real headings and tables, never inside a code fence; the fence below only shows the source):

```
## Pattern Detection Report

### State Management
| Pattern | Files | Share |
|---------|-------|-------|
| StateFlow | 45 | 82% |
| LiveData | 10 | 18% |

Consistency: 82% → **Match existing pattern (StateFlow)**

### Dependency Injection
| Pattern | Files | Share |
|---------|-------|-------|
| Hilt | 30 | 55% |
| Koin | 25 | 45% |

Consistency: 55% → **Pattern conflict (<80%) — consider standardization**
```

### 5. Apply 80/20 Matrix

Turn each `verdict` into advice:
- `match` (≥80%): "Match existing pattern — use [dominant] for new code"
- `conflict` (50-79%): "Pattern conflict — propose standardization on [recommended]"
- `adopt` (<50%): "No dominant pattern — adopt modern best practice: [recommendation]"

Modern best practice recommendations:
- State: StateFlow
- DI: Hilt (Android-only apps); Koin is reasonable for KMP
- Testing: fakes first; mocks only for final framework classes
- Architecture: Compose + MVVM/MVI
- Security: flag `androidx.security:security-crypto` (`EncryptedSharedPreferences`, `EncryptedFile`) as deprecated; see [security](../../references/security.md)

### 6. Summary

End with an overall summary:
- Categories checked
- Patterns with conflicts
- Recommended actions
- Reference to [pattern-detection](../../references/pattern-detection.md) for full decision framework

## Done means

- The report lists every category checked. `state`, `di`, `testing` and `architecture` show each decision's measured consistency percentage and matrix verdict (match / conflict / adopt); `security`, `performance` and `accessibility` show their counts and findings.
- Every number comes from `detect-patterns.py` file counts, shown in the report.
