# Gradle Patterns Reference

Code examples and implementation patterns extracted from gradle-build-engineer agent prompt.

## When to use

Read this reference when setting up convention plugins, managing version catalogs, configuring module build scripts, or optimizing build performance. Used by gradle-build-engineer during module setup and build configuration work.

## Convention Plugin Implementations

### Android Application Convention

```kotlin
class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.application")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<ApplicationExtension> {
                configureKotlinAndroid(this)

                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                    versionCode = 1
                    versionName = "1.0.0"
                }

                buildTypes {
                    release {
                        isMinifyEnabled = true
                        proguardFiles(
                            getDefaultProguardFile("proguard-android-optimize.txt"),
                            "proguard-rules.pro"
                        )
                    }
                }
            }
        }
    }
}
```

### Kotlin Android Configuration Extension

```kotlin
internal fun Project.configureKotlinAndroid(
    commonExtension: CommonExtension<*, *, *, *, *, *>,
) {
    commonExtension.apply {
        compileSdk = libs.findVersion("compileSdk").get().toString().toInt()

        defaultConfig {
            minSdk = libs.findVersion("minSdk").get().toString().toInt()
        }

        compileOptions {
            sourceCompatibility = JavaVersion.VERSION_11
            targetCompatibility = JavaVersion.VERSION_11
            isCoreLibraryDesugaringEnabled = true
        }
    }

    configureKotlin()

    dependencies {
        add("coreLibraryDesugaring", libs.findLibrary("android.desugarJdkLibs").get())
    }
}

internal fun Project.configureKotlin() {
    tasks.withType<KotlinCompile>().configureEach {
        kotlinOptions {
            jvmTarget = libs.findVersion("jvmTarget").get().toString()

            freeCompilerArgs = freeCompilerArgs + listOf(
                "-opt-in=kotlin.RequiresOptIn",
                "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
                "-opt-in=kotlinx.coroutines.FlowPreview",
            )
        }
    }
}
```

### Android Library Convention

```kotlin
class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<LibraryExtension> {
                configureKotlinAndroid(this)

                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                }

                buildTypes {
                    release {
                        isMinifyEnabled = false
                        proguardFiles(
                            getDefaultProguardFile("proguard-android-optimize.txt"),
                            "proguard-rules.pro"
                        )
                    }
                }
            }
        }
    }
}
```

### Android Compose Convention

```kotlin
class AndroidComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("org.jetbrains.kotlin.plugin.compose")
            }

            val extension = extensions.getByType<CommonExtension<*, *, *, *, *, *>>()

            extension.apply {
                buildFeatures {
                    compose = true
                }

                dependencies {
                    val bom = libs.findLibrary("androidx-compose-bom").get()
                    add("implementation", platform(bom))
                    add("androidTestImplementation", platform(bom))

                    add("implementation", libs.findLibrary("androidx-compose-ui").get())
                    add("implementation", libs.findLibrary("androidx-compose-material3").get())
                    add("implementation", libs.findLibrary("androidx-compose-ui-tooling-preview").get())
                    add("debugImplementation", libs.findLibrary("androidx-compose-ui-tooling").get())
                }
            }
        }
    }
}
```

### Hilt Convention

```kotlin
class HiltConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.google.devtools.ksp")
                apply("com.google.dagger.hilt.android")
            }

            dependencies {
                add("implementation", libs.findLibrary("hilt-android").get())
                add("ksp", libs.findLibrary("hilt-compiler").get())
            }
        }
    }
}
```

### Feature API Convention

```kotlin
class AndroidFeatureApiConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
                apply("org.jetbrains.kotlin.plugin.serialization")
            }

            extensions.configure<LibraryExtension> {
                configureKotlinAndroid(this)
            }

            dependencies {
                add("implementation", libs.findLibrary("kotlinx-serialization-json").get())
            }
        }
    }
}
```

### Feature Impl Convention

```kotlin
class AndroidFeatureImplConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            with(pluginManager) {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<LibraryExtension> {
                configureKotlinAndroid(this)

                defaultConfig {
                    testInstrumentationRunner = "com.example.app.core.testing.AppTestRunner"
                }
            }

            dependencies {
                add("implementation", project(":core:ui"))
                add("implementation", project(":core:designsystem"))
                add("testImplementation", project(":core:testing"))
                add("androidTestImplementation", project(":core:testing"))
            }
        }
    }
}
```

### build-logic build.gradle.kts

```kotlin
plugins {
    `kotlin-dsl`
}

group = "com.example.buildlogic"

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.compose.gradlePlugin)
}

gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "com.example.android.application"
            implementationClass = "AndroidApplicationConventionPlugin"
        }
        register("androidLibrary") {
            id = "com.example.android.library"
            implementationClass = "AndroidLibraryConventionPlugin"
        }
        register("androidFeatureApi") {
            id = "com.example.android.feature.api"
            implementationClass = "AndroidFeatureApiConventionPlugin"
        }
        register("androidFeatureImpl") {
            id = "com.example.android.feature.impl"
            implementationClass = "AndroidFeatureImplConventionPlugin"
        }
        register("androidCompose") {
            id = "com.example.android.compose"
            implementationClass = "AndroidComposeConventionPlugin"
        }
        register("hilt") {
            id = "com.example.hilt"
            implementationClass = "HiltConventionPlugin"
        }
    }
}
```

## Version Catalog Example

```toml
[versions]
compileSdk = "36"
minSdk = "24"
targetSdk = "36"
kotlin = "2.3.10"
jvmTarget = "11"
androidx-core = "1.15.0"
androidx-lifecycle = "2.10.0"
compose-bom = "2025.09.01"
hilt = "2.59"
room = "2.8.3"
retrofit = "2.11.0"

[libraries]
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version.ref = "androidx-core" }
androidx-lifecycle-runtime = { group = "androidx.lifecycle", name = "lifecycle-runtime-ktx", version.ref = "androidx-lifecycle" }
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
androidx-compose-ui = { group = "androidx.compose.ui", name = "ui" }
androidx-compose-material3 = { group = "androidx.compose.material3", name = "material3" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-compiler = { group = "com.google.dagger", name = "hilt-compiler", version.ref = "hilt" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
android-library = { id = "com.android.library", version.ref = "agp" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }

[bundles]
compose = ["androidx-compose-ui", "androidx-compose-material3", "androidx-compose-ui-tooling"]
lifecycle = ["androidx-lifecycle-runtime", "androidx-lifecycle-viewmodel"]
```

## Root settings.gradle.kts

```kotlin
pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")

rootProject.name = "MyApp"
include(":app")
include(":core:data")
include(":core:database")
include(":core:network")
include(":core:model")
include(":feature:items:api")
include(":feature:items:impl")
```

## Module build.gradle.kts Example

```kotlin
// feature/items/impl/build.gradle.kts
plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
    id("com.example.android.feature.impl")
    id("com.example.android.compose")
    id("com.example.hilt")
}

android {
    namespace = "com.example.feature.items.impl"
}

dependencies {
    implementation(projects.feature.items.api)
    implementation(projects.core.data)
    implementation(projects.core.model)
    implementation(libs.bundles.lifecycle)
    implementation(libs.androidx.navigation.compose)
    testImplementation(libs.junit)
    testImplementation(libs.truth)
    testImplementation(libs.turbine)
}
```

## Build Performance Configuration

### gradle.properties

```properties
# Kotlin
kotlin.code.style=official
kotlin.incremental=true
kotlin.incremental.useClasspathSnapshot=true

# Android
android.useAndroidX=true
android.nonTransitiveRClass=true
android.defaults.buildfeatures.buildconfig=false
android.defaults.buildfeatures.aidl=false
android.defaults.buildfeatures.renderscript=false
android.defaults.buildfeatures.resvalues=false
android.defaults.buildfeatures.shaders=false

# Gradle
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=1024m -XX:+HeapDumpOnOutOfMemoryError
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true
org.gradle.configuration-cache=true

# KSP
ksp.incremental=true
ksp.incremental.intermodule=true
```

## Gradle Build Cache Remote Sharing

Remote build cache allows team members and CI to share compiled outputs, significantly reducing build times for unchanged modules.

### settings.gradle.kts Configuration

```kotlin
// settings.gradle.kts
buildCache {
    local {
        isEnabled = true
        directory = File(rootDir, ".gradle/build-cache")
        removeUnusedEntriesAfterDays = 7
    }

    remote<HttpBuildCache> {
        url = uri(
            System.getenv("GRADLE_CACHE_URL") ?: "https://cache.example.com/cache/"
        )
        isEnabled = true
        // CI pushes to cache, developers only read
        isPush = System.getenv("CI") != null

        credentials {
            username = System.getenv("GRADLE_CACHE_USERNAME") ?: ""
            password = System.getenv("GRADLE_CACHE_PASSWORD") ?: ""
        }
    }
}
```

### gradle.properties for Cache

```properties
# Enable build cache
org.gradle.caching=true

# Enable configuration cache (Gradle 8.1+)
org.gradle.configuration-cache=true
```

### CI Configuration (GitHub Actions)

```yaml
- name: Build with remote cache
  env:
    GRADLE_CACHE_URL: ${{ secrets.GRADLE_CACHE_URL }}
    GRADLE_CACHE_USERNAME: ${{ secrets.GRADLE_CACHE_USERNAME }}
    GRADLE_CACHE_PASSWORD: ${{ secrets.GRADLE_CACHE_PASSWORD }}
    CI: true
  run: ./gradlew assembleDebug --build-cache
```

### Develocity (Gradle Enterprise) Alternative

```kotlin
// settings.gradle.kts — for teams using Develocity
plugins {
    id("com.gradle.develocity") version "3.19"
}

develocity {
    server = "https://ge.example.com"
    buildCache {
        remote(develocity.buildCache) {
            isEnabled = true
            isPush = System.getenv("CI") != null
        }
    }
}
```

## Advanced Patterns

### Product Flavors

```kotlin
android {
    flavorDimensions += "environment"
    productFlavors {
        create("demo") {
            dimension = "environment"
            applicationIdSuffix = ".demo"
            versionNameSuffix = "-demo"
        }
        create("prod") {
            dimension = "environment"
        }
    }
}
```

### Build Variants with Signing

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file(keystoreProperties["storeFile"] as String)
            storePassword = keystoreProperties["storePassword"] as String
            keyAlias = keystoreProperties["keyAlias"] as String
            keyPassword = keystoreProperties["keyPassword"] as String
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### Version Management Plugin

```kotlin
class VersionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val versionFile = file("version.properties")
            val versionProps = Properties().apply {
                if (versionFile.exists()) {
                    load(versionFile.inputStream())
                }
            }

            val versionMajor = versionProps.getProperty("VERSION_MAJOR", "1").toInt()
            val versionMinor = versionProps.getProperty("VERSION_MINOR", "0").toInt()
            val versionPatch = versionProps.getProperty("VERSION_PATCH", "0").toInt()
            val versionBuild = versionProps.getProperty("VERSION_BUILD", "0").toInt()

            extensions.create<VersionExtension>("versionConfig").apply {
                major.set(versionMajor)
                minor.set(versionMinor)
                patch.set(versionPatch)
                build.set(versionBuild)
                name.set("$versionMajor.$versionMinor.$versionPatch")
                code.set(versionMajor * 10000 + versionMinor * 1000 + versionPatch * 100 + versionBuild)
            }

            tasks.register("bumpPatch") {
                doLast {
                    versionProps.setProperty("VERSION_PATCH", (versionPatch + 1).toString())
                    versionProps.setProperty("VERSION_BUILD", "0")
                    versionProps.store(versionFile.outputStream(), "Version bumped")
                }
            }
        }
    }
}
```

## CI/CD Integration

### GitHub Actions - Android CI

```yaml
name: Android CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: gradle

      - name: Grant execute permission for gradlew
        run: chmod +x gradlew

      - name: Run lint
        run: ./gradlew lintDebug

      - name: Run unit tests
        run: ./gradlew testDebugUnitTest

      - name: Generate test report
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Unit Test Results
          path: '**/build/test-results/test*/*.xml'
          reporter: java-junit

      - name: Build debug APK
        run: ./gradlew assembleDebug

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-debug
          path: app/build/outputs/apk/debug/*.apk
          retention-days: 7

  instrumented-tests:
    runs-on: macos-latest
    timeout-minutes: 45

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: gradle

      - name: Grant execute permission for gradlew
        run: chmod +x gradlew

      - name: Run instrumented tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 33
          arch: x86_64
          profile: pixel_6
          script: ./gradlew connectedDebugAndroidTest

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: instrumented-test-results
          path: '**/build/reports/androidTests/'
          retention-days: 7
```

### Release Workflow

```yaml
name: Android Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: gradle

      - name: Decode keystore
        env:
          KEYSTORE_BASE64: ${{ secrets.KEYSTORE_BASE64 }}
        run: echo $KEYSTORE_BASE64 | base64 --decode > app/keystore.jks

      - name: Build release APK
        env:
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
        run: ./gradlew assembleRelease

      - name: Build release AAB
        env:
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
        run: ./gradlew bundleRelease

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            app/build/outputs/apk/release/*.apk
            app/build/outputs/bundle/release/*.aab
          draft: true
          generate_release_notes: true
```

### Signing Configuration

```kotlin
android {
    signingConfigs {
        create("release") {
            val keystorePropertiesFile = rootProject.file("keystore.properties")
            if (keystorePropertiesFile.exists()) {
                val keystoreProperties = Properties()
                keystoreProperties.load(keystorePropertiesFile.inputStream())

                storeFile = file(keystoreProperties["storeFile"] as String)
                storePassword = keystoreProperties["storePassword"] as String
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
            } else {
                storeFile = file("keystore.jks")
                storePassword = System.getenv("KEYSTORE_PASSWORD")
                keyAlias = System.getenv("KEY_ALIAS")
                keyPassword = System.getenv("KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### Fastlane Integration

```ruby
default_platform(:android)

platform :android do
  desc "Run unit tests"
  lane :test do
    gradle(task: "testDebugUnitTest")
  end

  desc "Build debug APK"
  lane :debug do
    gradle(task: "assembleDebug")
  end

  desc "Build and upload release to Firebase App Distribution"
  lane :beta do
    gradle(
      task: "assembleRelease",
      properties: {
        "android.injected.signing.store.file" => ENV["KEYSTORE_FILE"],
        "android.injected.signing.store.password" => ENV["KEYSTORE_PASSWORD"],
        "android.injected.signing.key.alias" => ENV["KEY_ALIAS"],
        "android.injected.signing.key.password" => ENV["KEY_PASSWORD"]
      }
    )

    firebase_app_distribution(
      app: ENV["FIREBASE_APP_ID"],
      groups: "internal-testers",
      release_notes: "Latest beta build"
    )
  end

  desc "Deploy to Play Store internal track"
  lane :internal do
    gradle(
      task: "bundleRelease",
      properties: {
        "android.injected.signing.store.file" => ENV["KEYSTORE_FILE"],
        "android.injected.signing.store.password" => ENV["KEYSTORE_PASSWORD"],
        "android.injected.signing.key.alias" => ENV["KEY_ALIAS"],
        "android.injected.signing.key.password" => ENV["KEY_PASSWORD"]
      }
    )

    upload_to_play_store(
      track: 'internal',
      aab: 'app/build/outputs/bundle/release/app-release.aab',
      skip_upload_screenshots: true,
      skip_upload_images: true
    )
  end

  desc "Promote internal to production"
  lane :production do
    upload_to_play_store(
      track: 'internal',
      track_promote_to: 'production',
      skip_upload_changelogs: false
    )
  end
end
```

### Dependency Updates Workflow

```yaml
name: Dependency Updates

on:
  schedule:
    - cron: '0 0 * * 1'
  workflow_dispatch:

jobs:
  update-dependencies:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Check for dependency updates
        run: ./gradlew dependencyUpdates

      - name: Upload dependency report
        uses: actions/upload-artifact@v4
        with:
          name: dependency-updates-report
          path: build/dependencyUpdates/
          retention-days: 30
```

### Code Quality Checks

```yaml
name: Code Quality

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: gradle

      - name: Run ktlint
        run: ./gradlew ktlintCheck

      - name: Run Detekt
        run: ./gradlew detekt

      - name: Upload lint reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: lint-reports
          path: |
            **/build/reports/ktlint/
            **/build/reports/detekt/
          retention-days: 7
```

## Decision Council Protocol - Build Example

```markdown
## Build Decision: Convention Plugin Strategy for Feature Modules

### Status Quo Advocate's Position:
"Current setup has explicit build.gradle.kts per module (15 modules).
Each module's configuration is visible and customizable.
- 15 feature modules, avg 120 lines per build.gradle.kts
- 70% configuration is duplicated
- Build works reliably, no configuration-related bugs
- Team understands inline configuration"

### Best Practices Advocate's Position:
"Convention plugins are Google's recommended pattern for multi-module projects.
- Eliminate ~1,500 lines of duplicated configuration
- Type-safe configuration with Kotlin DSL
- Single-line plugin application per module
- Configuration changes apply to all modules instantly
- Scales to 50+ modules"

### Pragmatic Synthesis:
Recommendation: Incremental convention plugin adoption
- Phase 1 (Week 1-2): Create 3 core convention plugins, pilot on 3 modules
- Phase 2 (Week 3-4): Migrate remaining 12 feature modules
- Phase 3 (ongoing): New modules use convention plugins from day 1

Success criteria:
- Build times unchanged or improved
- No increase in build failures
- Reduced lines of build configuration by 60%+
```

## CI/CD Checklist

```
CONTINUOUS INTEGRATION
- Build on every PR
- Unit tests run automatically
- Lint checks enforced
- Code coverage reported
- Build artifacts uploaded
- Test results published

CONTINUOUS DELIVERY
- Release builds signed automatically
- APK and AAB generated
- Firebase App Distribution setup
- Play Store deployment configured
- Release notes automated
- Version bumping automated

SECURITY
- Signing keys in secrets
- No credentials in repository
- Keystore base64 encoded
- Environment variables used
- Secrets rotation policy
- Dependency vulnerability scanning

QUALITY GATES
- Build must pass
- Tests must pass (80%+ coverage)
- Lint must pass
- No critical Detekt issues
- ProGuard mapping uploaded
- APK size monitored
```
