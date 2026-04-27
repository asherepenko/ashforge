# ashforge

Claude Code plugins for multi-agent engineering workflows.

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins) by [Andrew Sherepenko](https://github.com/asherepenko).

## Plugins

| Plugin | What It Does |
| --- | --- |
| [`android-expert-toolkit`](./plugins/android-expert-toolkit) | Production-grade Android development: 5 specialized agents (architect, developer, compose, gradle, testing), 7 pipeline types, 80/20 pattern detection, decision council |
| [`avengers-council`](./plugins/avengers-council) | 8-member engineering advisory board (+ Captain America orchestrator) for plan and code review through structured 3-round debate with domain scoring and security veto |

## Installation

Register the marketplace from inside Claude Code:

```
/plugin marketplace add asherepenko/ashforge
```

Install one or both plugins:

```
/plugin install android-expert-toolkit@ashforge
/plugin install avengers-council@ashforge
```

Activate them:

```
/reload-plugins
```

(Or restart Claude Code.)

### Verify

```
/plugin marketplace list   # ashforge should appear
/plugin                    # interactive plugin manager
```

If the plugin's slash commands (`/aet-pipeline`, `/avengers-council:plan-review`) don't autocomplete, run `/reload-plugins` once more or restart.

## Updating

Marketplace definitions are pulled from GitHub on demand:

```
/plugin marketplace update ashforge   # pull latest plugin definitions
/reload-plugins                       # apply
```

Individual plugins auto-update on every commit unless their `plugin.json` pins a `version`.

## Removing

```
/plugin uninstall android-expert-toolkit
/plugin uninstall avengers-council
/plugin marketplace remove ashforge
```

## Per-Plugin Setup

Each plugin documents its own usage and configuration:

- [android-expert-toolkit/README.md](./plugins/android-expert-toolkit/README.md) and [QUICK_START.md](./plugins/android-expert-toolkit/QUICK_START.md)
- [avengers-council/README.md](./plugins/avengers-council/README.md)

## Layout

```
.claude-plugin/
  marketplace.json       # marketplace manifest (name, owner, plugins[])
plugins/
  android-expert-toolkit/
  avengers-council/
```

Each plugin under `plugins/` is self-contained — its own `.claude-plugin/plugin.json`, agents, skills, commands, hooks, and references. Plugins are cached at `~/.claude/plugins/cache/` after install; reference plugin assets from hooks/configs via `${CLAUDE_PLUGIN_ROOT}` rather than relative paths.

## License

[MIT](./LICENSE) — see individual plugins for additional license details.
