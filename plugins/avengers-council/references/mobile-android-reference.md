# Mobile & Android Deep Dive Reference — Read on demand when relevant

## When to use

Read this reference when the review involves Android (Kotlin, Jetpack Compose, Room, Hilt) or cross-platform mobile concerns. Detects `android-expert-toolkit` plugin to leverage deeper architectural analysis (offline-first, reactive Flow, feature module independence). Skip for iOS-only, web, or backend reviews.

## Android Deep Dive (Enhanced Mode)

**When reviewing Android code, check if android-expert-toolkit is installed:**

```bash
# Quick check for android-expert-toolkit plugin
ls ~/.claude/plugins/cache/*/android-expert-toolkit/*/skills/android-expert/SKILL.md 2>/dev/null >/dev/null && echo "✓ android-expert-toolkit available" || echo "ℹ using built-in Android knowledge"
```

### If android-expert-toolkit IS installed:

**Leverage its deep Android knowledge for more thorough reviews:**

**Pattern Detection References:**
- Check StateFlow vs LiveData consistency using android-expert's 80/20 rule
- Verify DI framework adherence (Hilt/Koin/Manual) against codebase patterns
- Validate offline-first pattern compliance per android-expert architecture principles
- Reference android-expert-toolkit's `references/pattern-detection.md` for detection commands

**Architecture Principles to Cite:**
- **Offline-first**: Room as source of truth, network updates Room (not vice versa)
- **Reactive architecture**: Flow throughout stack, StateFlow for ViewModels
- **Feature module independence**: No feature-to-feature dependencies (core modules only)
- **Type safety**: Sealed interfaces for UI state, value objects for domain models
- **Convention over configuration**: Gradle convention plugins for standardization

**Reference in Findings:**
```
Example finding format:
"❌ HIGH: Violates offline-first pattern (android-expert-toolkit principle) — ProfileRepository makes network call without caching in Room. Network failures will break feature offline.
Recommendation: Use OfflineFirstUserRepository pattern from android-expert-toolkit with Room as source of truth."
```

**Available Resources (if installed):**
- `references/pattern-detection.md` — Pattern detection commands, 80/20 decision matrix
- `references/conflict-resolution.md` — Priority hierarchy (P0-P3) for competing patterns
- `references/agent-routing.md` — Android agent specializations
- `skills/android-expert/SKILL.md` — Comprehensive Android patterns and principles

**DO NOT invoke android-expert-toolkit agents** — you're a reviewer giving advisory feedback, not an implementer. Reference their knowledge, cite their patterns, but deliver your own council verdict.

### If android-expert-toolkit is NOT installed:

**Use built-in Android expertise:**

**Core Android Patterns to Check:**
- Offline-first architecture (Room as source of truth)
- Reactive state management (StateFlow/Flow, not callbacks)
- Proper lifecycle scoping (lifecycleScope, viewModelScope, not GlobalScope)
- Material 3 design system adherence
- Repository pattern with clear boundaries
- Dependency injection consistency

**Common Android Anti-patterns to Flag:**
- Network/DB on main thread (ANR risk)
- GlobalScope usage (lifecycle leaks)
- LiveData/StateFlow inconsistency within same feature
- Missing ProGuard rules for libraries
- Hardcoded resource values (no offline support)
- Fragment viewBinding leaks (not using viewLifecycleOwner)
- Activity context captured in ViewModels (memory leaks)
