# ashforge

Claude Code plugins for multi-agent engineering workflows.

A personal [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugins) by [Andrew Sherepenko](https://github.com/asherepenko).

## Plugins

| Plugin | Description |
| --- | --- |
| [`android-expert-toolkit`](./plugins/android-expert-toolkit) | Expert Android engineering agents and skill for modern Kotlin/Compose/Gradle development |
| [`avengers-council`](./plugins/avengers-council) | 9-member engineering advisory board that reviews planning decisions, code changes, and plan files through structured debate |

## Install

Inside Claude Code, add this repo as a marketplace:

```
/plugin marketplace add asherepenko/ashforge
```

Then install the plugins you want:

```
/plugin install android-expert-toolkit@ashforge
/plugin install avengers-council@ashforge
```

Enable a plugin (or restart Claude Code) to activate it:

```
/plugin enable android-expert-toolkit
/plugin enable avengers-council
```

## Manage

```
/plugin marketplace list              # show registered marketplaces
/plugin marketplace update ashforge   # pull latest plugin definitions
/plugin marketplace remove ashforge   # unregister this marketplace
```

Plugins are cached under `~/.claude/plugins/cache/`. Reference plugin assets from hooks/configs via `${CLAUDE_PLUGIN_ROOT}` rather than relative paths.

## Layout

```
.claude-plugin/
  marketplace.json    # marketplace manifest (name, owner, plugins[])
plugins/
  android-expert-toolkit/
  avengers-council/
```

Each plugin under `plugins/` is a self-contained Claude Code plugin with its own `.claude-plugin/plugin.json`, agents, skills, commands, and hooks.

## License

See individual plugins for license details.
