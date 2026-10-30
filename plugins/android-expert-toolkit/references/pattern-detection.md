# Pattern Detection and Decision Framework

## When to use

Read this reference when deciding whether to match existing codebase conventions or propose modern alternatives. Used by android-architect early in a review, and by android-developer before introducing patterns that diverge from what the project already uses. Detects existing patterns to ground decisions in codebase reality, not assumed conventions.

## Detection Commands

### State Management Patterns

```bash
# Detect LiveData usage
grep -r "LiveData<" --include="*.kt" --include="*.java" . | wc -l

# Detect StateFlow usage
grep -r "StateFlow<" --include="*.kt" . | wc -l

# Detect MutableLiveData
grep -r "MutableLiveData<" --include="*.kt" --include="*.java" . | wc -l

# Detect Flow usage
grep -r "Flow<" --include="*.kt" . | wc -l

# Detect RxJava usage (comprehensive)
grep -r "Single<\|Observable<\|Completable\|CompositeDisposable\|subscribeOn\|observeOn" --include="*.kt" --include="*.java" . | wc -l
```

### Dependency Injection Patterns

```bash
# Detect Hilt usage
grep -r "@HiltAndroidApp\|@HiltViewModel\|@Inject" --include="*.kt" --include="*.java" . | wc -l

# Detect Dagger usage
grep -r "@Component\|@Module\|@Provides" --include="*.kt" --include="*.java" . | wc -l

# Detect Koin usage (refined to avoid false positives)
grep -r "koinViewModel\|by inject()\|startKoin\|koinModule" --include="*.kt" . | wc -l

# Detect manual DI (ViewModel Factory pattern)
grep -r "ViewModelProvider.Factory\|ViewModelProvider.NewInstanceFactory\|class Factory.*ViewModel" --include="*.kt" . | wc -l
```

### Testing Patterns

```bash
# Detect Mockito usage
grep -r "@Mock\|mock(\|verify(" --include="*.kt" --include="*.java" . | wc -l

# Detect MockK usage
grep -r "mockk<\|every\|verify" --include="*.kt" . | wc -l

# Detect test doubles
grep -r "class Test.*Repository\|class Fake.*Repository\|class Test.*DataSource" --include="*.kt" . | wc -l

# Detect Turbine (Flow testing)
grep -r "\.test\s*{" --include="*.kt" . | wc -l

# Detect Truth assertions
grep -r "assertThat(" --include="*.kt" --include="*.java" . | wc -l

# Detect JUnit assertions
grep -r "assertEquals\|assertTrue\|assertNotNull" --include="*.kt" --include="*.java" . | wc -l
```

### Architecture Patterns

```bash
# Detect ViewModels
grep -r "ViewModel()" --include="*.kt" --include="*.java" . | wc -l

# Detect Compose usage
grep -r "@Composable" --include="*.kt" . | wc -l

# Detect XML layouts
find . -name "*.xml" -path "*/res/layout/*" | wc -l

# Detect Repository pattern
grep -r "interface.*Repository\|class.*Repository" --include="*.kt" --include="*.java" . | wc -l

# Detect UseCase pattern
grep -r "interface.*UseCase\|class.*UseCase" --include="*.kt" --include="*.java" . | wc -l

# Detect Activities
grep -r "class.*Activity\s*:" --include="*.kt" --include="*.java" . | wc -l

# Detect Fragments
grep -r "class.*Fragment\s*:" --include="*.kt" --include="*.java" . | wc -l

# Detect MVP Presenters (legacy pattern)
grep -r "Presenter\|: MvpView\|attachView" --include="*.kt" --include="*.java" . | wc -l
```

### Data Layer Patterns

```bash
# Detect Room usage
grep -r "@Database\|@Entity\|@Dao" --include="*.kt" --include="*.java" . | wc -l

# Detect DataStore usage
grep -r "DataStore<\|dataStore\|DataStoreFactory" --include="*.kt" . | wc -l

# Detect SharedPreferences
grep -r "SharedPreferences\|getSharedPreferences" --include="*.kt" --include="*.java" . | wc -l

# Detect Retrofit usage
grep -r "@GET\|@POST\|@PUT\|@DELETE" --include="*.kt" --include="*.java" . | wc -l
```

### Serialization Patterns

```bash
# Detect Moshi usage
grep -r "@Json\|@JsonClass" --include="*.kt" . | wc -l

# Detect Gson usage
grep -r "Gson\|@SerializedName" --include="*.kt" --include="*.java" . | wc -l

# Detect kotlinx.serialization usage
grep -r "@Serializable" --include="*.kt" . | wc -l
```

### Security Patterns

```bash
# Detect network security config
find . -name "network_security_config.xml" -path "*/res/xml/*" | wc -l

# Detect certificate pinning
grep -r "CertificatePinner" --include="*.kt" --include="*.java" . | wc -l

# Detect encrypted storage
grep -r "EncryptedSharedPreferences\|EncryptedFile\|MasterKey" --include="*.kt" . | wc -l   # androidx.security:security-crypto is deprecated: flag, don't recommend

# Detect hardcoded secrets (API keys, tokens in string literals)
grep -rn '"[A-Za-z0-9_-]\{32,\}"' --include="*.kt" . | grep -v "test\|Test\|mock\|Mock" | wc -l

# Detect ProGuard/R8 configuration
find . -name "proguard-rules.pro" -o -name "consumer-rules.pro" | wc -l

# Detect cleartext traffic permission
grep -r "cleartextTrafficPermitted\|usesCleartextTraffic" --include="*.xml" . | wc -l
```

### Performance Patterns

```bash
# Detect Baseline Profile configuration
find . -name "baseline-prof.txt" | wc -l
grep -r "BaselineProfileGenerator\|@BaselineProfileRule" --include="*.kt" . | wc -l

# Detect @Composable without remember for expensive operations
# (heuristic: listOf, mapOf, filter, sort inside @Composable without remember)
grep -rn "GlobalScope" --include="*.kt" . | wc -l

# Detect LazyColumn/LazyRow without key parameter
grep -rn "items(" --include="*.kt" . | grep -v "key\s*=" | wc -l

# Detect stateIn without WhileSubscribed in ViewModels
grep -rn "stateIn(" --include="*.kt" . | grep -v "WhileSubscribed" | wc -l

# Detect missing Dispatchers (potential main thread blocking)
grep -rn "withContext\|launch\|async" --include="*.kt" . | grep -v "Dispatchers\." | wc -l
```

### Accessibility Patterns

```bash
# Detect Icon/Image without contentDescription
grep -rn "Icon(" --include="*.kt" . | grep -v "contentDescription" | wc -l
grep -rn "Image(" --include="*.kt" . | grep -v "contentDescription" | wc -l

# Detect Modifier.semantics usage
grep -r "Modifier.semantics\|\.semantics {" --include="*.kt" . | wc -l

# Detect mergeDescendants usage
grep -r "mergeDescendants" --include="*.kt" . | wc -l

# Detect touch target sizes (clickable without minimum size)
grep -rn "\.clickable" --include="*.kt" . | wc -l
grep -rn "\.size.*48\.dp\|minimumInteractiveComponentSize" --include="*.kt" . | wc -l
```

### Language Distribution

```bash
# Count Kotlin files (main source set)
find . -name "*.kt" -path "*/src/main/*" | wc -l

# Count Java files (main source set)
find . -name "*.java" -path "*/src/main/*" | wc -l
```

## 80/20 Decision Matrix

### When to Match Existing Patterns (80%+ consistency)

| Pattern Type | Threshold | Action |
|--------------|-----------|--------|
| State Management | ≥80% LiveData | Use LiveData in new code |
| State Management | ≥80% StateFlow | Use StateFlow in new code |
| DI Framework | ≥80% Hilt | Use Hilt for new components |
| DI Framework | ≥80% Koin | Use Koin for new components |
| Testing Mocks | ≥80% Mockito | Use Mockito for new tests |
| Testing Mocks | ≥80% MockK | Use MockK for new tests |
| UI Framework | ≥80% Compose | Use Compose for new screens |
| UI Framework | ≥80% XML | Use XML for new layouts |
| Assertions | ≥80% Truth | Use Truth for new tests |
| Assertions | ≥80% JUnit | Use JUnit assertions |

### When to Propose Modern Alternatives (Mixed or <80%)

| Pattern Type | Condition | Recommendation |
|--------------|-----------|----------------|
| State Management | 50-79% LiveData + StateFlow | Propose migration plan to StateFlow |
| State Management | <50% consistency | Adopt StateFlow for all new features |
| DI Framework | Mixed Hilt + Koin | Consolidate to Hilt (official Android) |
| DI Framework | Manual DI present | Introduce Hilt incrementally |
| Testing | <50% test doubles | Prefer fakes for new tests; mocks only for final framework classes |
| Testing | Mixed mock frameworks | Standardize on one mock library for the cases that need mocks; fakes elsewhere |
| UI Framework | <30% Compose | Propose Compose for new features |
| Data Layer | SharedPreferences | Migrate to DataStore for new preferences |

### Calculation Formula

**IMPORTANT**: Calculate percentage within the pattern category, not against total files.

```bash
# CORRECT: Calculate LiveData vs StateFlow consistency
livedata_count=$(grep -r 'LiveData<\|MutableLiveData' --include='*.kt' --include='*.java' . | wc -l)
stateflow_count=$(grep -r 'StateFlow<\|MutableStateFlow' --include='*.kt' . | wc -l)
total=$((livedata_count + stateflow_count))

if [ $total -gt 0 ]; then
  livedata_pct=$(awk "BEGIN {printf \"%.1f\", ($livedata_count / $total) * 100}")
  stateflow_pct=$(awk "BEGIN {printf \"%.1f\", ($stateflow_count / $total) * 100}")
  echo "LiveData: $livedata_count occurrences ($livedata_pct%)"
  echo "StateFlow: $stateflow_count occurrences ($stateflow_pct%)"
else
  echo "No reactive state management detected"
fi
```

**Example for DI frameworks**:
```bash
hilt_count=$(grep -r '@HiltViewModel\|@HiltAndroidApp' --include='*.kt' . | wc -l)
koin_count=$(grep -r 'koinViewModel\|startKoin' --include='*.kt' . | wc -l)
dagger_count=$(grep -r '@Component\|@Module.*@Provides' --include='*.kt' --include='*.java' . | wc -l)
manual_count=$(grep -r 'ViewModelProvider.Factory' --include='*.kt' . | wc -l)
total_di=$((hilt_count + koin_count + dagger_count + manual_count))

if [ $total_di -gt 0 ]; then
  hilt_pct=$(awk "BEGIN {printf \"%.1f\", ($hilt_count / $total_di) * 100}")
  echo "Hilt: $hilt_count ($hilt_pct%)"
  echo "Koin: $koin_count ($(awk "BEGIN {printf \"%.1f\", ($koin_count / $total_di) * 100}")%)"
  echo "Manual DI: $manual_count ($(awk "BEGIN {printf \"%.1f\", ($manual_count / $total_di) * 100}")%)"
fi
```

## Pattern Detection Cache

### Cache Location

`.artifacts/aet/cache/detected-patterns.json`

### Cache Schema

```json
{
  "timestamp": "2026-03-18T17:00:00Z",
  "project_hash": "<hash of settings.gradle.kts + build.gradle.kts>",
  "patterns": {
    "di_framework": { "detected": "hilt", "confidence": 0.95, "evidence": ["app/build.gradle.kts:hilt-android"] },
    "state_management": { "detected": "stateflow", "confidence": 0.85, "evidence": ["ViewModel uses StateFlow"] },
    "ui_framework": { "detected": "compose", "confidence": 0.98, "evidence": ["app/build.gradle.kts:compose-bom"] }
  }
}
```

### Freshness Rules

- Cache is valid if `project_hash` matches current build files AND `timestamp` is <24 hours old
- Any change to `settings.gradle.kts` or root `build.gradle.kts` invalidates the cache (project structure changed)
- An explicit user choice overrides a cached value — record it with `confidence: 1.0`
- To force re-detection: delete the cache file or pass `--fresh` to the check command

### Computing `project_hash`

```bash
cat settings.gradle.kts build.gradle.kts 2>/dev/null | shasum -a 256 | cut -d' ' -f1
```

Only the root-level `settings.gradle.kts` and `build.gradle.kts` are included. Module-level build files are excluded — they change frequently without affecting which frameworks are in use.

The cache path is a stable contract: other tools read `.artifacts/aet/cache/detected-patterns.json`. Don't rename it or change existing keys.

## Decision Flowchart

```
1. Run detection commands
   ↓
2. Calculate consistency %
   ↓
3. Is consistency ≥80%?
   ↓
   YES → Match existing pattern
   ↓     Document with ARCHITECTURE_DECISION comment
   ↓     Note tech debt with TODO if legacy pattern
   ↓
   NO → Propose modern alternative
         Document rationale
         Provide migration path
         Get approval before implementing
```
