# Gradle Convention Plugins (AGP 9)

## When to use

Read when creating or editing `build-logic` convention plugins or a module's `build.gradle.kts`. Upgrading an existing project from AGP 8 → 9 is a migration: load the `agp-9-upgrade` skill instead. Match the project's AGP version first — the code below targets AGP 9 with built-in Kotlin.

## AGP 9 rules that change convention plugins

Source: `agp-9-upgrade` skill (`references/android/build/migrate-to-built-in-kotlin.md`, `references/android/build/releases/agp-9-0-0-release-notes.md`).

- **Built-in Kotlin.** AGP 9 compiles Kotlin itself. Do not apply `org.jetbrains.kotlin.android` (`kotlin-android`); applying it fails the build. KMP modules are the exception (use `org.jetbrains.kotlin.multiplatform` + `com.android.kotlin.multiplatform.library`).
- **`kotlinOptions {}` is gone.** Use `kotlin { compilerOptions { … } }`. `jvmTarget` defaults to `android.compileOptions.targetCompatibility`, so don't set it.
- **`CommonExtension` is not parameterized.** Write `CommonExtension`, not `CommonExtension<*, *, *, *, *, *>`. Block methods moved to the concrete extensions, so on `CommonExtension` use property access (`defaultConfig.apply { }`, `compileOptions.apply { }`, `buildFeatures.apply { }`).
- **kapt** is incompatible with built-in Kotlin. Use KSP (≥ 2.3.6 per the skill) or `legacy-kapt` — see the skill's `references/ksp-kapt.md`. Hilt ≥ 2.59.2.
- The Compose compiler plugin (`org.jetbrains.kotlin.plugin.compose`) and serialization plugin are still applied; only `kotlin-android` goes away.

On AGP 8.x, keep the project's existing pattern (`kotlin-android` + parameterized `CommonExtension`) and recommend the upgrade separately.

## Shared configuration

```kotlin
// build-logic/convention/src/main/kotlin/KotlinAndroid.kt
internal fun Project.configureKotlinAndroid(commonExtension: CommonExtension) {
    commonExtension.apply {
        compileSdk = libs.findVersion("compileSdk").get().requiredVersion.toInt()
        defaultConfig.apply {
            minSdk = libs.findVersion("minSdk").get().requiredVersion.toInt()
        }
        compileOptions.apply {
            sourceCompatibility = JavaVersion.VERSION_17
            targetCompatibility = JavaVersion.VERSION_17
            isCoreLibraryDesugaringEnabled = true
        }
    }
    extensions.configure<KotlinAndroidProjectExtension> {
        compilerOptions {
            freeCompilerArgs.addAll("-opt-in=kotlin.RequiresOptIn")
        }
    }
    dependencies {
        add("coreLibraryDesugaring", libs.findLibrary("android-desugarJdkLibs").get())
    }
}
```

Verify the Kotlin extension type against the project's Kotlin Gradle plugin version before copying (`android docs search "built-in Kotlin compilerOptions"`); use `KotlinAndroidProjectExtension` only if it resolves on the build-logic classpath.

## Application and library plugins

```kotlin
class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        pluginManager.apply("com.android.application")
        extensions.configure<ApplicationExtension> {
            configureKotlinAndroid(this)
            defaultConfig { targetSdk = libs.findVersion("targetSdk").get().requiredVersion.toInt() }
            buildTypes {
                release {
                    isMinifyEnabled = true
                    isShrinkResources = true
                    proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
                }
            }
        }
    }
}

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        pluginManager.apply("com.android.library")
        extensions.configure<LibraryExtension> {
            configureKotlinAndroid(this)
            defaultConfig.testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }
    }
}
```

Libraries don't minify themselves; ship consumer keep rules (`consumerProguardFiles`) only for what reflection actually needs. Keep-rule review → `r8-analyzer` skill.

## Compose plugin

```kotlin
class AndroidComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        pluginManager.apply("org.jetbrains.kotlin.plugin.compose")
        extensions.getByType<CommonExtension>().buildFeatures.apply { compose = true }
        dependencies {
            val bom = libs.findLibrary("androidx-compose-bom").get()
            add("implementation", platform(bom))
            add("androidTestImplementation", platform(bom))
            add("implementation", libs.findLibrary("androidx-compose-ui-tooling-preview").get())
            add("debugImplementation", libs.findLibrary("androidx-compose-ui-tooling").get())
        }
    }
}
```

## DI plugin (Hilt example)

Use whatever DI the project uses (run `android-conventions di`). For Hilt:

```kotlin
class HiltConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        pluginManager.apply("com.google.devtools.ksp")
        pluginManager.apply("com.google.dagger.hilt.android")
        dependencies {
            add("implementation", libs.findLibrary("hilt-android").get())
            add("ksp", libs.findLibrary("hilt-compiler").get())
        }
    }
}
```

## Feature plugins

- `feature.api`: `com.android.library` + `org.jetbrains.kotlin.plugin.serialization` (route keys). No UI deps.
- `feature.impl`: library + compose + DI plugins, plus `:core:ui`, `:core:designsystem`, `testImplementation(project(":core:testing"))`.

A feature impl module depends on other features' `api` modules only — never another `impl`.

## build-logic/convention/build.gradle.kts

```kotlin
plugins { `kotlin-dsl` }

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)   // Compose/serialization plugin classes, KotlinAndroidProjectExtension
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
}

gradlePlugin {
    plugins {
        register("androidApplication") { id = "app.android.application"; implementationClass = "AndroidApplicationConventionPlugin" }
        register("androidLibrary") { id = "app.android.library"; implementationClass = "AndroidLibraryConventionPlugin" }
        register("androidCompose") { id = "app.android.compose"; implementationClass = "AndroidComposeConventionPlugin" }
        register("hilt") { id = "app.hilt"; implementationClass = "HiltConventionPlugin" }
    }
}
```

## Module build file

```kotlin
// feature/items/impl/build.gradle.kts
plugins {
    id("app.android.library")
    id("app.android.compose")
    id("app.hilt")
}

android { namespace = "com.example.feature.items.impl" }

dependencies {
    implementation(projects.feature.items.api)
    implementation(projects.core.data)
}
```

No `alias(libs.plugins.kotlin.android)` line — the convention plugin applies everything the module needs.
