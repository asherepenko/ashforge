# Runtime Adapters — Capability Profiles for AET Skills

Platform-glue for every skill in this plugin. Skill bodies use Claude Code primitives (`Agent`, `TaskCreate`, `AskUserQuestion`); each other runtime maps onto the capability axes below. Read the preflight's `== Runtime capability ==` section, then resolve each axis — never branch on runtime names, branch on these values. If an axis reports `unknown`, resolve it conversationally before dispatching agents.

## Contents

- [Capability Axes](#capability-axes)
- [Known Runtime Profiles](#known-runtime-profiles)
- [`update_plan` example](#update_plan-example)
- [Codex feature flags](#codex-feature-flags)
- [Hooks](#hooks)
- [Read-only environment](#read-only-environment)
- [State-file behavior across runtimes](#state-file-behavior-across-runtimes)
- [Plugin Root Resolution](#plugin-root-resolution)

## Capability Axes

### SPAWN — agent dispatch

| Value | Dispatch | Used by |
|-------|----------|---------|
| `registry` | `Agent({subagent_type: 'android-expert-toolkit:<name>', name: '<name>', prompt: ...})` — `name` labels the stage and lets the orchestrator address it; re-dispatching a stage (DP4 recovery) reuses the name. Never pass `team_name` (deprecated and ignored). | Claude Code, Zcode |
| `prompt-embed` | `spawn_agent(prompt)` — embed the full agent persona (read from `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md`, frontmatter discarded, **`${CLAUDE_PLUGIN_ROOT}` rewritten to the resolved root**) plus the Pipeline Context Block. No `subagent_type` registry exists. | Codex (`multi_agent = true`) |
| `none` | **Read `${CLAUDE_PLUGIN_ROOT}/references/runtime-fallback.md`** and run sequential single-orchestrator dispatch. Do NOT attempt any spawn — it fails at the tool layer. | Codex (`multi_agent` off), pi (no subagent skill) |
| `unknown` | Ask the user whether a subagent tool exists before proceeding. | undetected runtimes |

Parallel dispatch (gradle-build-engineer + android-developer) works the same on `registry` and `prompt-embed`: multiple spawn calls in one turn — `Agent({...})` results return inline; on Codex, `wait_agent(agent_id)` per call, then `close_agent(agent_id)` to free slots.

AET is **hub-only by design**: agents have no `SendMessage` in their frontmatter and never message back — every stage returns its report as the tool result plus its handoff artifact. No stay-alive coordination exists on any runtime, so AET has no TRANSPORT branching.

| Skill references | Claude Code | Other runtimes |
|------------------|-------------|----------------|
| Message a subagent | `SendMessage({to: '<agent name>', summary, message})` — orchestrator-side only; it resumes a named agent from its transcript. AET agents never message back. | Not needed — hub-and-spoke: the orchestrator carries context between stages via the next dispatch prompt. |
| Invoke another skill | `Skill({skill, args})` | Skills auto-load on description match — follow the instructions inline or restate them |
| Run shell command | `Bash({command})` | Native shell tool |
| Read / write / edit files | `Read` / `Write` / `Edit` | Native file tools |
| `!`backtick shell expansion in command frontmatter | Auto-expanded at command invocation | Not supported — run the commands explicitly as the skill's first step |
| `allowed-tools` frontmatter field | Restricts available tools per command | Not honored — skills inherit whatever the session permits |
| Plan mode / `ExitPlanMode` tool | First-class plan mode with hook | Skip plan-mode hooks unless the runtime verifies parity |
| `@references/foo.md` mention in skill/agent text | Claude @-mention — auto-resolves and inlines the file content | No @-mention syntax — treat any `@references/<file>.md` as a `Read` instruction; load the file before continuing. With no plugin-root env var, resolve the path per [Plugin Root Resolution](#plugin-root-resolution) |

### PROGRESS — task tracking

| Value | Tool |
|-------|------|
| `task-list` | `TaskCreate` / `TaskUpdate` (Claude Code) |
| `todo` | `TodoWrite` (Zcode) |
| `plan-tool` | `update_plan` (Codex — see [example](#update_plan-example)) |
| `none` | Announce stages in text. |

### ASK — decision points and questions

| Value | Mechanics |
|-------|-----------|
| `structured` | `AskUserQuestion({questions: [{options: [...]}]})` (Claude Code, Zcode) |
| `plain-text` | Print the question and options as plain text; wait for and parse the free-form reply (Codex, pi, most others). |

Unattended runs (user unavailable): DP1 takes auto-detect/cached defaults, DP3 matches the majority pattern, DP4 auto-fixes (max 2 retries) then pauses — and DP2 always pauses for approval (never auto-approved). Never choose Abort or Skip-validation autonomously. Record every autonomous choice in `state.json`.

### ROOT_ENV / HOOKS / SANDBOX

- Plugin root: `CLAUDE_PLUGIN_ROOT` (Claude Code), `PLUGIN_ROOT` (Codex), `ZCODE_PLUGIN_ROOT` (Zcode, expected) — else the [cache-glob fallback](#plugin-root-resolution).
- Hooks: Claude full; Codex gated + trust, deny-only `PreToolUse`; Zcode / pi / Antigravity hook parity unverified — the pipeline never *depends* on hooks (inline state updates are the source of truth).
- Sandboxed worktrees: skip git checkpoints or stage-only, record intended commit messages in `.artifacts/aet/log.md`, and direct the user to the runtime's native "Create branch" / "Hand off to local" controls.

## Known Runtime Profiles

Advisory only — the preflight detection wins over this table.

| Runtime | SPAWN | PROGRESS | ASK | Notes |
|---------|-------|----------|-----|-------|
| claude-code | `registry` | `task-list` | `structured` | Reference runtime; hooks fire fully. |
| codex | `prompt-embed` | `plan-tool` | `plain-text` | Requires `[features] multi_agent = true`; hooks gated + trusted; `apply_patch` payloads lack `file_path`. |
| zcode | `registry` | `todo` | `structured` | Result-returning `Agent` spawns; hook parity unverified. |
| pi | `none`* | `none`/extension | `plain-text` | *No native subagent tool — SPAWN=`none` unless a subagent skill/extension is installed (then `prompt-embed`). |
| antigravity | `unknown` | internal | interactive | Claude Agent Skills standard; custom subagents — confirm spawn shape before dispatch. |

## `update_plan` example

Where the skill body says "TaskCreate / TaskUpdate", plan-tool runtimes use `update_plan`. Pass the full list of steps each call; mark each step `pending`, `in_progress`, or `completed`.

```javascript
update_plan({
  steps: [
    { label: "Step 1 — Validate Android project structure",     status: "completed"   },
    { label: "Step 2 — Create pipeline branch",                 status: "completed"   },
    { label: "Step 3 — Initialize state.json",                  status: "completed"   },
    { label: "Step 4 — Dispatch android-architect",             status: "in_progress" },
    { label: "Step 4 — Dispatch gradle + developer (parallel)", status: "pending"     },
    { label: "Step 4 — Dispatch compose-expert",                status: "pending"     },
    { label: "Step 4 — Dispatch android-testing-specialist",    status: "pending"     },
    { label: "Step 8 — Generate pipeline summary",              status: "pending"     }
  ]
})
```

The plan renders to the user as a checklist. Update it at every stage transition — updates are cheap; call them liberally.

## Codex feature flags

```toml
[features]
hooks = true            # enables hooks at all
plugin_hooks = true     # enables plugin-bundled hooks (still gated separately)
multi_agent = true      # enables spawn_agent/wait_agent/close_agent
```

Without `multi_agent`, parallel agent spawning is unavailable — the preflight detects this (`SPAWN=none`) and the pipeline falls back to sequential single-orchestrator dispatch per `references/runtime-fallback.md`.

Without `hooks` + `plugin_hooks`, hook scripts register in the manifest but never execute. The pipeline still works because the `aet-pipeline` skill updates `state.json` inline; the hooks are an optimization, not a hard dependency.

## Hooks

Codex hooks use the same JSON schema as Claude Code's, with these concrete differences:

| | Claude | Codex |
|---|------|-------|
| Manifest path | `hooks/hooks.json` (auto-discovered; the manifest `hooks` field is for *additional* files only) | `hooks/hooks-codex.json`, declared via `.codex-plugin/plugin.json` → `"hooks"`. **Codex also auto-discovers the legacy `hooks/hooks.json`, so both manifests load.** Every command in `hooks/hooks.json` is wrapped in `if [ -f "${CLAUDE_PLUGIN_ROOT}/…" ]; then … fi` — on Codex that variable expands to empty, the guard fails, and the Claude manifest no-ops instead of erroring. |
| Env var for plugin root | `${CLAUDE_PLUGIN_ROOT}` | `${PLUGIN_ROOT}` |
| `PreToolUse` / `PostToolUse` matchers | Tool names: `Write`, `Edit`, `Bash`, etc. | Tool names: `apply_patch` (for Write/Edit), `local_shell\|shell\|shell_command\|exec_command` (for Bash). Pipe-separated alternation works as a regex matcher. |
| Events available | `PreToolUse`, `PostToolUse`, `SessionStart`, `PreCompact`, `UserPromptSubmit`, `Stop` (and more) | Same set — PascalCase in the JSON, snake_case (`pre_tool_use`, `post_tool_use`, etc.) in `~/.codex/config.toml` trust state |
| `PreToolUse` powers | Allow / deny / inject `additionalContext` | **Deny only** — `permissionDecision: "deny"`. Input modification (`updatedInput`) and `additionalContext` injection are not supported yet ([openai/codex#18491](https://github.com/openai/codex/issues/18491)). Inject context via `PostToolUse` or `SessionStart` instead. |
| Activation | Automatic on install | Requires `[features] hooks = true, plugin_hooks = true` AND user trust of each hook command (recorded as `trusted_hash` in `~/.codex/config.toml`) |

Zcode / pi / Antigravity hook support is unverified — treat as absent until tested. The pipeline tolerates hook-less runtimes by design (inline state + filesystem fallback).

**Tool-payload divergence:** `apply_patch` on Codex doesn't expose `file_path` / `content` the way Claude's `Write` does — the patch text is in `tool_input.input`. Hook scripts that need file paths should either parse the patch headers or skip Codex `apply_patch` payloads and rely on the orchestrator skill updating state inline.

**Trust prompt:** When Codex first encounters a hook command it hasn't seen before, it prompts the user with the command text. The accepted hash is stored in `[hooks.state"<manifest>:<event>:<idx>:<sub>"]`. Editing the hook command resets the hash and requires re-trust.

## Read-only environment

If the runtime runs in a sandboxed worktree where branch creation and push are blocked (Codex App, managed worktrees generally):

- Skip git checkpoints (or stage-only — don't commit)
- Emit a handoff payload at the end describing what would have been committed
- Direct the user to the runtime's "Create branch" / "Hand off to local" controls

## State-file behavior across runtimes

Claude's `PostToolUse:Write` hook (`track-progress.py`) auto-updates `.artifacts/aet/state.json` after every tool call. The mirror `hooks/hooks-codex.json` runs the same script on Codex for `local_shell` / `shell` / `shell_command` / `exec_command` events (so validate-handoff results still get recorded), but the script silently no-ops on `apply_patch` because the payload doesn't expose `file_path` directly. On any runtime where hooks are absent or unverified, the orchestrator skill must:

1. Update `state.json` inline as part of skill steps (don't rely on the hook firing)
2. Fall back to filesystem-derived state when `state.json` is absent or stale — scan `.artifacts/aet/handoffs/<feature_slug>/` for completed artifacts and reconstruct stage status from filenames

Hooks are the fast path on Claude and the validate-handoff fast path on Codex. Inline updates + filesystem fallback are the safety net everywhere.

## Plugin Root Resolution

Skill bodies resolve the plugin root with this chain (first hit wins):

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-${ZCODE_PLUGIN_ROOT:-}}}"
```

If still empty, fall back to the newest cached copy (runtimes without a plugin-root env var install into a versioned cache):

```bash
for base in \
  "$HOME/.zcode/cli/plugins/cache"/*/android-expert-toolkit \
  "$HOME/.claude/plugins/cache"/*/android-expert-toolkit \
  "$HOME/.claude/plugins/cache/android-expert-toolkit" \
  "$HOME/.codex/plugins/cache"/*/android-expert-toolkit \
  "$HOME/.codex/plugins/cache/android-expert-toolkit"; do
  [ -d "$base" ] || continue
  latest="$(ls -1 "$base" 2>/dev/null | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)"
  [ -n "$latest" ] && PLUGIN_ROOT="$base/$latest" && break
done
```

Only fail when every option is exhausted — and then say WHICH variables/paths were tried. The cached copy may trail the repo source; surface `PLUGIN_ROOT` in preflight output when the fallback resolved it.
