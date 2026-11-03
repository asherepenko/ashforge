# iOS Expert Toolkit — Quick Start

## Install

```
/plugin marketplace add asherepenko/ashforge
/plugin install ios-expert-toolkit@ashforge
/reload-plugins
```

Codex: see [README.md](README.md#codex-cli--app).

## 1. Ask

Ask in plain language. The `ios-expert` skill routes to the right reference or skill:

```
Should this new feature use TCA?
Review this SwiftUI view for accessibility.
Write Swift Testing tests for this reducer.
```

## 2. Check what the project already uses

Run `ios-conventions`. The result decides between matching the codebase (80% or more) and proposing a change.

## 3. Use the Xcode MCP

Needs macOS and Xcode. See [README.md](README.md#xcode-mcp-requirements).

## 4. Delegate a scoped task

| Task | Agent |
|------|-------|
| New feature or layering decision | `ios-architect` |
| Models, services, persistence | `ios-developer` |
| Views, previews, accessibility | `swiftui-expert` |
| Tests or test review | `ios-testing-specialist` |
| SPM, schemes, xcconfig, signing | `xcode-build-engineer` |
