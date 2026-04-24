# Architecture Patterns

Extracted from SKILL.md for progressive disclosure. Referenced when the agent needs detailed architecture, DI, module organization, and Kotlin pattern guidance.

## When to use

Read this reference when making architectural decisions: choosing MVVM/MVI hybrid, laying out the three-layer architecture, selecting a DI framework (Hilt/Koin/manual), or organizing feature modules. Used by android-architect during blueprint creation and by android-developer when clarifying architectural intent.

## Architecture Pattern: MVVM + MVI Hybrid

### Three-Layer Architecture

#### Data Layer
- **Repositories** - Offline-first pattern, expose Flow (never snapshots)
- **Data Sources** - Room (local), Retrofit (remote), Proto DataStore (preferences)
- **Sync Logic** - WorkManager for background synchronization
- **Critical Rule**: Never expose `getModel()`, always `getModelFlow()`

#### Domain Layer (Optional)
- **Use Cases** - Business logic encapsulation when needed
- **When to use**: Complex business rules, cross-repository composition
- **When to skip**: Simple CRUD operations, direct repository usage is fine

#### UI Layer
- **ViewModels** - StateFlow-based state management, Hilt injection
- **Composables** - Jetpack Compose with Route/Screen separation
- **State Pattern** - Sealed interfaces (Loading, Error, Success states)

### State Management Pattern

```kotlin
// UI State (sealed interface)
sealed interface FeatureUiState {
    data object Loading : FeatureUiState
    data class Error(val message: String) : FeatureUiState
    data class Success(val data: Data) : FeatureUiState
}

// ViewModel (reactive state)
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: Repository,
) : ViewModel() {

    val uiState: StateFlow<FeatureUiState> =
        repository.dataFlow
            .map { FeatureUiState.Success(it) }
            .catch { emit(FeatureUiState.Error(it.message ?: "Unknown error")) }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = FeatureUiState.Loading,
            )

    // Intent methods (user actions)
    fun onAction(action: Action) {
        viewModelScope.launch {
            repository.performAction(action)
        }
    }
}

// Composable (Route + Screen separation)
@Composable
fun FeatureRoute(
    modifier: Modifier = Modifier,
    viewModel: FeatureViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    FeatureScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        modifier = modifier,
    )
}

@Composable
fun FeatureScreen(
    uiState: FeatureUiState,
    onAction: (Action) -> Unit,
    modifier: Modifier = Modifier,
) {
    // Stateless UI composition
}
```

## Module Organization

### Standard Module Structure

```
app/                          # Entry point, navigation, MainActivity
├── feature/
│   ├── feature1/
│   │   ├── api/             # Navigation routes only
│   │   └── impl/            # Screens, ViewModels, internal logic
│   └── feature2/
│       ├── api/
│       └── impl/
├── core/
│   ├── data/               # Repositories, data sources
│   ├── database/           # Room DAOs, entities
│   ├── network/            # Retrofit clients
│   ├── datastore/          # Proto DataStore
│   ├── model/              # Data models (JVM library, no dependencies)
│   ├── ui/                 # Reusable Compose components
│   ├── designsystem/       # Theme, Material3 components
│   ├── navigation/         # Navigation logic
│   ├── testing/            # Test doubles, utilities
│   └── common/             # Shared utilities
└── sync/                   # WorkManager background sync
```

### Module Dependency Rules

**Strict Hierarchy:**
- Features NEVER depend on other feature implementations
- Features MAY depend on other feature APIs (for navigation)
- Core modules NEVER reference features or app module
- Model module maintains absolute independence
- UI flows: Feature -> Data -> Database/Network

## Dependency Injection with Hilt

### Setup Pattern

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {

    @Binds
    internal abstract fun bindsRepository(
        impl: OfflineFirstRepository,
    ): Repository
}

@HiltViewModel
class ViewModel @Inject constructor(
    private val repository: Repository,
) : ViewModel()
```

### Key Principles
- Abstract modules with `@Binds` for interface bindings
- `SingletonComponent` for app-level singletons
- Constructor injection (no field injection)
- Test-friendly: use constructor injection in tests

## Dependency Injection - Multi-Framework Support

### Framework Selection Guide

Choose the appropriate DI framework based on project requirements:

**Hilt - Recommended for Android-First Projects**
- **Use when**: Building Android-only apps, Google-first ecosystem, team prefers compile-time safety
- **Advantages**: Jetpack integration, standardized components, Android lifecycle awareness, compile-time validation
- **Trade-offs**: Android-only, requires Gradle annotation processing (KSP), Dagger complexity underneath
- **Build impact**: Adds ~30s initial build (KSP), incremental builds fast

**Dagger - For Advanced Use Cases**
- **Use when**: Existing Dagger codebase, Kotlin Multiplatform shared code, need fine-grained lifecycle control, performance-critical apps
- **Advantages**: Framework-agnostic (works in KMP), maximum performance, explicit component hierarchy
- **Trade-offs**: Steeper learning curve, more boilerplate, manual component management
- **Build impact**: Similar to Hilt, KSP-based

**Koin - For Kotlin-First Projects**
- **Use when**: Pure Kotlin projects (KMP common code), rapid prototyping, simpler learning curve, faster build times
- **Advantages**: No code generation, DSL-based, minimal boilerplate, runtime injection
- **Trade-offs**: Runtime resolution (no compile-time safety), slightly slower injection, harder to debug
- **Build impact**: Minimal, no annotation processing

**Manual DI - For Simple Projects**
- **Use when**: Small apps (<10 injectable classes), educational purposes, maximum control needed, avoiding framework lock-in
- **Advantages**: Zero dependencies, complete transparency, easiest to understand
- **Trade-offs**: Manual wiring, no scoping, repetitive code at scale
- **Build impact**: None

### Dagger Implementation Patterns

Complete Dagger setup for Android applications with standard patterns.

#### Component Hierarchy

```kotlin
// Application-level component (Singleton scope)
@Singleton
@Component(
    modules = [
        AppModule::class,
        NetworkModule::class,
        DataModule::class,
    ]
)
interface AppComponent {
    // Expose for Activity components
    fun repository(): Repository
    fun networkMonitor(): NetworkMonitor

    // Factory for creating component
    @Component.Factory
    interface Factory {
        fun create(@BindsInstance application: Application): AppComponent
    }
}

// Activity-scoped component
@ActivityScoped
@Subcomponent(modules = [FeatureModule::class])
interface FeatureComponent {
    fun inject(activity: FeatureActivity)

    @Subcomponent.Factory
    interface Factory {
        fun create(): FeatureComponent
    }
}

// Install subcomponent in parent
@Module(subcomponents = [FeatureComponent::class])
interface AppModule

// Application class
class MyApplication : Application() {
    lateinit var appComponent: AppComponent
        private set

    override fun onCreate() {
        super.onCreate()
        appComponent = DaggerAppComponent.factory()
            .create(this)
    }
}
```

#### Module Definition with Provides and Binds

```kotlin
// Abstract module for interface bindings (preferred)
@Module
abstract class DataModule {

    // Use @Binds for interface implementation binding (more efficient)
    @Binds
    @Singleton
    abstract fun bindRepository(
        impl: OfflineFirstRepository
    ): Repository

    // Companion object for @Provides
    companion object {
        @Provides
        @Singleton
        fun provideDatabase(
            application: Application
        ): AppDatabase = Room.databaseBuilder(
            application,
            AppDatabase::class.java,
            "app_database"
        ).build()

        @Provides
        @Singleton
        fun provideDao(database: AppDatabase): ItemDao =
            database.itemDao()
    }
}

// Object module for simple provisions
@Module
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        })
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(KotlinxSerializationConverterFactory.create(Json {
            ignoreUnknownKeys = true
            coerceInputValues = true
        }))
        .build()

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService =
        retrofit.create(ApiService::class.java)
}
```

#### Custom Scopes

```kotlin
// Define custom scopes for lifecycle management
@Scope
@Retention(AnnotationRetention.RUNTIME)
annotation class ActivityScoped

@Scope
@Retention(AnnotationRetention.RUNTIME)
annotation class FragmentScoped

@Scope
@Retention(AnnotationRetention.RUNTIME)
annotation class FeatureScoped

// Usage in modules
@Module
abstract class FeatureModule {

    @Binds
    @ActivityScoped // Lives as long as the Activity
    abstract fun bindFeatureState(
        impl: FeatureStateImpl
    ): FeatureState
}

// Usage in components
@FeatureScoped
@Subcomponent(modules = [FeatureModule::class])
interface FeatureComponent {
    // All provisions with @FeatureScoped will be singletons within this component
}
```

#### ViewModel Injection (Manual Factory)

```kotlin
// ViewModel factory for Dagger
class ViewModelFactory @Inject constructor(
    private val repository: Repository,
    private val analyticsTracker: AnalyticsTracker,
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return when (modelClass) {
            FeatureViewModel::class.java -> FeatureViewModel(
                repository = repository,
                analyticsTracker = analyticsTracker,
            )
            else -> throw IllegalArgumentException("Unknown ViewModel class: $modelClass")
        } as T
    }
}

// Activity injection
class FeatureActivity : ComponentActivity() {

    @Inject
    lateinit var viewModelFactory: ViewModelFactory

    private val viewModel: FeatureViewModel by viewModels { viewModelFactory }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Inject dependencies
        (application as MyApplication)
            .appComponent
            .featureComponent()
            .create()
            .inject(this)

        setContent {
            FeatureScreen(viewModel = viewModel)
        }
    }
}
```

#### Multi-Module Dagger Setup

```kotlin
// Core module component (shared across features)
@Singleton
@Component(modules = [CoreDataModule::class])
interface CoreComponent {
    fun repository(): Repository
    fun database(): AppDatabase
}

// Feature component depends on core
@FeatureScoped
@Component(
    dependencies = [CoreComponent::class],
    modules = [FeatureModule::class]
)
interface FeatureComponent {
    fun inject(activity: FeatureActivity)
}

// Application provides both
class MyApplication : Application() {
    val coreComponent: CoreComponent by lazy {
        DaggerCoreComponent.create()
    }

    fun createFeatureComponent(): FeatureComponent =
        DaggerFeatureComponent.builder()
            .coreComponent(coreComponent)
            .build()
}
```

### Koin Implementation Patterns

DSL-based dependency injection for Kotlin projects.

#### Module Definition

```kotlin
// Define modules using Koin DSL
val networkModule = module {
    // Singleton - created once and reused
    single<OkHttpClient> {
        OkHttpClient.Builder()
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .build()
    }

    single<Retrofit> {
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(get()) // Get dependency from Koin
            .addConverterFactory(KotlinxSerializationConverterFactory.create(Json {
                ignoreUnknownKeys = true
            }))
            .build()
    }

    single<ApiService> { get<Retrofit>().create(ApiService::class.java) }
}

val databaseModule = module {
    single<AppDatabase> {
        Room.databaseBuilder(
            androidContext(),
            AppDatabase::class.java,
            "app_database"
        ).build()
    }

    single<ItemDao> { get<AppDatabase>().itemDao() }
}

val dataModule = module {
    // Bind interface to implementation
    single<Repository> {
        OfflineFirstRepository(
            dao = get(),
            apiService = get(),
            networkMonitor = get(),
            ioDispatcher = Dispatchers.IO,
        )
    }

    single<NetworkMonitor> { NetworkMonitorImpl(androidContext()) }
}

val featureModule = module {
    // Factory - created every time (no caching)
    factory {
        FeatureUseCase(
            repository = get()
        )
    }

    // ViewModel - special scope for Android ViewModels
    viewModel {
        FeatureViewModel(
            repository = get(),
            useCase = get(),
        )
    }
}
```

#### Application Setup

```kotlin
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        startKoin {
            // Enable Android context
            androidContext(this@MyApplication)

            // Enable logging in debug builds
            if (BuildConfig.DEBUG) {
                androidLogger(Level.DEBUG)
            }

            // Load modules
            modules(
                networkModule,
                databaseModule,
                dataModule,
                featureModule,
            )
        }
    }
}
```

#### ViewModel Injection in Compose

```kotlin
@Composable
fun FeatureRoute(
    modifier: Modifier = Modifier,
    viewModel: FeatureViewModel = koinViewModel(), // Koin's Compose integration
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    FeatureScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        modifier = modifier,
    )
}
```

#### Manual Injection (Activities, Fragments)

```kotlin
class FeatureActivity : ComponentActivity() {
    // Inject by lazy delegation
    private val repository: Repository by inject()
    private val analyticsTracker: AnalyticsTracker by inject()

    // ViewModel injection
    private val viewModel: FeatureViewModel by viewModel()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Dependencies already injected
        setContent {
            FeatureScreen(viewModel = viewModel)
        }
    }
}
```

#### Scoping in Koin

```kotlin
// Custom scope for feature lifecycle
val featureScope = module {
    scope<FeatureActivity> {
        // Scoped to FeatureActivity lifecycle
        scoped { FeatureState() }

        // ViewModel scoped to Activity
        viewModel { FeatureViewModel(get(), get()) }
    }
}

// Usage in Activity
class FeatureActivity : ComponentActivity() {
    private val scope = createScope(this)
    private val featureState: FeatureState by scope.inject()

    override fun onDestroy() {
        super.onDestroy()
        scope.close() // Clean up scoped dependencies
    }
}
```

#### Testing with Koin

```kotlin
class FeatureViewModelTest : KoinTest {

    @get:Rule
    val koinTestRule = KoinTestRule.create {
        modules(
            module {
                single<Repository> { TestRepository() }
            }
        )
    }

    @Test
    fun `test feature action`() = runTest {
        val repository: Repository by inject()
        val viewModel = FeatureViewModel(repository)

        // Test with injected test doubles
        viewModel.performAction()

        // Verify
    }
}
```

### Manual Dependency Injection Patterns

Simple container-based DI for small projects.

#### Container Pattern

```kotlin
// Application-level container
class AppContainer(private val context: Context) {

    // Lazily initialized singletons
    val database: AppDatabase by lazy {
        Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "app_database"
        ).build()
    }

    private val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .build()
    }

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(KotlinxSerializationConverterFactory.create(Json {
                ignoreUnknownKeys = true
            }))
            .build()
    }

    val apiService: ApiService by lazy {
        retrofit.create(ApiService::class.java)
    }

    val repository: Repository by lazy {
        OfflineFirstRepository(
            dao = database.itemDao(),
            apiService = apiService,
            networkMonitor = NetworkMonitorImpl(context),
            ioDispatcher = Dispatchers.IO,
        )
    }

    // Factory method for ViewModels (creates new instance each time)
    fun createFeatureViewModel(): FeatureViewModel {
        return FeatureViewModel(
            repository = repository,
        )
    }
}

// Application class
class MyApplication : Application() {
    lateinit var appContainer: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        appContainer = AppContainer(this)
    }
}
```

#### ViewModel Factory for Manual DI

```kotlin
// Generic ViewModel factory
class AppViewModelFactory(
    private val container: AppContainer,
) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return when (modelClass) {
            FeatureViewModel::class.java -> container.createFeatureViewModel()
            // Add other ViewModels here
            else -> throw IllegalArgumentException("Unknown ViewModel: $modelClass")
        } as T
    }
}

// Activity usage
class FeatureActivity : ComponentActivity() {

    private val appContainer
        get() = (application as MyApplication).appContainer

    private val viewModelFactory by lazy {
        AppViewModelFactory(appContainer)
    }

    private val viewModel: FeatureViewModel by viewModels { viewModelFactory }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            FeatureScreen(viewModel = viewModel)
        }
    }
}
```

#### Compose Integration for Manual DI

```kotlin
// Provide container via CompositionLocal
val LocalAppContainer = staticCompositionLocalOf<AppContainer> {
    error("AppContainer not provided")
}

// In MainActivity
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val appContainer = (application as MyApplication).appContainer

        setContent {
            CompositionLocalProvider(LocalAppContainer provides appContainer) {
                AppTheme {
                    AppNavigation()
                }
            }
        }
    }
}

// Access in composables
@Composable
fun FeatureRoute(
    modifier: Modifier = Modifier,
) {
    val appContainer = LocalAppContainer.current

    // Create ViewModel manually
    val viewModel = viewModel<FeatureViewModel>(
        factory = AppViewModelFactory(appContainer)
    )

    FeatureScreen(
        viewModel = viewModel,
        modifier = modifier,
    )
}
```

#### Feature-Specific Containers

```kotlin
// Feature container for feature-scoped dependencies
class FeatureContainer(
    private val appContainer: AppContainer,
) {
    // Feature-specific dependencies
    val featureState: FeatureState by lazy {
        FeatureState()
    }

    val featureUseCase: FeatureUseCase by lazy {
        FeatureUseCase(
            repository = appContainer.repository,
        )
    }

    fun createFeatureViewModel(): FeatureViewModel {
        return FeatureViewModel(
            repository = appContainer.repository,
            useCase = featureUseCase,
            state = featureState,
        )
    }
}

// Activity creates feature container
class FeatureActivity : ComponentActivity() {
    private val featureContainer by lazy {
        FeatureContainer(
            appContainer = (application as MyApplication).appContainer
        )
    }

    private val viewModelFactory by lazy {
        object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return featureContainer.createFeatureViewModel() as T
            }
        }
    }

    private val viewModel: FeatureViewModel by viewModels { viewModelFactory }
}
```

#### Testing with Manual DI

```kotlin
// Test container with test doubles
class TestAppContainer : AppContainer(
    context = ApplicationProvider.getApplicationContext()
) {
    override val repository: Repository by lazy {
        TestRepository()
    }

    override val apiService: ApiService by lazy {
        TestApiService()
    }
}

// Test
class FeatureViewModelTest {
    private lateinit var testContainer: TestAppContainer
    private lateinit var viewModel: FeatureViewModel

    @Before
    fun setup() {
        testContainer = TestAppContainer()
        viewModel = testContainer.createFeatureViewModel()
    }

    @Test
    fun `test feature action`() = runTest {
        // Test with test doubles from container
        viewModel.performAction()

        // Verify state
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf<FeatureUiState.Success>()
    }
}
```

### Framework Migration Guide

#### Migrating from Hilt to Koin

```kotlin
// Before (Hilt)
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    @Binds
    internal abstract fun bindsRepository(
        impl: OfflineFirstRepository,
    ): Repository
}

// After (Koin)
val dataModule = module {
    single<Repository> {
        OfflineFirstRepository(
            dao = get(),
            apiService = get(),
        )
    }
}

// Before (Hilt ViewModel)
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: Repository,
) : ViewModel()

// After (Koin ViewModel)
class FeatureViewModel(
    private val repository: Repository,
) : ViewModel()

// Koin module for ViewModel
val viewModelModule = module {
    viewModel { FeatureViewModel(get()) }
}
```

#### Migrating from Manual DI to Hilt

```kotlin
// Before (Manual container)
class AppContainer(context: Context) {
    val repository: Repository by lazy {
        OfflineFirstRepository(
            dao = database.itemDao(),
            apiService = apiService,
        )
    }
}

// After (Hilt module)
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    @Binds
    abstract fun bindsRepository(
        impl: OfflineFirstRepository,
    ): Repository
}

// Before (Manual ViewModel factory)
private val viewModelFactory = object : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return FeatureViewModel(appContainer.repository) as T
    }
}

// After (Hilt ViewModel)
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: Repository,
) : ViewModel()

// Usage stays the same
private val viewModel: FeatureViewModel by viewModels()
```

### Framework Comparison Matrix

| Feature | Hilt | Dagger | Koin | Manual |
|---------|------|--------|------|--------|
| Compile-time safety | Yes | Yes | No | No |
| Runtime performance | Excellent | Excellent | Good | Excellent |
| Build time impact | Medium | Medium | None | None |
| Learning curve | Medium | Steep | Easy | Easiest |
| Boilerplate | Low | High | Minimal | Medium |
| Android integration | Excellent | Good | Excellent | Manual |
| KMP support | No | Yes | Yes | Yes |
| ViewModel support | Built-in | Manual | Built-in | Manual |
| Scope management | Automatic | Manual | Flexible | Manual |
| Testability | Excellent | Excellent | Excellent | Excellent |
| Debug difficulty | Medium | Hard | Easy | Easiest |

### DI Best Practices (Framework-Agnostic)

1. **Constructor Injection Always** - Pass dependencies through constructors, never use field injection
2. **Depend on Interfaces** - Inject interfaces, not concrete implementations
3. **Single Responsibility** - Each module/container should have one clear purpose
4. **Avoid God Objects** - Don't inject the entire container, inject specific dependencies
5. **Lifecycle Awareness** - Match dependency scope to consumer lifecycle
6. **Test Doubles, Not Mocks** - Use real implementations with controllable behavior for tests
7. **Consistent Naming** - Use clear naming conventions (e.g., `*Module`, `*Component`, `*Container`)
8. **Documentation** - Document complex dependency graphs and custom scopes

## Security Architecture

### Certificate Pinning

**Primary approach: `network_security_config.xml`** (recommended for most projects):

```xml
<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2027-01-01">
            <pin digest="SHA-256">AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=</pin>
            <pin digest="SHA-256">BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=</pin>
        </pin-set>
    </domain-config>

    <!-- Disable cleartext traffic in production -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Allow cleartext for debug builds only -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

```xml
<!-- AndroidManifest.xml -->
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ... >
```

**Secondary approach: OkHttp `CertificatePinner`** (for dynamic pin management or when XML config is insufficient):

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkSecurityModule {

    @Provides
    @Singleton
    fun provideCertificatePinner(): CertificatePinner = CertificatePinner.Builder()
        .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        .add("api.example.com", "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=")
        .build()

    @Provides
    @Singleton
    fun provideOkHttpClient(
        certificatePinner: CertificatePinner,
    ): OkHttpClient = OkHttpClient.Builder()
        .certificatePinner(certificatePinner)
        .build()
}
```

### Encrypted Data Storage

**Recommended: `EncryptedFile` for new projects** (more flexible than EncryptedSharedPreferences):

```kotlin
// EncryptedFile for general-purpose encrypted storage
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val encryptedFile = EncryptedFile.Builder(
    context,
    File(context.filesDir, "secure_data.json"),
    masterKey,
    EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB,
).build()

// Write encrypted data
encryptedFile.openFileOutput().bufferedWriter().use { writer ->
    writer.write(Json.encodeToString(sensitiveData))
}

// Read encrypted data
val content = encryptedFile.openFileInput().bufferedReader().use { it.readText() }
val data = Json.decodeFromString<SensitiveData>(content)
```

```kotlin
// Encrypted Proto DataStore (for structured preferences)
val Context.secureDataStore: DataStore<SecurePreferences> by dataStore(
    fileName = "secure_prefs.pb",
    serializer = SecurePreferencesSerializer(
        EncryptedFile.Builder(
            context,
            File(context.filesDir, "secure_prefs.pb"),
            MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build(),
            EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB
        ).build()
    )
)
```

```kotlin
// Encrypted Room Database with SQLCipher
@Database(entities = [/*...*/], version = 1)
abstract class SecureDatabase : RoomDatabase() {
    companion object {
        fun build(context: Context): SecureDatabase {
            val passphrase = SQLiteDatabase.getBytes(
                MasterKey.Builder(context)
                    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                    .build()
                    .toString()
                    .toCharArray()
            )

            return Room.databaseBuilder(context, SecureDatabase::class.java, "secure.db")
                .openHelperFactory(SupportFactory(passphrase))
                .build()
        }
    }
}
```

### Secure Credential Storage

```kotlin
// Android Keystore for sensitive tokens and credentials
class SecureCredentialStorage @Inject constructor(
    private val context: Context,
) {
    private val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    private val cipher: Cipher
        get() = Cipher.getInstance(
            KeyProperties.KEY_ALGORITHM_AES + "/" +
            KeyProperties.BLOCK_MODE_GCM + "/" +
            KeyProperties.ENCRYPTION_PADDING_NONE
        )

    fun storeToken(token: String) {
        val key = getOrCreateKey()
        val cipher = cipher.apply {
            init(Cipher.ENCRYPT_MODE, key)
        }

        val encrypted = cipher.doFinal(token.toByteArray())
        val iv = cipher.iv

        context.getSharedPreferences("secure", Context.MODE_PRIVATE)
            .edit()
            .putString("token", Base64.encodeToString(encrypted, Base64.DEFAULT))
            .putString("iv", Base64.encodeToString(iv, Base64.DEFAULT))
            .apply()
    }

    private fun getOrCreateKey(): SecretKey {
        return if (keyStore.containsAlias(KEY_ALIAS)) {
            (keyStore.getEntry(KEY_ALIAS, null) as KeyStore.SecretKeyEntry).secretKey
        } else {
            KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
                .apply {
                    init(
                        KeyGenParameterSpec.Builder(
                            KEY_ALIAS,
                            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                        )
                            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                            .setUserAuthenticationRequired(false)
                            .build()
                    )
                }
                .generateKey()
        }
    }

    companion object {
        private const val KEY_ALIAS = "app_master_key"
    }
}
```

### ProGuard/R8 Configuration

```kotlin
// Convention plugin for release security
class AndroidReleaseSecurityPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            extensions.configure<ApplicationExtension> {
                buildTypes {
                    release {
                        isMinifyEnabled = true
                        isShrinkResources = true
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

**proguard-rules.pro template:**
```proguard
# Keep data models for serialization
-keep class com.example.app.core.model.** { *; }

# Keep Retrofit service interfaces
-keep interface com.example.app.core.network.** { *; }

# Keep Room entities
-keep @androidx.room.Entity class *
-keepclassmembers class * {
    @androidx.room.* <methods>;
}

# Keep Hilt generated classes
-keep class dagger.hilt.** { *; }
-keep class * extends dagger.hilt.android.internal.managers.ViewComponentManager$FragmentContextWrapper { *; }

# Kotlinx Serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers class kotlinx.serialization.json.** {
    *** Companion;
}
```

### Security Architecture Checklist

```
NETWORK SECURITY
- Certificate pinning via network_security_config.xml (primary)
- OkHttp CertificatePinner for dynamic pins (secondary)
- Backup pins configured (2+ pins per domain)
- Cleartext traffic disabled in production
- TLS 1.2+ enforced

DATA ENCRYPTION
- EncryptedFile for general encrypted storage (recommended for new projects)
- Proto DataStore encrypted for structured sensitive data
- Room database encrypted with SQLCipher
- Android Keystore used for credential storage
- No sensitive data in SharedPreferences (unencrypted)
- Biometric auth for sensitive operations

CODE OBFUSCATION
- ProGuard/R8 enabled for release builds
- Resource shrinking enabled
- Debug symbols removed in release
- Custom ProGuard rules for data models

API SECURITY
- API keys not hardcoded (BuildConfig only)
- Token refresh mechanism implemented
- Request signing for critical operations
- Rate limiting handled gracefully
- Input validation on all user input

AUTHENTICATION
- Secure token storage (Keystore)
- Token expiration handling
- Biometric authentication option
- Screen capture disabled for sensitive screens
- Session timeout implemented
```

## Build System: Gradle Convention Plugins

### Structure

```
build-logic/
├── convention/
│   └── src/main/kotlin/
│       ├── AndroidApplicationConventionPlugin.kt
│       ├── AndroidLibraryConventionPlugin.kt
│       ├── AndroidFeatureApiConventionPlugin.kt
│       ├── AndroidFeatureImplConventionPlugin.kt
│       ├── AndroidComposeConventionPlugin.kt
│       ├── HiltConventionPlugin.kt
│       └── AndroidLintConventionPlugin.kt
└── build.gradle.kts
```

### Usage in Module build.gradle.kts

```kotlin
plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
    id("your.app.android.feature.impl")
    id("your.app.android.compose")
    id("your.app.hilt")
}
```

### Version Catalog (gradle/libs.versions.toml)

```toml
[versions]
kotlin = "2.3.10"
compose-bom = "2025.09.01"
hilt = "2.59"
room = "2.8.3"

[libraries]
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version.ref = "core-ktx" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
```

## Coroutines & Flow Best Practices

### Flow Operators

```kotlin
// Combine multiple sources
combine(flow1, flow2, flow3) { a, b, c ->
    Result(a, b, c)
}

// Transform and filter
flow.map { it.toUiModel() }
    .filter { it.isValid() }
    .distinctUntilChanged()

// Error handling
flow.catch { exception ->
    emit(ErrorState(exception))
}

// State conversion
flow.stateIn(
    scope = viewModelScope,
    started = SharingStarted.WhileSubscribed(5_000),
    initialValue = InitialState,
)
```

### Dispatcher Management

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DispatchersModule {
    @Provides
    @Dispatcher(IO)
    fun providesIODispatcher(): CoroutineDispatcher = Dispatchers.IO

    @Provides
    @Dispatcher(Default)
    fun providesDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default
}

// Usage
class Repository @Inject constructor(
    @Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
) {
    suspend fun loadData() = withContext(ioDispatcher) {
        // IO operation
    }
}
```

## Navigation with Type-Safe Routes

### @Serializable Route Definitions

```kotlin
// Define routes as @Serializable data classes/objects
@Serializable
data object HomeRoute

@Serializable
data class ItemDetailRoute(val itemId: String)

@Serializable
data class ProfileRoute(val userId: String, val tab: ProfileTab = ProfileTab.OVERVIEW)

@Serializable
enum class ProfileTab { OVERVIEW, SETTINGS, ACTIVITY }

// Nested navigation graph route
@Serializable
data object SettingsGraphRoute
```

### NavHost Setup with Type-Safe Routes

```kotlin
@Composable
fun AppNavHost(
    navController: NavHostController = rememberNavController(),
    modifier: Modifier = Modifier,
) {
    NavHost(
        navController = navController,
        startDestination = HomeRoute,
        modifier = modifier,
    ) {
        composable<HomeRoute> {
            HomeRoute(
                onNavigateToItem = { itemId ->
                    navController.navigate(ItemDetailRoute(itemId))
                },
                onNavigateToProfile = { userId ->
                    navController.navigate(ProfileRoute(userId))
                },
            )
        }

        composable<ItemDetailRoute> { backStackEntry ->
            val route = backStackEntry.toRoute<ItemDetailRoute>()
            ItemDetailRoute(itemId = route.itemId)
        }

        composable<ProfileRoute> { backStackEntry ->
            val route = backStackEntry.toRoute<ProfileRoute>()
            ProfileRoute(userId = route.userId, initialTab = route.tab)
        }

        // Nested navigation graph
        navigation<SettingsGraphRoute>(startDestination = SettingsMainRoute) {
            composable<SettingsMainRoute> { /* ... */ }
            composable<SettingsNotificationsRoute> { /* ... */ }
        }
    }
}
```

### Multi-Module Navigation with Feature APIs

```kotlin
// feature/items/api - Navigation contract
@Serializable
data class ItemsRoute(val category: String? = null)

@Serializable
data class ItemDetailRoute(val itemId: String)

// feature/items/impl - Graph registration
fun NavGraphBuilder.itemsGraph(
    onNavigateToDetail: (String) -> Unit,
    onNavigateBack: () -> Unit,
) {
    composable<ItemsRoute> { backStackEntry ->
        val route = backStackEntry.toRoute<ItemsRoute>()
        ItemsRoute(
            category = route.category,
            onItemClick = onNavigateToDetail,
        )
    }

    composable<ItemDetailRoute> { backStackEntry ->
        val route = backStackEntry.toRoute<ItemDetailRoute>()
        ItemDetailRoute(
            itemId = route.itemId,
            onBack = onNavigateBack,
        )
    }
}

// app module - Wiring feature graphs
NavHost(navController = navController, startDestination = HomeRoute) {
    itemsGraph(
        onNavigateToDetail = { id -> navController.navigate(ItemDetailRoute(id)) },
        onNavigateBack = { navController.popBackStack() },
    )
    profileGraph(/* ... */)
}
```

## App Links & Deep Links

### AndroidManifest.xml Intent Filters

```xml
<activity android:name=".MainActivity"
    android:exported="true">

    <!-- App Links (verified, HTTPS only) -->
    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https"
              android:host="www.example.com"
              android:pathPrefix="/items" />
    </intent-filter>

    <!-- Deep Links (custom scheme, no verification) -->
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp"
              android:host="items" />
    </intent-filter>
</activity>
```

### Digital Asset Links

Host `/.well-known/assetlinks.json` on your domain for App Link verification:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.example.app",
    "sha256_cert_fingerprints": [
      "AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90"
    ]
  }
}]
```

Get your signing certificate fingerprint:
```bash
keytool -list -v -keystore your-keystore.jks | grep SHA256
```

### Navigation Deep Link Integration

```kotlin
// Route definitions with deep link support
@Serializable
data class ItemDetailRoute(val itemId: String)

// NavHost with deep link mapping
NavHost(navController = navController, startDestination = HomeRoute) {
    composable<ItemDetailRoute>(
        deepLinks = listOf(
            navDeepLink<ItemDetailRoute>(
                basePath = "https://www.example.com/items"
            ),
            navDeepLink<ItemDetailRoute>(
                basePath = "myapp://items"
            ),
        ),
    ) { backStackEntry ->
        val route = backStackEntry.toRoute<ItemDetailRoute>()
        ItemDetailRoute(itemId = route.itemId)
    }
}
```

### Handling Incoming Deep Links

```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val navController = rememberNavController()
            AppNavHost(navController = navController)
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // NavController handles deep link intents automatically
        // when using navDeepLink in the NavHost
    }
}
```

## KSP 2 Annotation Processing

KSP (Kotlin Symbol Processing) replaces kapt for all annotation processors. KSP 2 aligns with the Kotlin compiler pipeline for faster builds.

### Migration from kapt to KSP

```kotlin
// build.gradle.kts - BEFORE (kapt)
plugins {
    id("org.jetbrains.kotlin.kapt")  // Remove this
}
dependencies {
    kapt(libs.hilt.compiler)          // Replace these
    kapt(libs.room.compiler)
}

// build.gradle.kts - AFTER (KSP)
plugins {
    id("com.google.devtools.ksp")     // Use KSP
}
dependencies {
    ksp(libs.hilt.compiler)           // KSP equivalents
    ksp(libs.room.compiler)
}
```

### KSP Configuration in Convention Plugin

```kotlin
class KspConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply("com.google.devtools.ksp")

            // KSP-specific configuration
            extensions.configure<KspExtension> {
                // Room schema export for migration testing
                arg("room.schemaLocation", "${project.projectDir}/schemas")
                arg("room.incremental", "true")
                arg("room.generateKotlin", "true")
            }
        }
    }
}
```

### Version Catalog for KSP

```toml
[versions]
kotlin = "2.3.10"
ksp = "2.3.6"  # KSP version tracks Kotlin version

[plugins]
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
```

### gradle.properties KSP Optimization

```properties
# KSP incremental processing
ksp.incremental=true
ksp.incremental.intermodule=true
```

## Advanced Kotlin Features

### Value Classes for Type Safety

Zero-cost abstraction using inline value classes to prevent parameter mix-ups at compile time.

```kotlin
// Type-safe wrappers with no runtime overhead
@JvmInline
value class UserId(val value: String)

@JvmInline
value class EmailAddress(val value: String)

@JvmInline
value class Timestamp(val millis: Long) {
    fun toFormattedString(): String =
        SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.US).format(Date(millis))
}

// Compile-time safety prevents errors
fun getUserProfile(userId: UserId): UserProfile {
    // Cannot accidentally pass EmailAddress here - compile error!
    return repository.findUser(userId)
}

// Usage
val userId = UserId("user_123")
val email = EmailAddress("user@example.com")
getUserProfile(userId) // Correct
// getUserProfile(email) // Compile error
```

### Context Receivers (Kotlin 1.6.20+)

Enable implicit receiver patterns for cleaner DSLs and dependency access.

```kotlin
// Define context requirements
context(CoroutineScope, Logger)
suspend fun fetchUserData(userId: String): User {
    log("Fetching user: $userId") // Logger from context

    return withContext(Dispatchers.IO) { // CoroutineScope from context
        apiService.getUser(userId)
    }
}

// Provide context when calling
class UserRepository(
    private val apiService: ApiService,
) : CoroutineScope by MainScope() {

    private val logger = Logger("UserRepository")

    suspend fun loadUser(userId: String): User {
        return with(logger) {
            fetchUserData(userId) // Contexts provided implicitly
        }
    }
}

// DSL builder with context
context(StringBuilder)
fun appendSection(title: String, content: String) {
    appendLine("## $title")
    appendLine(content)
    appendLine()
}

fun buildDocument(): String = buildString {
    appendSection("Introduction", "Welcome") // StringBuilder is context
    appendSection("Body", "Main content")
}
```

### Contracts API for Smart Casts

Enable compiler smart casts through contracts.

```kotlin
// Custom validation with contract
fun String?.isNotNullOrBlank(): Boolean {
    contract {
        returns(true) implies (this@isNotNullOrBlank != null)
    }
    return this != null && this.isNotBlank()
}

// Smart cast enabled by contract
fun processInput(input: String?) {
    if (input.isNotNullOrBlank()) {
        // input is smart cast to String (not String?)
        println(input.uppercase()) // No !! or ? needed
    }
}

// Contract for require checks
inline fun requireValidEmail(email: String?) {
    contract {
        returns() implies (email != null)
    }
    require(email?.contains("@") == true) {
        "Invalid email format"
    }
}

fun sendEmail(email: String?) {
    requireValidEmail(email)
    // email is smart cast to String after check
    mailService.send(email)
}
```

### Inline Classes for Performance

Use inline classes to avoid boxing overhead while maintaining type safety.

```kotlin
// Inline class for performance-critical paths
@JvmInline
value class ItemId(val value: Long)

@JvmInline
value class Coordinate(val value: Float) {
    operator fun plus(other: Coordinate): Coordinate =
        Coordinate(value + other.value)

    operator fun times(scale: Float): Coordinate =
        Coordinate(value * scale)
}

// Zero allocation in loops
fun calculateDistance(points: List<Coordinate>): Coordinate {
    var total = Coordinate(0f)
    for (point in points) {
        total += point // No boxing, direct float operations
    }
    return total
}

// Compare with regular class (boxing overhead)
data class CoordinateBoxed(val value: Float) // Each instance allocates object

// Inline class with complex operations
@JvmInline
value class Money(val cents: Long) {
    operator fun plus(other: Money): Money = Money(cents + other.cents)
    operator fun minus(other: Money): Money = Money(cents - other.cents)
    operator fun times(multiplier: Int): Money = Money(cents * multiplier)

    fun toDollars(): Double = cents / 100.0

    companion object {
        fun dollars(amount: Double): Money = Money((amount * 100).toLong())
    }
}

// Usage with zero runtime overhead
val price = Money.dollars(19.99)
val tax = Money.dollars(2.00)
val total = price + tax
```

### Delegation Patterns

Leverage property delegation for cleaner code and reusable behavior.

```kotlin
// Lazy initialization with thread safety
class ImageLoader {
    private val cache: ImageCache by lazy {
        ImageCache(maxSize = 100)
    }

    // Custom delegate for lifecycle-aware properties
    private var currentImage: Bitmap? by lifecycleAware(onDestroy = { it?.recycle() })
}

// Observable properties with custom delegates
class ViewModel {
    var username: String by observable("") { _, old, new ->
        if (old != new) {
            validateUsername(new)
        }
    }

    var isLoading: Boolean by observable(false) { _, _, new ->
        _uiState.value = if (new) UiState.Loading else UiState.Idle
    }
}

// Vetoable delegates
class Settings {
    var theme: Theme by vetoable(Theme.LIGHT) { _, _, new ->
        // Veto changes that require API level 31+
        if (new == Theme.DYNAMIC && Build.VERSION.SDK_INT < 31) {
            false // Reject change
        } else {
            true // Accept change
        }
    }
}

// Custom delegate for preferences
class PreferenceDelegate<T>(
    private val key: String,
    private val default: T,
    private val dataStore: DataStore<Preferences>,
) : ReadWriteProperty<Any?, T> {
    override fun getValue(thisRef: Any?, property: KProperty<*>): T {
        return runBlocking {
            dataStore.data.first()[stringPreferencesKey(key)] as? T ?: default
        }
    }

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        runBlocking {
            dataStore.edit { prefs ->
                prefs[stringPreferencesKey(key)] = value.toString()
            }
        }
    }
}
```

### Emerging Patterns

**Circuit (Slack)** — A Compose-driven architecture where presenters are composable functions that produce state and handle events. Eliminates the ViewModel layer entirely and uses Compose's runtime for state management.

```kotlin
// Circuit presenter — a composable that returns state
@CircuitInject(ItemsScreen::class, AppScope::class)
@Composable
fun ItemsPresenter(navigator: Navigator): ItemsState {
    var items by remember { mutableStateOf<List<Item>>(emptyList()) }

    LaunchedEffect(Unit) {
        items = repository.getItems()
    }

    return ItemsState(items = items) { event ->
        when (event) {
            is ItemsEvent.ItemClicked -> navigator.goTo(ItemDetailScreen(event.id))
        }
    }
}
```

**Molecule (Cash App)** — Turns Compose's runtime into a general-purpose reactive state engine. Useful for building reactive state outside of UI — in ViewModels, presenters, or repositories.

```kotlin
// Molecule-powered ViewModel — Compose runtime for state production
class ItemsViewModel(private val repository: Repository) : ViewModel() {
    val uiState: StateFlow<ItemsUiState> = moleculeScope.launchMolecule(RecompositionMode.Immediate) {
        val items by repository.itemsFlow().collectAsState(emptyList())
        val isRefreshing by remember { mutableStateOf(false) }

        ItemsUiState(items = items, isRefreshing = isRefreshing)
    }
}
```

Both are worth evaluating for greenfield projects where the team is comfortable with Compose's runtime model beyond UI rendering. For existing projects using MVVM + StateFlow, migration is not necessary.

### Sealed Class Hierarchies

Model state and results with exhaustive when expressions.

```kotlin
// Complex state modeling
sealed interface NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>

    sealed interface Error : NetworkResult<Nothing> {
        data class Http(val code: Int, val message: String) : Error
        data class Network(val exception: IOException) : Error
        data class Unknown(val throwable: Throwable) : Error
    }

    data object Loading : NetworkResult<Nothing>
}

// Exhaustive handling (compiler ensures all cases covered)
fun <T> handleResult(result: NetworkResult<T>) {
    when (result) {
        is NetworkResult.Success -> showData(result.data)
        is NetworkResult.Error.Http -> showHttpError(result.code)
        is NetworkResult.Error.Network -> showNetworkError()
        is NetworkResult.Error.Unknown -> showUnknownError(result.throwable)
        NetworkResult.Loading -> showLoading()
    }
} // No else needed - compiler knows all cases covered

// UI state with nested sealed hierarchies
sealed interface ScreenState {
    data object Loading : ScreenState

    sealed interface Content : ScreenState {
        data class Loaded(val items: List<Item>) : Content
        data class Empty(val message: String) : Content
    }

    sealed interface Error : ScreenState {
        data class Recoverable(val message: String, val retry: () -> Unit) : Error
        data class Fatal(val message: String) : Error
    }
}
```
