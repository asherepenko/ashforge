# Android Expert Toolkit

Maintainer notes. Usage: [README.md](README.md), [QUICK_START.md](QUICK_START.md).

## Layout

```
android-expert-toolkit/
├── .claude-plugin/plugin.json   # Claude Code manifest
├── .codex-plugin/plugin.json    # Codex manifest (skills only; no hooks)
├── agents/                      # 5 agents, canonical Markdown
├── codex-agents/                # generated Codex TOML agents — do not edit
├── skills/
│   ├── android-expert/          # router
│   ├── android-testing/         # own skill
│   ├── android-error-handling/  # own skill
│   ├── aet-check/               # pattern detection + cache
│   └── <official skills>/       # vendored, listed in official-skills.lock — do not edit
├── references/                  # topic references, each ≤ ~300 lines
├── scripts/
│   ├── sync-android-skills.sh  # vendors the official skills at a pinned commit
│   └── codex-agents-gen.py      # agents/*.md → codex-agents/*.toml
├── official-skills.lock         # upstream repo, commit, skill list
├── THIRD_PARTY_NOTICES.md       # Apache-2.0 attribution
└── tests/
```

## Rules

- **Thin skills, short agents.** Skills route or state rules; detail lives in `references/` or the official skills. Agents work from a plain brief (goal, acceptance criteria, files, verify command) and point at skills/references instead of embedding pattern dumps. Every agent keeps a `## Scope Boundaries` section.
- **Defer to official skills.** When an official skill covers a topic, the reference keeps a one-line pointer, not a copy.
- **Stack-neutral.** Skills say "detect what the project uses (`aet-check`)"; don't mandate a DI framework, assertion library, HTTP client, or result type.
- **Verify facts.** API claims are checked with `android docs search` / `android docs fetch`; cite the page when a reference states a deprecation or threshold.
- **Cache contract.** `aet-check` writes `.artifacts/aet/cache/detected-patterns.json`. External tools read it; don't move it or rename existing keys.

## Vendored official skills

`scripts/sync-android-skills.sh [ref]` downloads android/skills at `ref` (default: the locked commit), replaces each listed skill directory, copies upstream `LICENSE.txt` into it, and rewrites `official-skills.lock`. `android-cli` is excluded on purpose: users often install their own and a same-named copy would shadow it. To add a skill, add it to `SKILLS` in the script, run it, list it in `THIRD_PARTY_NOTICES.md`, and route it in `skills/android-expert/SKILL.md`.

## Codex

- Skills: `.codex-plugin/plugin.json` → `"skills": "./skills/"`. Each own skill has `agents/openai.yaml` with `interface.short_description`; vendored skills are left as upstream ships them.
- Agents: Codex custom agents are TOML. After editing `agents/*.md`, run `python3 scripts/codex-agents-gen.py --write`; `tests/test_codex_packaging.py` fails on drift.
- No hooks on either runtime.

## Agents

| Agent | Model (Claude) | Tools |
|-------|----------------|-------|
| android-architect | opus | read, write notes, web |
| android-developer | sonnet | read/write/edit, web |
| compose-expert | sonnet | read/write/edit, web |
| gradle-build-engineer | sonnet | read/write/edit (no web: build config shouldn't drift on web content) |
| android-testing-specialist | sonnet | read/write/edit (no web) |

`model` and `tools` frontmatter apply on Claude Code only; Codex agents inherit the session model.

## Tests

```bash
pytest tests -q
```

Covers agent frontmatter/size, Codex packaging and TOML drift, the vendored-skill lock, link and reference-path resolution, and manifest/CHANGELOG version agreement.

## Versioning

Semver in both manifests (they must match; the newest `CHANGELOG.md` heading must equal it):

- **Major**: removed or renamed skills/agents, breaking agent contracts.
- **Minor**: new skills, agents, or vendored official skills.
- **Patch**: reference and prompt fixes, upstream skill refreshes.
