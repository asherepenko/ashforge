# Testing Framework & Coverage Reference — Read on demand when relevant

## When to use

Read this reference when the review involves test strategy, coverage analysis, test framework choices (Jest, Vitest, pytest, JUnit, Turbine), flaky tests, or CI test optimization. Use to ground findings in framework-specific patterns. Skip for reviews without testable code changes.

## Test Framework Detection & Integration

**Detect project's testing stack:**

```bash
# JavaScript/TypeScript
grep -q "\"jest\"" package.json 2>/dev/null && echo "✓ Jest detected"
grep -q "\"vitest\"" package.json 2>/dev/null && echo "✓ Vitest detected"
grep -q "@testing-library/react" package.json 2>/dev/null && echo "✓ React Testing Library"

# Python
grep -q "pytest" pyproject.toml 2>/dev/null && echo "✓ pytest detected"
test -f pytest.ini && echo "✓ pytest configured"

# Android
grep -q "junit" build.gradle.kts 2>/dev/null && echo "✓ JUnit detected"
grep -q "turbine" build.gradle.kts 2>/dev/null && echo "✓ Turbine (Flow testing)"

# Check for android-expert-toolkit (Android testing patterns)
ls ~/.claude/plugins/cache/*/android-expert-toolkit/*/skills/android-expert/SKILL.md 2>/dev/null >/dev/null && echo "✓ android-expert-toolkit available"
```

## Framework-Specific Patterns

### Jest / Vitest (JavaScript/TypeScript)

**Patterns to check:**
- Mock cleanup: `afterEach(() => jest.resetAllMocks())`
- Timer mocks: `jest.useFakeTimers()` with `advanceTimersByTime()`
- Snapshot tests: prefer `.toMatchInlineSnapshot()` for reviewability
- Async testing: `await` or `.resolves` / `.rejects` matchers
- Mock modules: `jest.mock()` with proper factory functions

**Common issues to flag:**
```
❌ HIGH: Missing afterEach cleanup - mocks leak between tests
❌ MEDIUM: Snapshot tests use `.toMatchSnapshot()` - not reviewable in PR
⚠️ LOW: Using `setTimeout` in tests instead of fake timers
```

### React Testing Library

**Best practices:**
- Use `getByRole` over `getByTestId` (accessibility-first)
- Use `userEvent` instead of `fireEvent` (better simulation)
- Use `waitFor` for async assertions (avoid race conditions)
- Query priority: role > label > placeholder > text > testId

**Anti-patterns to flag:**
```
❌ HIGH: Uses `getByTestId` everywhere - tests implementation details
Recommendation: Use `getByRole('button', {name: 'Submit'})` for semantic queries
Reference: Testing Library guiding principles - test user behavior, not implementation
```

### pytest (Python)

**Patterns to check:**
- Fixture scope (`function` vs `session` - watch for shared state)
- Parametrize for edge cases: `@pytest.mark.parametrize("input,expected", [...])`
- Async tests: `pytest-asyncio` for `async def test_*`
- Mock vs fake: prefer fakes over mocks (matches android-expert philosophy)

**Common issues:**
```
❌ MEDIUM: Fixture has session scope but mutates state - will leak between tests
⚠️ LOW: Single test case - should use parametrize for edge cases (None, "", 0, negative)
```

### JUnit + Turbine (Android)

**If android-expert-toolkit available:**

**Reference android-expert testing patterns:**
- **No mocking philosophy**: Create test doubles (TestRepository with MutableStateFlow)
- **Flow testing with Turbine**: `turbine.test { }` for StateFlow emissions
- **Given-When-Then structure**: Clear test organization
- **MainDispatcherRule**: Replace main dispatcher for deterministic coroutine tests

**Example finding format:**
```
❌ HIGH: Uses Mockito for FeedRepository - violates android-expert-toolkit "no mocking" philosophy
Recommendation: Create TestFeedRepository with MutableStateFlow per android-expert test doubles pattern
Reference: android-expert-toolkit agents/android-testing-specialist.md
```

**If android-expert-toolkit NOT available:**

**Use built-in Android testing knowledge:**
- Prefer test doubles over mocks (better encapsulation)
- Test StateFlow with Turbine library
- Use MainDispatcherRule for coroutine tests
- Target 80%+ coverage for ViewModels and repositories

## Coverage Analysis

**Detect coverage tools:**
```bash
# JavaScript
grep -q "nyc\|c8\|istanbul" package.json && echo "✓ Coverage configured"

# Python
grep -q "pytest-cov\|coverage" pyproject.toml && echo "✓ pytest-cov"

# Android
grep -q "jacoco" build.gradle.kts && echo "✓ JaCoCo coverage"
```

**Coverage recommendations:**
- Unit tests: 80%+ for business logic
- Integration tests: 70%+ for critical paths
- E2E tests: 90%+ for happy paths

**Flag coverage gaps:**
```
❌ HIGH: ProfileViewModel has 43% coverage (target: 80%+)
Missing tests: error handling (0%), pagination edge cases (0%)
Recommendation: Add tests for network failures, empty responses, boundary conditions
```
