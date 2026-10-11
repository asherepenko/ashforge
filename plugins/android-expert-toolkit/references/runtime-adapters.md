# Runtime Adapters — Capability Profiles for AET Skills

Platform-glue for every skill in this plugin. Skill bodies use Claude Code primitives (`Agent`, `TaskCreate`, `AskUserQuestion`); each other runtime maps onto the capability axes below. Read the preflight's `== Runtime capability ==` section, then resolve each axis — never branch on runtime names, branch on these values. The actual exposed tool inventory and its schemas are authoritative. Configuration and preflight output are hints: override a stale or unknown SPAWN hint when a working spawn tool is exposed, or select `none` when it is absent after tool discovery. Ask only about facts the tool inventory cannot resolve.

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
| `registry` | `Agent({subagent_type: 'android-expert-toolkit:<name>', name: '<name>', prompt: ...})` — inspect the exposed schema, label the stage when supported, and retain the returned agent ID for continuation. Use a unique name for each new invocation; resume by ID with the available continuation tool. Do not assume name reuse retargets messages. No explicit team creation is required. | Claude Code, Zcode |
| `prompt-embed` | `spawn_agent(prompt)` — embed the full agent persona (read from `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md`, frontmatter discarded, **`${CLAUDE_PLUGIN_ROOT}` rewritten to the resolved root**) plus the Pipeline Context Block. No `subagent_type` registry exists. | Codex with an exposed spawn tool |
| `none` | **Read `${CLAUDE_PLUGIN_ROOT}/references/runtime-fallback.md`** and run sequential single-orchestrator dispatch. Do NOT attempt any spawn — it fails at the tool layer. | Runtimes without an exposed spawn tool |
| `unknown` | Inspect and discover the runtime tool inventory first; resolve to a supported spawn profile or `none`. | undetected runtimes |

Dispatch an independent batch in one turn only after prerequisites exist. Gradle/developer parallelism requires existing target modules, required build/source files, and no setup handoff dependency; otherwise finish Gradle setup and validation first.

### Completion and continuation

AET remains **hub-oriented**: specialists have no `SendMessage` and do not negotiate with each other. The orchestrator forwards validated handoffs and collects final answers. Completion delivery depends on the exposed runtime:

- **Claude without teams:** a foreground `Agent` may return its final answer directly. A background agent needs the supported completion notification/wait mechanism.
- **Claude with teams enabled:** named `Agent` launches may become teammates. Collect their final answers from idle notifications, identify the agent by its returned ID, and validate its handoff before advancing. An idle status alone is not proof of a completed stage. Do not assume the spawn response is a blocking final result or that specialists can send peer messages.
- **Current Codex collaboration namespace:** `collaboration.spawn_agent` returns an ID; `collaboration.wait_agent` waits for mailbox updates, not a per-ID final result. Read the resulting messages/final notifications and use `collaboration.list_agents` for status. Continue an idle worker with `collaboration.followup_task`; `collaboration.send_message` can steer a running worker but does not trigger an idle turn. Pass arguments from the actual schemas.
- **Older Codex CLI:** when exposed, use `spawn_agent`, `wait_agent`/`wait`, `send_input` and `close_agent` with their own schemas. Never invent a close or wait tool because an older example names it.

Run bounded batches within available slots. If no close tool is exposed, reuse a small worker pool through the available continuation tool, giving each stage a fresh persona/context prompt; do not spawn a new agent for every stage until slots run out. Sequential dispatch is valid when only one worker slot is available. Modern Codex `agents.max_concurrent_threads_per_session` counts spawned threads, excluding the primary; older `agents.max_threads` is a compatibility alias. A runtime-reported total slot limit takes precedence over these config hints.

Record stage agent IDs in pipeline state. On recovery, prefer continuing that ID; if a fresh spawn is needed, use a unique name and replace the stage's recorded ID. Claude may reject a name whose binding changed. For supported Claude versions, the orchestrator resumes via `SendMessage({to: agent_id, ...})`; use the installed schema instead of assuming a message argument shape.

| Skill references | Claude Code | Other runtimes |
|------------------|-------------|----------------|
| Message a subagent | `SendMessage` to the recorded agent ID using the exposed schema — orchestrator-side only; ordinary subagent resumption needs no agent-team enablement. | Use exposed continuation tools (`followup_task` or legacy `send_input`) and carry validated handoffs in the next stage prompt. |
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

Advisory only — actual exposed tools and schemas win over the preflight and this table.

| Runtime | SPAWN | PROGRESS | ASK | Notes |
|---------|-------|----------|-----|-------|
| claude-code | `registry` | `task-list` | `structured` | Hooks enabled on installation; named agents may return through teammate idle notifications when teams are enabled. |
| codex | `prompt-embed` | `plan-tool` | `plain-text` | `[agents] enabled` defaults true; legacy `features.multi_agent` supported; exposed tools decide capability; hooks gated + trusted; `apply_patch` payloads lack `file_path`. |
| zcode | `registry` | `todo` | `structured` | Result-returning `Agent` spawns; hook parity unverified. |
| pi | `none`* | `none`/extension | `plain-text` | *No native subagent tool — SPAWN=`none` unless a subagent skill/extension is installed (then `prompt-embed`). |
| antigravity | `unknown` | internal | interactive | Claude Agent Skills standard; discover actual tools and inspect spawn shape before dispatch. |

## `update_plan` example

Where the skill body says "TaskCreate / TaskUpdate", use the exposed task/plan tool and its schema. This illustrative `update_plan` shape applies only when accepted by that runtime; otherwise track stages in `.artifacts/aet/state.json`.

```javascript
update_plan({
  steps: [
    { label: "Step 1 — Validate Android project structure",     status: "completed"   },
    { label: "Step 2 — Create pipeline branch",                 status: "completed"   },
    { label: "Step 3 — Initialize state.json",                  status: "completed"   },
    { label: "Step 4 — Dispatch android-architect",             status: "in_progress" },
    { label: "Step 4 — Dispatch gradle + developer per prerequisites", status: "pending"     },
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

[agents]
enabled = true          # default on current Codex; exposed tools remain authoritative
```

Older Codex versions accept `[features] multi_agent = true`; the preflight recognizes explicit legacy true/false when no modern `agents.enabled` value exists. Missing configuration is not evidence that spawning is unavailable. Inspect actual tools before choosing the sequential single-orchestrator fallback in `references/runtime-fallback.md`. See the [Codex subagent documentation](https://developers.openai.com/codex/subagents) for current settings.

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

On POSIX, progress-hook read/modify/write transactions hold a stable sibling `state.lock` and atomically replace `state.json`. This lock coordinates hook processes only. Direct orchestrator updates must wait until every worker in the active batch has delivered a final answer and all their tool calls/hooks have completed; read the latest state and preserve all completed stages. Before-dispatch initialization is also safe. Platforms without Python `fcntl` (including Windows) skip the optional progress cache rather than performing unlocked writes; inline barrier updates remain the source of truth.

Claude's `PostToolUse:Write` hook (`track-progress.py`) auto-updates `.artifacts/aet/state.json` after every tool call. The mirror `hooks/hooks-codex.json` runs the same script on Codex for `local_shell` / `shell` / `shell_command` / `exec_command` events (so validate-handoff results still get recorded), but the script silently no-ops on `apply_patch` because the payload doesn't expose `file_path` directly. On any runtime where hooks are absent or unverified, the orchestrator skill must:

1. Update `state.json` inline at safe batch barriers as part of skill steps (do not rely on the hook firing)
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
