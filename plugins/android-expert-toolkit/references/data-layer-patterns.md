# Data Layer Patterns

Extracted from SKILL.md for progressive disclosure. Referenced when the agent needs detailed data layer, persistence, networking, and sync guidance.

## When to use

Read this reference when implementing the data layer: offline-first repositories, Room DAOs, Retrofit services, WorkManager sync, or Proto DataStore. Used by android-developer during data-layer implementation and by android-architect when defining repository contracts in the blueprint.

## Repository Pattern: Offline-First Implementation

The repository pattern is the cornerstone of the data layer, providing a clean abstraction between data sources and domain/UI layers.

**Key Principles:**
- Local database (Room) as single source of truth
- Expose reactive Flow (never snapshots)
- Network operations update local database
- Offline-first: Writes go to local DB, sync to network when available
- Error handling: Network failures don't block local operations

**Standard Implementation:**

```kotlin
// Repository interface (core:data)
interface ItemRepository {
    val items: Flow<List<Item>>  // Reactive read
    suspend fun refresh()        // Network sync
    suspend fun createItem(item: Item)
    suspend fun deleteItem(id: String)
}

// Offline-first implementation (core:data)
internal class OfflineFirstItemRepository @Inject constructor(
    private val itemDao: ItemDao,
    private val apiService: ItemApiService,
    private val networkMonitor: NetworkMonitor,
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) : ItemRepository {

    // Flow from local database - single source of truth
    override val items: Flow<List<Item>> =
        itemDao.observeAll()
            .map { entities -> entities.map { it.toModel() } }

    // Network refresh updates local database
    override suspend fun refresh() = withContext(ioDispatcher) {
        if (networkMonitor.isOnline) {
            val remoteItems = apiService.getItems()
            itemDao.insertAll(remoteItems.map { it.toEntity() })
        }
    }

    // Write to local DB first, sync to network opportunistically
    override suspend fun createItem(item: Item) = withContext(ioDispatcher) {
        itemDao.insertAll(listOf(item.toEntity()))
        if (networkMonitor.isOnline) {
            try {
                apiService.createItem(item.toDto())
            } catch (e: Exception) {
                // Mark for sync later (see WorkManager sync)
            }
        }
    }

    override suspend fun deleteItem(id: String) = withContext(ioDispatcher) {
        itemDao.deleteById(id)
        if (networkMonitor.isOnline) {
            try {
                apiService.deleteItem(id)
            } catch (e: Exception) {
                // Mark for sync later
            }
        }
    }
}

// Hilt module binding (core:data)
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    @Binds
    internal abstract fun bindsItemRepository(
        impl: OfflineFirstItemRepository,
    ): ItemRepository
}
```

**Supporting Components:**

```kotlin
// Room DAO (core:database)
@Dao
interface ItemDao {
    @Query("SELECT * FROM items")
    fun observeAll(): Flow<List<ItemEntity>>  // Flow, not suspend fun

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(items: List<ItemEntity>)

    @Query("DELETE FROM items WHERE id = :id")
    suspend fun deleteById(id: String)
}

// Retrofit service (core:network)
interface ItemApiService {
    @GET("items")
    suspend fun getItems(): List<ItemDto>

    @POST("items")
    suspend fun createItem(@Body item: ItemDto): ItemDto

    @DELETE("items/{id}")
    suspend fun deleteItem(@Path("id") id: String)
}
```

**Advanced Patterns:**
- Conflict resolution strategies: See "Offline Synchronization Patterns" section below
- Delta sync with queue management: See "Offline Synchronization Patterns" section below
- WorkManager integration: See "Background Work" section

## Data Persistence

### Proto DataStore (Preferences)
- Type-safe alternative to SharedPreferences
- Proto files define schema
- Automatic serialization/deserialization
- Reactive Flow-based API

### Room Database
- Entities with `@Entity`, `@PrimaryKey`, `@ForeignKey`
- DAOs return Flow for reactive queries
- Auto-migrations for schema changes
- FTS (Full-Text Search) for search functionality

```kotlin
@Database(
    entities = [Entity::class],
    version = 1,
    autoMigrations = [AutoMigration(from = 1, to = 2)],
    exportSchema = true,
)
internal abstract class AppDatabase : RoomDatabase() {
    abstract fun dao(): Dao
}

@Dao
interface Dao {
    @Query("SELECT * FROM entity")
    fun observeAll(): Flow<List<Entity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: Entity)
}
```

## Networking

### Retrofit + OkHttp

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .build()

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(KotlinxSerializationConverterFactory.create(Json {
            ignoreUnknownKeys = true
            coerceInputValues = true
        }))
        .build()
}

interface ApiService {
    @GET("items")
    suspend fun getItems(): List<ItemDto>

    @POST("items")
    suspend fun createItem(@Body item: ItemDto): ItemDto
}
```

## Background Work: WorkManager

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val repository: Repository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result = try {
        repository.sync()
        Result.success()
    } catch (e: Exception) {
        Result.retry()
    }
}

// Schedule work
WorkManager.getInstance(context)
    .enqueueUniquePeriodicWork(
        "sync",
        ExistingPeriodicWorkPolicy.KEEP,
        PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS).build()
    )
```

## Common Patterns & Recipes

### Pull-to-Refresh

```kotlin
val pullRefreshState = rememberPullToRefreshState()
if (pullRefreshState.isRefreshing) {
    LaunchedEffect(true) {
        viewModel.refresh()
    }
}

Box(Modifier.nestedScroll(pullRefreshState.nestedScrollConnection)) {
    LazyColumn { /* content */ }
    PullToRefreshContainer(
        state = pullRefreshState,
        modifier = Modifier.align(Alignment.TopCenter),
    )
}
```

### Pagination with Paging 3

```kotlin
@Pager(
    config = PagingConfig(pageSize = 20),
    pagingSourceFactory = { database.dao().pagingSource() }
)
val flow: Flow<PagingData<Entity>>

// In Composable
val lazyPagingItems = flow.collectAsLazyPagingItems()
LazyColumn {
    items(lazyPagingItems.itemCount) { index ->
        lazyPagingItems[index]?.let { ItemCard(it) }
    }
}
```

### Image Loading with Coil

```kotlin
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data(imageUrl)
        .crossfade(true)
        .build(),
    contentDescription = null,
    contentScale = ContentScale.Crop,
    modifier = Modifier.size(128.dp),
)
```

## Migration & Integration

### Integrating with Legacy Code
- Create adapter layer between old and new architecture
- Gradually migrate features one at a time
- Use interface boundaries to isolate legacy code
- Write characterization tests before refactoring

### Third-Party SDK Integration
- Wrap SDKs in repository interfaces
- Inject wrappers via Hilt
- Keep SDK-specific code isolated in data layer
- Test with SDK test doubles
