---
name: aet-check
description: Run pattern detection against the codebase to analyze consistency and recommend approaches
argument-hint: "[state (management) | di (injection) | testing (coverage) | architecture (layers) | security | performance | accessibility | all]"
allowed-tools: Grep, Glob, Read, Bash(cat:*), Bash(shasum:*), Bash(find:*), Bash(wc:*), Bash(grep:*)
---

# Android Expert Pattern Check

Run pattern detection from `references/pattern-detection.md` against the current codebase. Reports consistency percentages and applies the 80/20 decision matrix.

## Pre-flight Context

Cheap codebase fingerprint pre-loaded via shell expansion (parallel, capped output):

- **Project hash**: !`bash -c 'if [ -f settings.gradle.kts ] || [ -f build.gradle.kts ]; then cat settings.gradle.kts build.gradle.kts 2>/dev/null | shasum -a 256 | cut -d" " -f1; else echo NO_GRADLE_FILES; fi'`
- **Cached patterns**: !`bash -c 'if [ -f .artifacts/aet/cache/detected-patterns.json ]; then head -30 .artifacts/aet/cache/detected-patterns.json; else echo NO_CACHE; fi'`
- **Kotlin file count**: !`find . -name '*.kt' -not -path '*/build/*' -not -path '*/.gradle/*' 2>/dev/null | wc -l | tr -d ' '`
- **DI fingerprint**: !`grep -rln --include='*.kt' -E '@HiltAndroidApp|@HiltViewModel|startKoin\(|@Component' . 2>/dev/null | head -5`
- **State fingerprint**: !`grep -rcEh --include='*.kt' '(StateFlow<|LiveData<|MutableLiveData<)' . 2>/dev/null | awk -F: '{s+=$1} END{print s+0}'`

Use this fingerprint to:
1. Skip cache compute step if hash matches cached `project_hash` (Step 1.5).
2. Decide whether full Grep sweep is needed — if file count < 50, single-pass detection suffices.
3. Pre-bias detection categories: if DI fingerprint shows `@HiltAndroidApp` → skip Koin/Dagger sweeps in `di` category.

## Usage

```bash
/aet-check              # Run all categories
/aet-check state        # State management only
/aet-check di           # Dependency injection only
/aet-check testing      # Testing patterns only
/aet-check architecture # Architecture patterns only
/aet-check security     # Security patterns
/aet-check performance  # Performance patterns
/aet-check accessibility # Accessibility patterns
/aet-check --fresh      # Force re-detection, ignore cache
/aet-check di --fresh   # Re-detect specific category
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

After detection completes (Step 3), write results to `.artifacts/aet/cache/detected-patterns.json` following the schema in `references/pattern-detection.md` § Pattern Detection Cache.

### 2. Run Detection

For each category (or all), use the Grep tool to count pattern occurrences:

**State Management** (`state`):
- Count `LiveData<` in `*.kt` and `*.java` files
- Count `StateFlow<` in `*.kt` files
- Count `MutableLiveData<` in `*.kt` and `*.java` files
- Count `Flow<` in `*.kt` files
- Count RxJava markers (`Single<`, `Observable<`, `Completable`) in `*.kt` and `*.java` files

**Dependency Injection** (`di`):
- Count Hilt markers (`@HiltAndroidApp`, `@HiltViewModel`, `@Inject`) in `*.kt` files
- Count Koin markers (`koinViewModel`, `by inject()`, `startKoin`) in `*.kt` files
- Count Dagger markers (`@Component`, `@Module`, `@Provides`) in `*.kt` and `*.java` files
- Count Manual DI (`ViewModelProvider.Factory`) in `*.kt` files

**Testing** (`testing`):
- Count Mockito (`@Mock`, `mock(`) in `*.kt` and `*.java` files
- Count MockK (`mockk<`, `every `) in `*.kt` files
- Count Test Doubles (`class Test.*Repository`, `class Fake`) in `*.kt` files
- Count Turbine (`.test {`) in `*.kt` files

**Architecture** (`architecture`):
- Count ViewModels (`ViewModel()`) in `*.kt` files
- Count Composables (`@Composable`) in `*.kt` files
- Count XML layouts in `*/res/layout/*.xml`
- Count Repository interfaces/classes in `*.kt` files
- Count UseCase classes in `*.kt` files

**Security** (`security`):
- Check `network_security_config.xml` presence in `*/res/xml/`
- Count `CertificatePinner` usage in `*.kt` and `*.java` files
- Count `EncryptedSharedPreferences` or `EncryptedFile` usage in `*.kt` files
- Detect hardcoded secrets: strings matching API key patterns (`[A-Za-z0-9]{32,}` in string literals) in `*.kt` files
- Check ProGuard/R8 configuration: `proguard-rules.pro` or `consumer-rules.pro` presence

**Performance** (`performance`):
- Check Baseline Profile configuration: `baseline-prof.txt` or `BaselineProfileGenerator` in `*.kt` files
- Detect `@Composable` functions without `remember` for expensive calculations in `*.kt` files
- Detect `LazyColumn`/`LazyRow` without stable `key` parameter in `*.kt` files
- Count `GlobalScope` usage (anti-pattern) in `*.kt` files
- Detect `stateIn` without `SharingStarted.WhileSubscribed` in ViewModel files

**Accessibility** (`accessibility`):
- Count `contentDescription` presence on `Icon` and `Image` composables in `*.kt` files
- Count `Modifier.semantics` usage in `*.kt` files
- Detect touch target sizes: `Modifier.size` with values < 48.dp near clickable modifiers
- Count `mergeDescendants` usage in `*.kt` files

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
- Reference to `references/pattern-detection.md` for full decision framework
