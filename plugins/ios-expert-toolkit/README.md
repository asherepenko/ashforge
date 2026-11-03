# iOS Expert Toolkit

iOS knowledge for Claude Code and Codex: a topic router, TCA and SwiftUI skills, pattern detection, vendored community and Xcode skills, the Xcode MCP, and five standalone agents for Swift, SwiftUI and Xcode work.

## What it ships

- **Own skills**: `ios-expert` (router), `ios-conventions` (pattern detection), `ios-testing`, `ios-error-handling`, `tca`, and `swiftui-pro` (a fork of [twostraws/SwiftUI-Agent-Skill](https://github.com/twostraws/SwiftUI-Agent-Skill)).
- **Community skills** (MIT, pinned commits): `swift-concurrency`, `swift-testing-expert`, `swiftdata-pro`.
- **Xcode skills**: 11 skills exported from Xcode (© Apple). Their content depends on the Xcode build they were exported from.
- **Xcode MCP**: `xcrun mcpbridge`, declared in `.mcp.json`.
- **Agents**: `ios-architect`, `ios-developer`, `swiftui-expert`, `ios-testing-specialist`, `xcode-build-engineer`.

## Installation

### Claude Code

```
/plugin marketplace add asherepenko/ashforge
/plugin install ios-expert-toolkit@ashforge
/reload-plugins
```

### Codex (CLI / App)

```bash
codex plugin marketplace add asherepenko/ashforge
```

```toml
[plugins."ios-expert-toolkit@ashforge"]
enabled = true
```

## Xcode MCP requirements

- macOS with Xcode installed.
- The server acts on the Xcode that `xcode-select` points to. Set `MCP_XCODE_PID` to target one running Xcode process (optional).
- Without Xcode, the `xcode` server fails to connect. The plugin still loads, and all skills work.

Check it:

```bash
xcode-select -p
claude --plugin-dir plugins/ios-expert-toolkit mcp list
```

## Third-party content

Licences and sources: `THIRD_PARTY_NOTICES.md` (added with the vendored skills).

## License

MIT. See [LICENSE](LICENSE).
