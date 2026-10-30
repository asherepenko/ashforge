# Android Expert Toolkit — Quick Start

## Install

```
/plugin marketplace add asherepenko/ashforge
/plugin install android-expert-toolkit@ashforge
/reload-plugins
```

Codex: see [README.md](README.md#codex-cli--app).

## 1. Ask

Ask in plain language. The `android-expert` skill routes to the right reference or skill:

```
How should I model the error state for this screen?
Is this Room migration safe for users upgrading from 3.2?
Review this Compose screen for accessibility.
```

## 2. Check what the project already uses

```
android-conventions            # all categories
android-conventions di         # one category
android-conventions --fresh    # ignore the 24h cache
```

The result decides between matching the codebase (≥80% consistency) and proposing a change.

## 3. Write tests that find bugs

```
Write tests for CheckoutViewModel.
```

The `android-testing` skill lists break vectors first (emoji length, Int overflow, NaN, clock going backwards, stale response, double-tap, process death), then writes one test per distinct angle.

## 4. Delegate a scoped task

Give an agent a goal, acceptance criteria, files, and a verify command. Pick by layer:

| Task | Agent |
|------|-------|
| New module or layering decision | `android-architect` |
| ViewModel, repository, persistence | `android-developer` |
| Screen, component, previews, a11y | `compose-expert` |
| Build files, catalog, convention plugins | `gradle-build-engineer` |
| Tests or test review | `android-testing-specialist` |

## 5. Platform migrations

Use the official skills directly: `agp-9-upgrade`, `navigation-3`, `edge-to-edge`, `migrate-xml-views-to-jetpack-compose`, `adaptive`.
