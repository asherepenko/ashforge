# Developer Patterns Reference

Code examples and implementation patterns extracted from android-developer agent prompt.

## When to use

Read this reference when implementing ViewModels, wiring repositories into the UI layer, or structuring UI state handling in code. Used by android-developer after receiving `architecture-blueprint.md`. For architectural decisions (not implementation), see `architecture-patterns.md`.

## ViewModel Implementation

```kotlin
@HiltViewModel
class ItemsViewModel @Inject constructor(
    private val repository: ItemRepository,
) : ViewModel() {

    val uiState: StateFlow<ItemsUiState> =
        repository.items
            .map<List<Item>, ItemsUiState> { ItemsUiState.Success(it) }
            .catch { emit(ItemsUiState.Error(it.message ?: "Unknown error")) }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = ItemsUiState.Loading,
            )

    fun refresh() {
        viewModelScope.launch {
            repository.refresh()
        }
    }

    fun createItem(name: String, description: String) {
        viewModelScope.launch {
            repository.createItem(
                Item(
                    id = UUID.randomUUID().toString(),
                    name = name,
                    description = description,
                )
            )
        }
    }

    fun deleteItem(id: String) {
        viewModelScope.launch {
            repository.deleteItem(id)
        }
    }
}
```

## UI State Sealed Interface

```kotlin
sealed interface ItemsUiState {
    data object Loading : ItemsUiState
    data class Error(val message: String) : ItemsUiState
    data class Success(val items: List<Item>) : ItemsUiState
}
```

## Repository Pattern - Offline-First

```kotlin
class OfflineFirstItemRepository @Inject constructor(
    private val itemDao: ItemDao,
    private val apiService: ItemApiService,
    private val networkMonitor: NetworkMonitor,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) : ItemRepository {

    override val items: Flow<List<Item>> =
        itemDao.getAll().map { entities ->
            entities.map { it.toDomain() }
        }

    override suspend fun refresh() = withContext(ioDispatcher) {
        if (networkMonitor.isOnline) {
            val remoteItems = apiService.getItems()
            itemDao.deleteAllAndInsert(remoteItems.map { it.toEntity() })
        }
    }

    override suspend fun createItem(item: Item) = withContext(ioDispatcher) {
        itemDao.insert(item.toEntity())
        if (networkMonitor.isOnline) {
            apiService.createItem(item.toDto())
        }
    }

    override suspend fun deleteItem(id: String) = withContext(ioDispatcher) {
        itemDao.deleteById(id)
        if (networkMonitor.isOnline) {
            apiService.deleteItem(id)
        }
    }
}
```

## Room Database Setup

### Entity

```kotlin
@Entity(tableName = "items")
data class ItemEntity(
    @PrimaryKey val id: String,
    @ColumnInfo(name = "name") val name: String,
    @ColumnInfo(name = "description") val description: String,
    @ColumnInfo(name = "created_at") val createdAt: Long = System.currentTimeMillis(),
    @ColumnInfo(name = "updated_at") val updatedAt: Long = System.currentTimeMillis(),
)

fun ItemEntity.toDomain() = Item(
    id = id,
    name = name,
    description = description,
)

fun Item.toEntity() = ItemEntity(
    id = id,
    name = name,
    description = description,
)
```

### DAO

```kotlin
@Dao
interface ItemDao {
    @Query("SELECT * FROM items ORDER BY created_at DESC")
    fun getAll(): Flow<List<ItemEntity>>

    @Query("SELECT * FROM items WHERE id = :id")
    fun getById(id: String): Flow<ItemEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(item: ItemEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<ItemEntity>)

    @Query("DELETE FROM items WHERE id = :id")
    suspend fun deleteById(id: String)

    @Transaction
    suspend fun deleteAllAndInsert(items: List<ItemEntity>) {
        deleteAll()
        insertAll(items)
    }

    @Query("DELETE FROM items")
    suspend fun deleteAll()
}
```

### Database

```kotlin
@Database(
    entities = [ItemEntity::class],
    version = 1,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun itemDao(): ItemDao
}
```

### Database Module

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context,
    ): AppDatabase = Room.databaseBuilder(
        context,
        AppDatabase::class.java,
        "app_database",
    ).build()

    @Provides
    fun provideItemDao(database: AppDatabase): ItemDao = database.itemDao()
}
```

### Migration

```kotlin
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE items ADD COLUMN priority INTEGER NOT NULL DEFAULT 0")
    }
}

// In DatabaseModule
@Provides
@Singleton
fun provideDatabase(
    @ApplicationContext context: Context,
): AppDatabase = Room.databaseBuilder(
    context,
    AppDatabase::class.java,
    "app_database",
)
    .addMigrations(MIGRATION_1_2)
    .build()
```

## Retrofit & Network Setup

### API Service

```kotlin
interface ItemApiService {
    @GET("items")
    suspend fun getItems(): List<ItemDto>

    @GET("items/{id}")
    suspend fun getItem(@Path("id") id: String): ItemDto

    @POST("items")
    suspend fun createItem(@Body item: ItemDto): ItemDto

    @DELETE("items/{id}")
    suspend fun deleteItem(@Path("id") id: String)
}
```

### Network Module

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        })
        .build()

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        json: Json,
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    @Provides
    @Singleton
    fun provideItemApiService(retrofit: Retrofit): ItemApiService =
        retrofit.create(ItemApiService::class.java)
}
```

## Hilt DI Module

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {

    @Binds
    abstract fun bindItemRepository(
        impl: OfflineFirstItemRepository,
    ): ItemRepository

    @Binds
    abstract fun bindNetworkMonitor(
        impl: ConnectivityNetworkMonitor,
    ): NetworkMonitor
}
```

## WorkManager Background Sync

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted workerParams: WorkerParameters,
    private val syncManager: SyncManager,
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            syncManager.processSyncQueue()
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Result.failure()
            }
        }
    }
}

// Schedule periodic sync
class SyncScheduler @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    fun schedulePeriodicSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .setRequiresBatteryNotLow(true)
            .build()

        val syncWork = PeriodicWorkRequestBuilder<SyncWorker>(
            repeatInterval = 15,
            repeatIntervalTimeUnit = TimeUnit.MINUTES,
        )
            .setConstraints(constraints)
            .setBackoffCriteria(
                BackoffPolicy.EXPONENTIAL,
                WorkRequest.MIN_BACKOFF_MILLIS,
                TimeUnit.MILLISECONDS,
            )
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "sync_work",
            ExistingPeriodicWorkPolicy.KEEP,
            syncWork,
        )
    }
}
```

## Kotlin-Java Interop Patterns

### @JvmStatic for Companion Objects

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

### @JvmOverloads for Default Parameters

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

### @JvmField for Direct Field Access

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

### @JvmName for Custom JVM Names

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

### Properties vs. Getters/Setters

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

### Data Classes in Java

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

### Extension Functions and Top-Level Functions

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

### Migration Strategy

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

## Offline Synchronization Patterns

### Conflict Resolution - Last-Write-Wins

```kotlin
data class SyncableEntity(
    val id: String,
    val data: String,
    val lastModified: Long,
    val version: Int,
)

suspend fun resolveConflict(
    local: SyncableEntity,
    remote: SyncableEntity,
): SyncableEntity {
    return if (remote.lastModified > local.lastModified) {
        remote.copy(version = remote.version + 1)
    } else {
        local
    }
}
```

### Vector Clocks (Advanced)

```kotlin
data class VectorClock(val timestamps: Map<String, Long>) {
    fun happensBefore(other: VectorClock): Boolean {
        return timestamps.all { (deviceId, timestamp) ->
            timestamp <= (other.timestamps[deviceId] ?: 0)
        } && timestamps != other.timestamps
    }

    fun merge(other: VectorClock): VectorClock {
        val allDevices = timestamps.keys + other.timestamps.keys
        val mergedTimestamps = allDevices.associateWith { deviceId ->
            maxOf(
                timestamps[deviceId] ?: 0,
                other.timestamps[deviceId] ?: 0,
            )
        }
        return VectorClock(mergedTimestamps)
    }
}

data class Versioned<T>(
    val data: T,
    val vectorClock: VectorClock,
)
```

### Delta Sync with Queue Management

```kotlin
@Entity(tableName = "sync_queue")
data class SyncOperation(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val entityType: String,
    val entityId: String,
    val operation: OperationType,
    val payload: String,
    val status: SyncStatus,
    val retryCount: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
)

enum class OperationType { CREATE, UPDATE, DELETE }
enum class SyncStatus { PENDING, IN_PROGRESS, COMPLETED, FAILED }

@Dao
interface SyncQueueDao {
    @Query("SELECT * FROM sync_queue WHERE status = 'PENDING' ORDER BY createdAt ASC")
    fun getPendingOperations(): Flow<List<SyncOperation>>

    @Insert
    suspend fun enqueue(operation: SyncOperation)

    @Update
    suspend fun update(operation: SyncOperation)

    @Query("DELETE FROM sync_queue WHERE status = 'COMPLETED' AND createdAt < :before")
    suspend fun cleanupCompleted(before: Long)
}

class SyncManager @Inject constructor(
    private val syncQueueDao: SyncQueueDao,
    private val apiService: ApiService,
    private val networkMonitor: NetworkMonitor,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) {
    suspend fun processSyncQueue() = withContext(ioDispatcher) {
        if (!networkMonitor.isOnline) return@withContext

        syncQueueDao.getPendingOperations()
            .first()
            .forEach { operation ->
                try {
                    syncQueueDao.update(operation.copy(status = SyncStatus.IN_PROGRESS))

                    when (operation.operation) {
                        OperationType.CREATE -> apiService.create(operation.payload)
                        OperationType.UPDATE -> apiService.update(operation.entityId, operation.payload)
                        OperationType.DELETE -> apiService.delete(operation.entityId)
                    }

                    syncQueueDao.update(operation.copy(status = SyncStatus.COMPLETED))
                } catch (e: Exception) {
                    handleSyncError(operation, e)
                }
            }

        syncQueueDao.cleanupCompleted(System.currentTimeMillis() - 7.days.inWholeMilliseconds)
    }

    private suspend fun handleSyncError(operation: SyncOperation, error: Exception) {
        val maxRetries = 5
        if (operation.retryCount < maxRetries) {
            syncQueueDao.update(
                operation.copy(
                    status = SyncStatus.PENDING,
                    retryCount = operation.retryCount + 1,
                )
            )
        } else {
            syncQueueDao.update(operation.copy(status = SyncStatus.FAILED))
            Timber.e(error, "Sync failed after $maxRetries attempts: ${operation.entityId}")
        }
    }
}
```

### Retry Logic with Exponential Backoff

```kotlin
suspend fun <T> retryWithExponentialBackoff(
    maxRetries: Int = 3,
    initialDelay: Long = 1000,
    maxDelay: Long = 10000,
    factor: Double = 2.0,
    jitter: Boolean = true,
    block: suspend () -> T,
): T {
    var currentDelay = initialDelay
    repeat(maxRetries) { attempt ->
        try {
            return block()
        } catch (e: Exception) {
            if (attempt == maxRetries - 1) throw e

            val delay = if (jitter) {
                currentDelay + Random.nextLong(0, currentDelay / 2)
            } else {
                currentDelay
            }

            Timber.w(e, "Retry attempt ${attempt + 1} failed, retrying in ${delay}ms")
            delay(delay)
            currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelay)
        }
    }
    throw IllegalStateException("Should not reach here")
}

// Usage in repository
override suspend fun syncData(): Result<Unit> = try {
    retryWithExponentialBackoff {
        val localData = dao.getAll().first()
        val remoteData = apiService.fetchAll()
        val merged = mergeWithConflictResolution(localData, remoteData)
        dao.insertAll(merged)
        Result.success(Unit)
    }
} catch (e: Exception) {
    Timber.e(e, "Sync failed after retries")
    Result.failure(e)
}
```
