---
agent: gradle-build-engineer
feature: "{feature_slug}"
timestamp: "{run_timestamp}"
files_created: []
files_modified: []
dependencies_added: []
interfaces_exposed: []
---

# Module Setup Report: [FEATURE NAME]

```yaml
Written by: [AGENT NAME]
Timestamp: [ISO 8601 - e.g., 2026-02-13T10:30:00Z]
```

## Pipeline Context

<!-- Copy verbatim from architecture-blueprint.md Pipeline Context section -->

**Original Prompt:** [Copy from blueprint]

**Business Purpose:** [Copy from blueprint]

## Summary

[Brief overview of modules created and build configuration applied]

## Modules Created

**Created Modules:**
```
[List of module paths created]
feature/[feature-name]/api/
feature/[feature-name]/impl/
```

**Module Dependencies:**
```kotlin
// feature/[feature-name]/impl/build.gradle.kts
dependencies {
    implementation(project(":feature:[feature-name]:api"))
    implementation(project(":core:data"))
    implementation(project(":core:model"))
    implementation(project(":core:ui"))
    // [Additional dependencies]
}
```

## Dependencies Added

**Convention Plugins Applied:**
```kotlin
// feature/[feature-name]/api/build.gradle.kts
plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.serialization)
}

// feature/[feature-name]/impl/build.gradle.kts
plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.hilt)
    alias(libs.plugins.kotlin.compose)
}
```

**Custom Build Configuration:**
```kotlin
android {
    namespace = "com.example.app.feature.[feature-name].[api|impl]"
    // [Additional configuration]
}
```

## Build System Integration

**Version Catalog Entries:**
```toml
# [Libraries added to libs.versions.toml]
[libraries]
[library-name] = { module = "group:artifact", version.ref = "version-ref" }
```

**Dependency Graph Verification:**
```bash
# Command to verify module structure
./gradlew :[module]:dependencies --configuration debugRuntimeClasspath

# Expected output:
# [Paste expected dependency tree]
```

**Build Performance:**
```
Module build time: [X seconds]
Configuration time: [X ms]
No circular dependencies detected: ✅
```

## Testing Configuration

**Test Dependencies:**
```kotlin
dependencies {
    testImplementation(project(":core:testing"))
    testImplementation(libs.junit)
    testImplementation(libs.truth)
    testImplementation(libs.turbine)
    // [Additional test dependencies]
}
```

**Test Source Sets:**
```
src/
├── test/java/           # Unit tests
├── androidTest/java/    # Instrumented tests
└── testFixtures/java/   # Test doubles (if feature API module)
```

## Integration Instructions

**For android-developer:**
```bash
# Sync project after module creation
./gradlew --refresh-dependencies

# Verify modules are recognized
./gradlew projects | grep [feature-name]

# Build modules to verify setup
./gradlew :[feature]:api:build :[feature]:impl:build
```

**App Module Integration:**
```kotlin
// app/build.gradle.kts - add these dependencies
dependencies {
    implementation(project(":feature:[feature-name]:impl"))
}
```

**Navigation Integration:**
```kotlin
// app/src/main/kotlin/navigation/NavHost.kt
import com.example.app.feature.[feature-name].api.[Feature]Route

// Add to NavHost
[feature-name]Graph(
    onNavigateBack = { /* ... */ },
)
```

## Verification Checklist

**Module Setup:**
- [ ] All modules created in correct locations
- [ ] build.gradle.kts files configured
- [ ] Convention plugins applied correctly
- [ ] Dependencies properly declared

**Build System:**
- [ ] Gradle sync succeeds
- [ ] No circular dependencies
- [ ] Module builds successfully
- [ ] Version catalog updated if needed

**Integration:**
- [ ] App module references feature module
- [ ] Navigation routes exposed via API module
- [ ] No compilation errors

## Next Steps

**For android-developer:**
1. [Implement classes in the modules]
2. [Create repository implementations]
3. [Write implementation-report.md handoff]

**For android-architect:**
1. [Review module structure alignment with blueprint]
2. [Validate dependency rules]
