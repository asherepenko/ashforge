# iOS Expert Toolkit

Maintainer notes. Usage: [README.md](README.md), [QUICK_START.md](QUICK_START.md).

## Layout

```
ios-expert-toolkit/
├── .claude-plugin/plugin.json   # Claude Code manifest
├── .codex-plugin/plugin.json    # Codex manifest (skills + hooks)
├── .mcp.json                    # Xcode MCP (xcrun mcpbridge)
├── agents/                      # 5 agents, canonical Markdown
├── codex-agents/                # generated Codex TOML agents — do not edit
├── hooks/                       # SessionStart agent linkers
├── skills/
│   ├── ios-expert/              # router
│   ├── ios-conventions/         # own skill: pattern detection
│   ├── ios-testing/             # own skill
│   ├── ios-error-handling/      # own skill
│   ├── tca/                     # own skill
│   ├── swiftui-pro/             # fork of twostraws/SwiftUI-Agent-Skill — see ios-skills.lock
│   ├── community/               # vendored: swift-concurrency, swift-testing-expert, swiftdata-pro — do not edit
│   └── xcode/                   # exported from Xcode, 11 skills listed in ios-skills.lock — do not edit
├── references/                  # topic references, each ≤ ~300 lines
├── scripts/
│   └── sync-ios-skills.sh       # vendors community and Xcode skills (Phase 2.2)
├── ios-skills.lock              # sources, commits, skill lists
├── THIRD_PARTY_NOTICES.md       # licences for vendored content
└── tests/
```

Skill names live in `ios-skills.lock`. Tests read them from there; don't hardcode counts.

## Rules

- **Thin skills, short agents.** Skills route or state rules; detail lives in `references/` or the vendored skills. Agents work from a plain brief (goal, acceptance criteria, files, verify command) and point at skills/references.
- **Own skills via `/create-skill`.** Author or review every own skill and agent with it.
- **Defer to vendored skills.** When a community or Xcode skill covers a topic, the reference keeps a one-line pointer, not a copy.
- **Verify facts.** Check API claims with `/doc-lookup` before a reference states a deprecation or an availability level.

## Vendored skills

`scripts/sync-ios-skills.sh` (added in Phase 2.2) fetches community skills at locked SHAs and exports the Xcode skills with `xcrun agent skills export`. Until it lands, `skills/community/` and `skills/xcode/` stay empty.

## Xcode MCP

`.mcp.json` runs `xcrun mcpbridge` over stdio. Claude Code picks it up from the plugin root. Without Xcode the server fails to connect; skills still load.

## Codex

- Skills: `.codex-plugin/plugin.json` → `"skills": "./skills/"` (a string). Codex scans it recursively, so `skills/community/` and `skills/xcode/` load with no array. The Claude manifest does need the array.
- Hooks: `"hooks": "./hooks/hooks-codex.json"`. The hook files arrive in Phase 4.2. Claude auto-discovers `hooks/hooks.json`.
- Agents: Codex custom agents are TOML, generated from `agents/*.md`.

## Tests

```bash
pytest tests -q
```

## Versioning

Semver in both manifests (they must match; the newest `CHANGELOG.md` heading must equal it):

- **Major**: removed or renamed skills/agents, breaking agent contracts.
- **Minor**: new skills, agents, or vendored skills.
- **Patch**: reference and prompt fixes, upstream skill refreshes.
