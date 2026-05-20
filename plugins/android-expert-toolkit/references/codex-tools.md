## When to use

Read this when running a skill that references Claude-only primitives (`Agent`, `TaskCreate`, `AskUserQuestion`, etc.) inside a Codex CLI or Codex App session. The mapping below tells you which Codex tool to invoke for each Claude-flavored instruction.

This file is platform-glue. Claude Code reads the original tool names natively; Codex reads them and substitutes per the table.

## Tool Mapping

| Skill references | Claude Code | Codex equivalent |
|---|---|---|
| Spawn a subagent | `Agent({subagent_type, prompt})` | `spawn_agent(prompt)` — embed the agent persona text into the prompt (no `subagent_type` registry exists on Codex) |
| Spawn multiple subagents in parallel | Multiple `Agent({...})` calls in one message | Multiple `spawn_agent` calls in one turn |
| Read subagent result | Tool result returned inline | `wait_agent(agent_id)` returns the result; `close_agent(agent_id)` frees the slot |
| Register a team | `TeamCreate({team_name})` | **No equivalent.** Skip the step. Codex has no team primitive — parallel `spawn_agent` calls are the entire concurrency model. |
| Peer-to-peer comms between subagents | `SendMessage({to, content})` | **No equivalent.** Adapt the skill to a hub-and-spoke pattern where the orchestrator carries context between rounds via the next `spawn_agent` prompt. |
| Persist task state across the session | `TaskCreate` / `TaskUpdate` | `update_plan` |
| Ask the user a structured multiple-choice question | `AskUserQuestion({questions: [{options: [...]}]})` | Print the question and options as plain text and wait for the user's reply. Parse free-form answer. |
| Invoke another skill | `Skill({skill, args})` | Skills auto-load on description match — just follow the instructions inline or restate them |
| Run shell command | `Bash({command})` | Native shell tool |
| Read / write / edit files | `Read` / `Write` / `Edit` | Native file tools |
| `!`backtick shell expansion in command frontmatter | Auto-expanded at command invocation | Not supported — run the commands explicitly as the skill's first step |
| `allowed-tools` frontmatter field | Restricts available tools per command | Not honored — Codex skills inherit whatever the session permits |
| Plan mode / `ExitPlanMode` tool | First-class plan mode with hook | No equivalent — skip plan-mode hooks |
| Plugin hooks (`hooks/hooks.json`) | Auto-discovered, fires on all standard events | Mirror manifest at `.codex-plugin/hooks.json` — same JSON schema, see "Hooks" section below |

## Codex feature flags

```toml
[features]
hooks = true            # enables hooks at all
plugin_hooks = true     # enables plugin-bundled hooks (still gated separately)
multi_agent = true      # enables spawn_agent/wait_agent/close_agent
```

Without `multi_agent`, parallel agent spawning is unavailable — skills that depend on it should detect the missing capability and fall back to single-pass execution.

Without `hooks` + `plugin_hooks`, hook scripts register in the manifest but never execute. The pipeline still works because the `aet-pipeline` skill updates `state.json` inline; the hooks are an optimization, not a hard dependency.

## Hooks

Codex hooks use the same JSON schema as Claude Code's, with three concrete differences:

| | Claude | Codex |
|---|---|---|
| Manifest path | `hooks/hooks.json` (auto-discovered) | `.codex-plugin/hooks.json` |
| Env var for plugin root | `${CLAUDE_PLUGIN_ROOT}` | `${PLUGIN_ROOT}` |
| `PreToolUse` / `PostToolUse` matchers | Tool names: `Write`, `Edit`, `Bash`, etc. | Tool names: `apply_patch` (for Write/Edit), `local_shell\|shell\|shell_command\|exec_command` (for Bash). Pipe-separated alternation works as a regex matcher. |
| Events available | `PreToolUse`, `PostToolUse`, `SessionStart`, `PreCompact`, `UserPromptSubmit`, `Stop` (and more) | Same set — PascalCase in the JSON, snake_case (`pre_tool_use`, `post_tool_use`, etc.) in `~/.codex/config.toml` trust state |
| `PreToolUse` powers | Allow / deny / inject `additionalContext` | **Deny only** — `permissionDecision: "deny"`. Input modification (`updatedInput`) and `additionalContext` injection are not supported yet ([openai/codex#18491](https://github.com/openai/codex/issues/18491)). Inject context via `PostToolUse` or `SessionStart` instead. |
| Activation | Automatic on install | Requires `[features] hooks = true, plugin_hooks = true` AND user trust of each hook command (recorded as `trusted_hash` in `~/.codex/config.toml`) |

**Tool-payload divergence:** `apply_patch` on Codex doesn't expose `file_path` / `content` the way Claude's `Write` does — the patch text is in `tool_input.input`. Hook scripts that need file paths should either parse the patch headers or skip Codex `apply_patch` payloads and rely on the orchestrator skill updating state inline.

**Trust prompt:** When Codex first encounters a hook command it hasn't seen before, it prompts the user with the command text. The accepted hash is stored in `[hooks.state."<manifest>:<event>:<idx>:<sub>"]`. Editing the hook command resets the hash and requires re-trust.

## Read-only environment

If Codex App is running in a sandboxed worktree where branch creation and push are blocked:

- Skip git checkpoints (or stage-only — don't commit)
- Emit a handoff payload at the end describing what would have been committed
- Direct the user to the App's "Create branch" / "Hand off to local" controls

## State-file behavior across platforms

Claude's `PostToolUse:Write` hook (`track-progress.py`) auto-updates `.artifacts/aet/state.json` after every tool call. The mirror `.codex-plugin/hooks.json` runs the same script on Codex for `local_shell` / `shell` / `shell_command` / `exec_command` events (so validate-handoff results still get recorded), but the script silently no-ops on `apply_patch` because the payload doesn't expose `file_path` directly. To stay correct on Codex regardless of hook state, the orchestrator skill must:

1. Update `state.json` inline as part of skill steps (don't rely solely on the hook firing)
2. Fall back to filesystem-derived state when `state.json` is absent or stale — scan `.artifacts/aet/handoffs/<feature_slug>/` for completed artifacts and reconstruct stage status from filenames

Hooks remain the fast path on Claude and the validate-handoff fast path on Codex. Inline updates + filesystem fallback are the safety net.
