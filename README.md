# ashforge

Multi-agent engineering plugins for [Claude Code](https://docs.claude.com/en/docs/claude-code/plugins) and [Codex](https://openai.com/codex) (CLI / App).

A personal plugin marketplace by [Andrew Sherepenko](https://github.com/asherepenko).

## Plugins

| Plugin | What It Does |
| --- | --- |
| [`android-expert-toolkit`](./plugins/android-expert-toolkit) | Production-grade Android development: 5 specialized agents (architect, developer, compose, gradle, testing), 7 pipeline types, 80/20 pattern detection, decision council |
| [`avengers-council`](./plugins/avengers-council) | 8-member engineering advisory board (+ Captain America orchestrator) for plan and code review through structured 3-round debate with domain scoring and security veto |

Both plugins ship dual manifests: `.claude-plugin/plugin.json` for Claude Code, `.codex-plugin/plugin.json` for Codex. Skills are the only entry point — slash commands (`/aet-pipeline`, `/avengers-council:plan-review`) were retired in 3.0.0.

## Installation

### Claude Code

```
/plugin marketplace add asherepenko/ashforge
/plugin install android-expert-toolkit@ashforge
/plugin install avengers-council@ashforge
/reload-plugins
```

(Or restart Claude Code to activate.)

### Codex (CLI / App)

```bash
codex plugin marketplace add asherepenko/ashforge
```

Then enable in `~/.codex/config.toml`:

```toml
[plugins."android-expert-toolkit@ashforge"]
enabled = true

[plugins."avengers-council@ashforge"]
enabled = true

[features]
hooks = true            # enable hooks at all
plugin_hooks = true     # enable plugin-bundled hooks
multi_agent = true      # REQUIRED — parallel spawn_agent dispatch for both plugins
```

On first run, Codex will prompt to trust each plugin hook command — accept to record the `trusted_hash` entries. The avengers-council plugin does not ship Codex-side hooks (the `ExitPlanMode` hook is Claude-only), so only android-expert-toolkit's hooks need trust.

### Verify

```
/plugin marketplace list   # ashforge should appear (Claude only)
/plugin                    # interactive plugin manager (Claude only)
```

In Codex, list plugins via `codex plugin list` or via the App's plugin settings. Skills auto-trigger on natural-language description match — try saying "run the aet-pipeline skill" or "review my plan with the council".

## Updating

Marketplace definitions are pulled from GitHub on demand:

```
/plugin marketplace update ashforge        # Claude
codex plugin marketplace update ashforge   # Codex
```

Individual plugins auto-update on every commit unless their `plugin.json` pins a `version`.

## Removing

```
# Claude
/plugin uninstall android-expert-toolkit
/plugin uninstall avengers-council
/plugin marketplace remove ashforge

# Codex
codex plugin remove android-expert-toolkit@ashforge
codex plugin remove avengers-council@ashforge
codex plugin marketplace remove ashforge
```

## Per-Plugin Setup

Each plugin documents its own usage, Codex compatibility, and configuration:

- [android-expert-toolkit/README.md](./plugins/android-expert-toolkit/README.md) and [QUICK_START.md](./plugins/android-expert-toolkit/QUICK_START.md)
- [avengers-council/README.md](./plugins/avengers-council/README.md)
- Cross-platform tool mapping (Claude → Codex): each plugin's `references/codex-tools.md`

## Layout

```
.claude-plugin/
  marketplace.json       # Claude Code marketplace manifest
.agents/plugins/
  marketplace.json       # Codex marketplace manifest
plugins/
  android-expert-toolkit/
  avengers-council/
```

Each plugin under `plugins/` is self-contained — its own `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, agents, skills, hooks, and references. Plugins are cached at `~/.claude/plugins/cache/` (Claude) or `~/.codex/plugins/cache/` (Codex) after install; reference plugin assets via `${CLAUDE_PLUGIN_ROOT}` (Claude) or `${PLUGIN_ROOT}` (Codex) rather than relative paths.

## License

[MIT](./LICENSE) — see individual plugins for additional license details.
