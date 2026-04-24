# Testing Patterns

Extracted from SKILL.md for progressive disclosure. Referenced when the agent needs detailed testing strategy, test doubles, and coverage guidance.

## When to use

Read this reference when designing a testing strategy: choosing between test doubles vs mocking, setting coverage targets, or deciding which layers need integration vs unit tests. Used by android-testing-specialist during planning. For concrete test implementation examples, see `testing-patterns-detail.md`.

## Testing Strategy

### No Mocking - Test Doubles Pattern

Use real test implementations with controllable behavior instead of mocking frameworks. Test doubles enable fast, isolated tests with constructor injection.

**Example**: `TestRepository`, `TestDataSource`, `TestNetworkMonitor`

**Full patterns and implementation details**: See `android-testing-specialist` agent for comprehensive test double patterns, verification helpers, and best practices.

### Testing Tools
- **Unit Tests**: JUnit 4, Truth (assertions), Turbine (Flow testing)
- **UI Tests**: Compose testing, Roborazzi (screenshot tests)
- **No Mocking**: Constructor injection enables test doubles
- **MainDispatcherRule**: Sets test dispatcher for coroutines

### Test Structure
```
src/
├── main/
│   └── kotlin/
├── test/              # Unit tests
│   └── kotlin/
└── androidTest/       # Instrumented tests
    └── kotlin/
```

## Code Quality Standards

### Code Style
- Kotlin official style guide
- ktlint for formatting
- Spotless for automatic formatting
- Custom lint rules for app-specific patterns
