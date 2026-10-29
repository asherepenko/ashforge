# Kotlin–Java Interop

## When to use

Read when Kotlin code is called from Java (mixed modules, legacy code, Java SDK callbacks) or when migrating Java classes to Kotlin.

## @JvmStatic for Companion Objects

```kotlin
class ConfigManager private constructor() {
    companion object {
        private val instance = ConfigManager()

        @JvmStatic
        fun getInstance(): ConfigManager {
            return instance
        }

        const val DEFAULT_TIMEOUT = 30_000L
    }
}
```

```java
// Java consumption
public class JavaClient {
    public void initialize() {
        ConfigManager manager = ConfigManager.getInstance();
        int timeout = ConfigManager.DEFAULT_TIMEOUT;
    }
}
```

## @JvmOverloads for Default Parameters

```kotlin
class NotificationBuilder @JvmOverloads constructor(
    private val title: String,
    private val message: String,
    private val priority: Int = PRIORITY_DEFAULT,
    private val autoCancel: Boolean = true,
) {
    companion object {
        const val PRIORITY_DEFAULT = 0
        const val PRIORITY_HIGH = 1
    }

    @JvmOverloads
    fun setSound(soundUri: Uri, audioAttributes: AudioAttributes? = null): NotificationBuilder {
        return this
    }
}
```

## @JvmField for Direct Field Access

```kotlin
data class Coordinates(
    @JvmField val latitude: Double,
    @JvmField val longitude: Double,
    val altitude: Double,
) {
    companion object {
        @JvmField
        val EARTH_RADIUS = 6371.0
    }
}
```

## @JvmName for Custom JVM Names

```kotlin
class DataProcessor {
    fun String.process(): String = this.trim()

    @JvmName("processString")
    fun process(input: String): String = input.process()

    val items: List<Item> = emptyList()

    @JvmName("getItemsList")
    fun getItems(): List<Item> = items
}

@file:JvmName("StringUtils")
package com.example.utils

fun String.toTitleCase(): String {
    return split(" ").joinToString(" ") { it.capitalize() }
}
```

## Properties vs. Getters/Setters

```kotlin
class UserProfile(
    var username: String,          // Generates getUsername()/setUsername()
    val email: String,              // Generates getEmail() only
    private val id: String,         // Not visible to Java
) {
    var isVerified: Boolean = false // Generates isVerified()/setVerified()
        private set

    @get:JvmName("isActive")
    val active: Boolean = true
}
```

## Data Classes in Java

```kotlin
data class ApiResponse(
    val success: Boolean,
    val data: String?,
    val errorCode: Int = 0,
) {
    companion object {
        @JvmStatic
        fun success(data: String): ApiResponse {
            return ApiResponse(success = true, data = data)
        }

        @JvmStatic
        fun error(errorCode: Int): ApiResponse {
            return ApiResponse(success = false, data = null, errorCode = errorCode)
        }
    }
}
```

## Extension Functions and Top-Level Functions

```kotlin
fun String.isValidEmail(): Boolean {
    return contains("@") && contains(".")
}

object StringUtils {
    @JvmStatic
    fun isValidEmail(input: String): Boolean {
        return input.isValidEmail()
    }
}

@file:JvmName("DateUtils")
package com.example.utils

fun Long.toFormattedDate(): String {
    return SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date(this))
}

@JvmName("formatDate")
fun formatDate(timestamp: Long): String = timestamp.toFormattedDate()
```

## Migration Strategy

```
MIGRATION CANDIDATES (High Priority)
- Data models and DTOs - Simple, high impact
- Utility classes - Pure functions, easy to convert
- Repository interfaces - Define contracts first
- New features - Write in Kotlin from the start

KEEP IN JAVA (Low Priority)
- Generated code (builders, AutoValue)
- Stable, rarely changed classes
- Heavy annotation processing (Dagger modules)
- Third-party code integration
```

**Step-by-Step Conversion Process:**

```kotlin
// STEP 1: Convert Java class using IDE (Code > Convert Java File to Kotlin)

// Original Java
public class User {
    private String name;
    private int age;
    public User(String name, int age) { this.name = name; this.age = age; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
}

// STEP 2: IDE auto-converts to:
class User(private var name: String, private var age: Int) {
    fun getName(): String = name
    fun setName(name: String) { this.name = name }
    fun getAge(): Int = age
    fun setAge(age: Int) { this.age = age }
}

// STEP 3: Manual cleanup - Convert to idiomatic Kotlin
data class User(
    var name: String,
    var age: Int,
)

// STEP 4: Add null safety if needed
data class User(
    val name: String,
    val age: Int,
    val email: String? = null,
)

// STEP 5: Add @JvmOverloads if used from Java
data class User @JvmOverloads constructor(
    val name: String,
    val age: Int,
    val email: String? = null,
)
```

**Migration Testing:**

```kotlin
class UserRepositoryMigrationTest {
    private lateinit var javaRepository: JavaUserRepository
    private lateinit var kotlinRepository: KotlinUserRepository

    @Before
    fun setup() {
        javaRepository = JavaUserRepository(database)
        kotlinRepository = KotlinUserRepository(database)
    }

    @Test
    fun `both repositories return same results`() = runTest {
        val userId = "123"
        val javaResult = javaRepository.getUser(userId)
        val kotlinResult = kotlinRepository.getUser(userId)
        assertThat(kotlinResult).isEqualTo(javaResult)
    }
}
```

**Migration Checklist:**

```
BEFORE CONVERSION
- Ensure all tests pass
- Create feature branch
- Run static analysis (lint, detekt)
- Document Java-specific behavior

DURING CONVERSION
- Convert with IDE (Code > Convert Java File to Kotlin)
- Resolve compilation errors
- Clean up auto-generated code
- Add @JvmStatic/@JvmOverloads where needed
- Replace !! with safe calls
- Run ktlint formatting

AFTER CONVERSION
- Run all tests (unit + integration)
- Test from Java call sites
- Verify APK size change
- Check ProGuard rules
- Update documentation
- Review with team before merging
```

