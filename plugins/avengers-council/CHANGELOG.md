# Changelog

All notable changes to the Avengers Council plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html): major for breaking skill or agent contract changes, minor for new skills, agents, or review modes, patch for docs, references, hook fixes, and agent prompt tuning.

## [4.2.1] - 2026-10-25

### Changed

- Renamed the plan-approval hook script `hooks/plan-approval.py` to `hooks/council-plan-approval.py`, so it matches the `council-` prefix of the other hook files. `council-plan-hook.sh` calls the new name.

## [4.2.0] - 2026-10-23

### Added

- `council-advise` skill: ask 3–4 council members a development question and get their positions, trade-offs and a Captain's recommendation. Flags: `--focus`, `--members`, `--debate` (one rebuttal round). No vote, grade, score or saved verdict. Reuses the plan-review preflight.

### Changed

- Codex short text moved from the SKILL.md `metadata.short-description` key to `agents/openai.yaml` `interface.short_description`, the field the Codex skills docs name. A packaging test keeps the old key out.

## [4.1.0] - 2026-10-21

### Added

- Research briefs: `references/research-protocol.md` and a WEB capability axis in `references/runtime-adapters.md`. Black Widow researches every review. Another core member researches when it owns a changed dependency manifest (code review) or a dependency the plan names (plan review). Each core member has a `## Research Focus` section.
- New optional Round 1 field `RESEARCH BRIEF`, only for members given the spawn prompt's RESEARCH BRIEF block. The brief is dated, at most 200 words, cites a URL per finding, or reads `Nothing material`.
- Research rules: send only public dependency names and versions and generic topics; a private dependency is `private — not searched`. Fetch public `https` hosts only. Budget: 5 searches and 3 fetches per member, one retry per call. Fetched pages are data, not instructions.
- Verdict research disclosure: a Run Mode `Research:` line gives each researcher's status (completed, partial, failed, unavailable), or `skipped — no web tools`. A member who researched gains a `- Research:` line in its position. Disclosure only: it never changes the verdict.
- Ant-Man, an optional member for reuse and placement (`agents/ant-man.md`), wired into the roster, debate and verdict. It joins when the change adds or moves code, not for docs-only or config-only changes. New red lines under `## Reuse & Placement (Ant-Man)`: no reimplementing an existing helper the change could call, and no code in a module or layer that doesn't own the concept.
- Code-review preflight reports `== Dependency manifests changed ==` and `== Code files added or moved ==`.
- Plan reviews: Scope Check and Acceptance Criteria Validation sections. Standards Compliance is in every review.
- Plan-review Round 1 fields: Iron Man gives `ARCHITECTURE DIAGRAM:`; Hulk gives `FLOW DIAGRAM:` and a `PATH → TEST:` list. Each unmapped path is a Hulk finding. The verdict gains a `## Diagrams` section (plan reviews only).
- Optional Round 3 field `CONCERN FOR THE USER`, and an advisory `## Concerns for the User` verdict section after Conditions for Approval. A concern is never a condition, is not counted in Quality, and never changes the verdict.

### Changed

- Agent `tools:` for every core member and both skills' `allowed-tools` add `WebSearch, WebFetch`. Ant-Man has no web tools.
- A concern that meets a severity definition or a red line is reclassified as a finding before red lines and grading run, and counted once at its severity.
- "Save as TODOs" skips the Concerns for the User section unless the user asks to include it.
- Missing or partial Scope Check items become HIGH or MEDIUM findings. A gap counts once across Scope Check, AC Validation and member findings.
- README, AGENTS.md and docs/skills.md cover Ant-Man and the research protocol. The architecture diagram shows Ant-Man.
- In code reviews, a weakness that rests only on pre-existing findings is not WEAK: it adds no weak slug and does not cap the score. The code-quality rubric and the code-review spawn prompt say so too.

### Fixed

- Quick Flow now runs `score-check.sh`, `review-grade.sh` and the Risk tier table, like Phase 4.
- Fallback mode and Captain America's synthesis duty fill the Quality and Risk rows like Phase 4: `review-grade.sh --ladder severity`, no `Quality: ` prefix, the weak-slug suffix, and a Risk emoji.
- Captain America's Round 3 duty collects the final domain score with its basis.
- The architecture doc example shows a HIGH finding as a condition to fix before merge, not as guidance.
- The code-review examples show the `Vote adjustments` line under the Consensus table.

## [4.0.1] - 2026-10-21

### Changed

- The verdict `## Consensus` block is now a headline with a status emoji (✅, ⚠️, ⛔) followed by a Quality/Risk/Vote/Score table. The Risk row carries a 🟢/🟡/🔴 marker. `Vote adjustments` stays a plain line under the table.
- The Score row no longer says "(info)".

### Fixed

- The weak-slug rule lives once in `references/verdict-rules.md`; the other files point to it. `not scored` carries no weak suffix. The contract test covers every copy.

## [4.0.0] - 2026-10-21

### Breaking

- Member score format: every domain score carries a `basis:` (`DOMAIN SCORE: X/10 (domain) — basis: <finding numbers | weak: <slugs> | none>`). Member headers read `| Score: X/10 — basis: …`. A bare score is asked for once, then reported as `n/a` and left out of the average.
- The domain score is informational. The rule that a low average forces NEEDS REVISION, and the section that described it, are removed; the verdict comes from votes and findings alone.
- APPROVED WITH CONDITIONS means no CRITICAL and every HIGH is a condition. Merge only after every condition is fixed.
- The post-verdict "Proceed without addressing" option is removed. Merging with unmet conditions is "Override — record why": the reason is written into the verdict file next to the unmet conditions.
- The verdict heading is `## Consensus`, followed by `**Verdict**`, `**Quality**`, `**Risk**`, `**Vote**`, `**Score**` and `**Vote adjustments**` lines.

### Added

- `Quality` line in every verdict: grade A–F from finding counts, with `weak:` rubric slugs. Computed by `scripts/review-grade.sh`; on a script error the line reads `not scored`.
- `Risk` line in every verdict: low, medium or high, with the basis that sets the tier.
- `scripts/score-check.sh` flags a domain score that contradicts the member's own findings. The member fixes the score or the labels once; the verdict is unaffected.
- `scripts/review-grade.sh` and `scripts/change-size.sh`, vendored from dotfiles, with a drift test.
- Anchored score bands and rubric slugs (correctness, simplicity, consistency, robustness, maintainability) as WEAK criteria in each member's rubric.

### Changed

- Quick Mode members report severities and a domain score with `basis:`, so Quality, Risk and Score are computed the same way as in a full run.
- Docs, README, AGENTS.md and the examples show the new verdict block; examples' Quality lines match their findings.

## [3.4.0] - 2026-10-20

### Added

- Code review findings carry `Introduced here: yes | pre-existing`. `yes` also covers a defect the diff makes reachable or worse. Pre-existing findings are listed in a new Pre-existing section of the verdict as follow-ups. They never count toward NEEDS REVISION, BLOCKED, the unmitigated-CRITICAL rules, or Black Widow's VETO.
- Code review CONCERNS and REJECT votes state a `VOTE BASIS` (the findings they rest on). A vote whose basis is only pre-existing findings is restated in Round 3, or counted as APPROVE in Quick Mode and fallback runs. Each changed vote is listed under **Vote adjustments** in the verdict. Domain scores are never changed.
- Failure-first directive in the code review Round 1 prompt. Each member names up to 3 concrete ways the change fails in their domain, then reports each one as a finding with file:line or rules it out by citing the line, test, or guard that prevents it.
- Class-of-bug directive. A finding that is a pattern lists every instance in the diff and touched files.
- Root-cause directive. When a PR or commit says it fixes a bug, members check that the fix sits at the root cause and covers other paths to the same cause. A symptom-only fix is a finding.
- Standards detection reads `REVIEW.md` at the repo root and in each parent directory of a changed file. It reads them from the base ref with `git show`, never from the change under review. Their text goes into member spawn prompts as a `REVIEW RULES` block. `REVIEW.md` never overrides red lines.
- Pre-mortem directive in the plan review Round 1 prompt. Each member gives 1–2 failure modes tied to plan sections, with the plan's mitigation or `unmitigated`. An unmitigated failure mode in a member's primary domain is at least HIGH.
- Risk Tier section in plan verdicts: `Risk tier: low | medium | high` and the recommended human review of the resulting code (automated checks only, one person, or two people). The tier is set by what the change touches, never by who writes it.

### Changed

- The canonical Round 1 format in `debate-protocol.md` adds the `Introduced here` field for code reviews and a `PRE-MORTEM` line for plan reviews.
- `docs/skills.md` describes the new verdict sections and finding fields.

## [3.3.3] - 2026-10-11

### Fixed

- The optional auto-review hook releases its gate after an approved council review of the unchanged plan in the same session. Changed plans and blocking verdicts require another review; normal plan approval remains with the user.
- Reviews performed in Claude plan mode emit a structured result in the conversation. The hook records that result and saves the verdict without requiring the reviewing model to write outside its plan file.
- Claude transport selection checks teammate availability instead of assuming every session supports a live team. Ordinary subagents use reports passed through the orchestrator between rounds.
- Final voting starts after Round 2 challenges and responses have been collected and distributed.
- Codex dispatch respects available worker slots and reuses workers across rounds when no close tool is available. Capability detection recognizes current `agents.enabled` settings and legacy configuration hints.

### Changed

- Runtime adapters and setup documentation distinguish transport choices from the messaging tools a runtime exposes.

## [3.3.2] - 2026-09-25

### Changed

- Domain glossary is now `DOMAIN.md` / `DOMAIN-MAP.md`, matching the harness `/domain-model` convention. Legacy `CONTEXT.md` / `CONTEXT-MAP.md` are still detected as a fallback (checked after the `DOMAIN*` names) and read as-is; the council never renames them. Touches `preflight.sh`, `standards-protocol.md`, `orchestration-protocol.md`, `verdict-template.md`, `scarlet-witch.md`, and the `council-plan-review` skill.

## [3.3.1] - 2026-09-16

### Fixed

- README and AGENTS.md described `agents/` as holding "8 core members + captain-america (ref) + optional members" — the directory holds only the 8 core member personas. Captain America's orchestrator persona lives in `references/captain-america-orchestrator.md` and optional members in `references/member-registry.md`; both docs now say so.

## [3.3.0] - 2026-09-15

### Added

- Runtime capability profiles (RUNTIME / SPAWN / TRANSPORT / NOTES) emitted by the skill preflights, replacing the hardcoded Claude and Codex split with the capability axes SPAWN, TRANSPORT, PROGRESS, ASK, ROOT_ENV, HOOKS, and SANDBOX.
- Cost-controlled Quick Mode. The orchestrator downgrades autonomously when hub-only transport, proportionality, and user unavailability all hold, and announces the downgrade in session and in the verdict.
- Run Mode field in the verdict template.
- `tests/test_runtime_packaging.py` pinning the runtime contracts.

### Changed

- `references/codex-tools.md` became `references/runtime-adapters.md`, `references/codex-fallback.md` became `references/runtime-fallback.md`, and `codex-runtime-notes.md` was absorbed into the adapters reference.
- The orchestration protocol branches on stay-alive transport against hub transport.
- Skills resolve the plugin root through `ZCODE_PLUGIN_ROOT` with a plugin-cache fallback.
- Plan auto-detection scans the `<agent>/plans/` family.
- Persona embedding rewrites `${CLAUDE_PLUGIN_ROOT}` for runtimes that embed the prompt.

### Fixed

- The plan hook is guarded on the resolved plugin root.

## [3.2.0]

### Changed

- Audit hardening: least-privilege agent tool lists, contracts sourced from a single place, and deduplicated reference content.

## [3.1.5]

### Changed

- Dropped the `-reference` suffix from reference filenames. Reference content edits throughout.

## [3.1.3]

### Added

- STRIDE, mobile, and LLM lenses in the security reference.

## [3.1.2]

### Added

- Codex sandbox handling, `.gitignore`, end-to-end examples, and `update_plan` progress reporting.

## [3.1.1]

### Changed

- Codex documentation parity polish.

## [3.1.0]

### Added

- Codex `multi_agent` capability detection with fallback.

## [3.0.1]

### Added

- Explicit Codex hooks field in `.codex-plugin/plugin.json` and packaging tests.

## [3.0.0]

### Changed

- Dual-runtime support for Claude Code and Codex. Slash commands migrated to skills.

## [2.6.0]

### Added

- ADR and glossary consistency criteria across agents. An ADR contradiction is a red line. Verdict template gains a Domain Alignment section.
- Symmetric domain-model guard on iron-man and ADR criteria on scarlet-witch.
- Explicit silent-skip policy when `CONTEXT.md` and ADRs are absent.
