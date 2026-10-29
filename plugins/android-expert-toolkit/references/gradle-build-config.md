# Gradle Build Configuration

## When to use

Read when editing the version catalog, `settings.gradle.kts`, `gradle.properties`, build caching, flavors, signing, or CI build steps. Convention plugins → `gradle-convention-plugins.md`. AGP upgrades → `agp-9-upgrade` skill. Release shrinking → `r8-analyzer` skill.

## Version catalog

Every `version.ref` must name a key in `[versions]`. Versions below are **placeholders** — read the project's catalog, or look up the current stable release; never copy them.

```toml
[versions]
agp = "<agp-version>"
kotlin = "<kotlin-version>"
ksp = "<ksp-version>"          # AGP 9 needs KSP >= 2.3.6
compileSdk = "<api-level>"
minSdk = "<api-level>"
targetSdk = "<api-level>"
composeBom = "<bom-version>"
hilt = "<hilt-version>"        # AGP 9 needs Hilt >= 2.59.2

[libraries]
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-compose-ui-tooling = { group = "androidx.compose.ui", name = "ui-tooling" }
androidx-compose-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-compiler = { group = "com.google.dagger", name = "hilt-compiler", version.ref = "hilt" }
# build-logic classpath
android-gradlePlugin = { group = "com.android.tools.build", name = "gradle", version.ref = "agp" }
kotlin-gradlePlugin = { group = "org.jetbrains.kotlin", name = "kotlin-gradle-plugin", version.ref = "kotlin" }
ksp-gradlePlugin = { group = "com.google.devtools.ksp", name = "com.google.devtools.ksp.gradle.plugin", version.ref = "ksp" }
compose-gradlePlugin = { group = "org.jetbrains.kotlin", name = "compose-compiler-gradle-plugin", version.ref = "kotlin" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
android-library = { id = "com.android.library", version.ref = "agp" }
kotlin-compose = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }
kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
# No kotlin-android entry on AGP 9: built-in Kotlin replaces it.
```

Libraries managed by a BOM omit `version.ref`. Check with `./gradlew help` after editing — an undefined `version.ref` fails at configuration time.

## settings.gradle.kts

```kotlin
pluginManagement {
    includeBuild("build-logic")
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories { google(); mavenCentral() }
}

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")
rootProject.name = "MyApp"
include(":app", ":core:data", ":core:model", ":feature:items:api", ":feature:items:impl")
```

## gradle.properties

```properties
org.gradle.jvmargs=-Xmx4g -XX:+HeapDumpOnOutOfMemoryError
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configuration-cache=true
android.nonTransitiveRClass=true
```

After an AGP 9 migration, remove `android.builtInKotlin`, `android.newDsl`, `android.uniquePackageNames` and `android.enableAppCompileTimeRClass` (per the `agp-9-upgrade` skill). Don't add flags whose defaults already match; check each against the AGP release notes for the project's version.

## Remote build cache

```kotlin
// settings.gradle.kts
buildCache {
    remote<HttpBuildCache> {
        url = uri(providers.environmentVariable("GRADLE_CACHE_URL").get())
        isPush = providers.environmentVariable("CI").isPresent   // CI writes, developers read
        credentials {
            username = providers.environmentVariable("GRADLE_CACHE_USERNAME").orNull
            password = providers.environmentVariable("GRADLE_CACHE_PASSWORD").orNull
        }
    }
}
```

Teams on Develocity use its `buildCache { remote(develocity.buildCache) }` instead.

## Flavors and signing

```kotlin
android {
    flavorDimensions += "environment"
    productFlavors {
        create("demo") { dimension = "environment"; applicationIdSuffix = ".demo" }
        create("prod") { dimension = "environment" }
    }
    signingConfigs {
        create("release") {
            // Read from env or an untracked keystore.properties — never commit keys.
            storeFile = file(providers.environmentVariable("KEYSTORE_PATH").get())
            storePassword = providers.environmentVariable("KEYSTORE_PASSWORD").get()
            keyAlias = providers.environmentVariable("KEY_ALIAS").get()
            keyPassword = providers.environmentVariable("KEY_PASSWORD").get()
        }
    }
    buildTypes { release { signingConfig = signingConfigs.getByName("release") } }
}
```

`variantFilter` is removed in AGP 9 — use `androidComponents.beforeVariants { }`.

## CI checklist

- Build, unit tests, and lint on every PR; upload test reports.
- Release builds signed from CI secrets; no keystore or passwords in the repo.
- Upload the R8 mapping file with each release build.
- Track APK/AAB size per release (`android` CLI can analyze artifacts).
- Gradle runs with `--no-daemon` on ephemeral CI agents, or with a short daemon idle timeout.
