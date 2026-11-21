# iOS Pattern Detection and Decision Framework

## When to use

Read this before deciding whether new iOS code should match the codebase's existing architecture or follow the toolkit default. The `/ios-conventions` skill runs these sweeps. This file is the single source for the sweep patterns; `skills/ios-conventions/scripts/detect-patterns.py` implements every sweep below and a test keeps its patterns identical to this file.

## Architecture sweep (counts files)

Count files, not matches. Match code only: the script blanks comments and the contents of string literals first, so `// @Reducer` and `"Factory"` never count (the `rg` commands below do not, so check their hits by eye). Exclude `Pods/`, `Carthage/`, `.build/`, `SourcePackages/`, any `*Tests` directory, and any `*Preview*` path.

| Id | Meaning | Pattern (ERE) |
|----|---------|---------------|
| TCA | File declares a reducer (`@ReducerBuilder` does not match) | `@Reducer([^A-Za-z0-9_]\|$)` |
| MVVM_OBSERVABLE | File has an `@Observable` class (view state). `@ObservableState` is TCA and does not match | `@Observable([^A-Za-z0-9_]\|$)` |
| MVVM_OBJECT | File declares a class conforming to `ObservableObject`. A generic constraint (`Box<T: ObservableObject>`), `ObservableObjectPublisher` and `class func` do not match | `(^\|[^A-Za-z0-9_])class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*(<[^{]*>)?[[:space:]]*:([^{]*[^A-Za-z0-9_])?ObservableObject([^A-Za-z0-9_]\|$)` |
| UIKIT | File subclasses a `UIViewController`. `UIViewControllerRepresentable` and `UIViewControllerTransitioningDelegate` do not match | `(^\|[^A-Za-z0-9_])class[[:space:]]+[A-Za-z0-9_]+[[:space:]]*:[[:space:]]*UI[A-Za-z]*ViewController([^A-Za-z0-9_]\|$)` |

The `\|` in these rows is table escaping; the real pattern is, for example, `@Reducer([^A-Za-z0-9_]|$)`.

MVVM = files matching MVVM_OBSERVABLE or MVVM_OBJECT (a file counts once). A class need not be named `*Model` or `*ViewModel`.

Reference run: `python3 skills/ios-conventions/scripts/detect-patterns.py <project-dir> architecture` prints the file counts and one `verdict_architecture=` line.

```
total = TCA + MVVM + UIKit
NEW    no Swift file beyond the Xcode template (the @main App file and ContentView.swift)
TCA    TCA / total >= 0.8
MVVM   (MVVM + UIKit) / total >= 0.8
MIXED  everything else, including a project with code but zero signal
```

The 80% test is integer math (`TCA*10 >= 8*total`), so exactly 80% counts as dominant.

## Decision rule

| Verdict | What new feature code does |
|---------|----------------------------|
| NEW | TCA required |
| TCA | TCA for new features (share is 80% or more) |
| MVVM | Never force TCA; follow the existing MVVM/UIKit pattern |
| MIXED | Follow the dominant local pattern in the feature's folder; TCA only on request |

## Other sweeps

Run with `rg` from the project root, with the same exclusions as above unless noted. `detect-patterns.py` runs the same patterns over `.swift` files.

### Audit: what each sweep can miscount

Patterns match single lines of code (comments and strings blanked). Risk is a match that is not the framework the sweep names.

| Sweep | Risk before | Handling |
|-------|-------------|----------|
| `@Reducer` | comments and strings; `@ReducerBuilder` | fixed: code only, word boundary |
| `@Observable` | comments; `@Observable2`-style suffixes | fixed: code only, full word boundary. `@ObservableState` already excluded |
| `ObservableObject` class | `Box<T: ObservableObject>: NSObject`, `class func f(x: ObservableObject)`, `ObservableObjectPublisher`, comments | fixed: class name, optional generics, then conformance after the colon |
| `UIViewController` subclass | `UIViewControllerRepresentable`, `...TransitioningDelegate`, comments | fixed: end boundary |
| `@Dependency` / `DependencyKey` | comments; `...DependencyKey` suffix words | fixed: word boundary, `TestDependencyKey` allowed. `@DependencyClient` alone does not count |
| `static let shared` | comments | fixed by code-only matching. `static var shared` is not counted |
| Factories | `makeUIView`, `makeCoordinator`, `makeBody`, `makeIterator` (SwiftUI and stdlib requirements); `Factory` inside other words | fixed: `make<Name><Suffix>(` only for DI-style suffixes; `Factory` ends a camel word |
| `import Testing` | `import TestingSupport`, comments | fixed: word boundary |
| `XCTestCase` | `XCTestCaseEntry`, comments | fixed: word boundary. UI-test targets are XCTest by necessity and still count |
| `@Model` / `NSManagedObject` | `@ModelActor` already excluded by `\b`; comments | fixed by code-only matching. `NSManagedObject` counts any Core Data type use (contexts, IDs), by design |
| `NavigationStack` / `navigationDestination` | a property named `navigationDestination` in coordinator code; wrapper types such as `AppNavigationStack` | fixed: left word boundary, `.navigationDestination(` call only |
| Coordinators | `Coordinator` class nested in every `UIViewRepresentable`, `makeCoordinator`, `NSPersistentStoreCoordinator`, `UINavigationControllerDelegate` (image pickers) | fixed: declarations named `<Name>Coordinator`, `protocol Coordinator`, `UINavigationController` as a whole word. A class named exactly `Coordinator` and representable coordinators with a prefixed name (`MapCoordinator`) stay ambiguous |
| `@MainActor` | comments | fixed by code-only matching |
| `swiftLanguageModes` / `SWIFT_VERSION` | commented-out manifest lines. Only root-level `Package.swift` and `*.xcodeproj` are searched | comments fixed; root-only scope kept |

### Dependency injection

```bash
rg -l '@Dependency\b|(^|[^A-Za-z0-9_])(Test)?DependencyKey([^A-Za-z0-9_]|$)' --glob '*.swift'          # TCA dependencies
rg -l 'static let shared\b' --glob '*.swift'                   # singletons
rg -l 'Factory([^a-z]|$)|func make[A-Z][A-Za-z]*(ViewModel|Service|Client|Repository|Manager|Provider|UseCase|Interactor|Presenter)\(' --glob '*.swift'     # factories
```

### Tests

```bash
rg -l 'import Testing([^A-Za-z0-9_]|$)' --glob '*.swift'      # Swift Testing
rg -l 'XCTestCase([^A-Za-z0-9_]|$)' --glob '*.swift'          # XCTest
```

This sweep scans test directories on purpose, so skip the `*Tests` exclusion.

### Persistence

```bash
rg -l '@Model\b' --glob '*.swift'            # SwiftData
rg -l 'NSManagedObject' --glob '*.swift'     # Core Data
```

### Concurrency

```bash
rg -n 'swiftLanguageModes|SWIFT_VERSION' Package.swift ./*.xcodeproj/project.pbxproj
rg -l '@MainActor' --glob '*.swift'
```

Swift 6 language mode means strict concurrency errors; match it in new code. Below 6, follow the project's current strictness.

### Navigation

```bash
rg -l '(^|[^A-Za-z0-9_])NavigationStack(Store)?([^A-Za-z0-9_]|$)|\.navigationDestination\(' --glob '*.swift'
rg -l '(class|struct|actor)[[:space:]]+[A-Za-z0-9_]+Coordinator([^A-Za-z0-9_]|$)|protocol[[:space:]]+[A-Za-z0-9_]*Coordinator([^A-Za-z0-9_]|$)|UINavigationController([^A-Za-z0-9_]|$)' --glob '*.swift'
```

## Decision matrix (80/20)

For every area except `architecture` (which has the verdict above), compare the files of the competing patterns. The dominant pattern's share of all matching files decides:

| Share | Verdict | Meaning |
|-------|---------|---------|
| 80% or more | `match` | Use the dominant pattern for new code |
| 50-79% | `conflict` | Propose standardizing on the modern choice |
| Below 50% | `adopt` | No dominant pattern; use the modern choice |
| no matches | `none` | The pattern is absent; say so |

Ties go to the first pattern listed in the sweep. Sweeps outside a comparison (`@MainActor`, the language-mode settings) are reported as counts.

## Version sweep

```bash
jq -r '.pins[] | select(.identity=="swift-composable-architecture") | .state.version' Package.resolved
rg -o 'IPHONEOS_DEPLOYMENT_TARGET = [0-9.]+' --glob '*.pbxproj' | sort -u
rg -o 'SWIFT_VERSION = [0-9.]+|swiftLanguageModes: \[[^]]*\]' --glob '*.pbxproj' --glob 'Package.swift' | sort -u
```

Package.resolved may live under `*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/`. Check availability against the deployment target before recommending an API: `@Observable` and SwiftData need iOS 17; the `*-whats-new-27` skills need iOS 27. Flag legacy TCA APIs only when the resolved TCA version deprecates them.

## Pattern Detection Cache

### Cache Location

`.artifacts/iet/cache/detected-patterns.json`, under the project directory. `detect-patterns.py --write-cache` writes it.

### Cache Schema

```json
{
  "timestamp": "2026-11-21T17:00:00Z",
  "project_hash": "<sha256 over path + content-hash lines, see Computing project_hash>",
  "patterns": {
    "architecture": { "detected": "TCA", "confidence": 0.9, "evidence": ["Sources/Features/CounterFeature.swift:tca"] },
    "di_style": { "detected": "tca_dependency", "confidence": 0.75, "evidence": ["Sources/Features/FeedFeature.swift:tca_dependency"] },
    "testing_framework": { "detected": "swift_testing", "confidence": 1.0, "evidence": ["Tests/CounterTests.swift:swift_testing"] },
    "version": { "detected": "tca=1.17.0;deployment=17.0;swift=6.0;modes=[.v6]", "confidence": 1.0, "evidence": ["Package.resolved:tca_version", "App.xcodeproj/project.pbxproj:deployment_target"] }
  }
}
```

Keys: `architecture`, `di_style`, `testing_framework`, `persistence_framework`, `navigation_style`, `version`. For `architecture`, `detected` is the verdict (`NEW`, `TCA`, `MVVM` or `MIXED`) and `confidence` is the share of the side that decided it (`NEW` is 1.0; `MIXED` is the larger side's share, 0.0 with no signal). For the other keys, `detected` is the dominant pattern id (or `none`) and `confidence` its share. `evidence` lists up to three `path:pattern` entries. `version` holds the version facts as `tca=<v>;deployment=<v>;swift=<v>;modes=<v>` (`none` for a missing fact, several values joined by `,`) with confidence 1.0; its evidence entries are `path:kind` for the files the facts came from (`tca_version`, `deployment_target`, `swift_version`, `swift_language_modes`, the keys of the script's `version` block). It is cacheable because `Package.resolved`, every `Package.swift` and every `project.pbxproj` are part of `project_hash`. The `concurrency` counts are not cached; read them from `preflight.py` or the script.

### Freshness Rules

- The cache is valid while `project_hash` equals the current hash (see below; every scanned file and project file counts). A run for a subset of categories keeps the other entries while the hash is unchanged and drops them when it changes.
- An explicit user choice overrides a cached value; record it with `confidence: 1.0`.
- To force re-detection, delete the cache file or ask for `--fresh`.

### Computing `project_hash`

sha256 over UTF-8 lines `<relpath>\t<sha256 of the file bytes>\n`, sorted by `relpath` (POSIX `/`, plain string order), one per file in this set:

- every `.swift` file the scan reads (all of them after pruning `Pods`, `Carthage`, `.build`, `SourcePackages`, `DerivedData`, `.git`, `.artifacts`, `node_modules`; symlinks skipped);
- every project file at any depth that is not pruned: `Package.swift`, `Package.resolved`, `*.xcodeproj/project.pbxproj`, `*.xcconfig`.

`NO_PROJECT_FILES` when the set is empty. The key follows the content, so editing a source file, the resolved packages or a project nested in a subfolder invalidates the cache; touching a pruned directory does not. `detect-patterns.py --hash <project-dir>` prints only `project_hash=<hex>`; `preflight.py` imports that same function and prints the value under `== Project hash ==`.

The cache path is a stable contract: other tools read `.artifacts/iet/cache/detected-patterns.json`. Don't rename it or change existing keys.

## Report format

One line per area: dominant pattern, share, verdict. State the architecture verdict first, then the rule it triggers.
