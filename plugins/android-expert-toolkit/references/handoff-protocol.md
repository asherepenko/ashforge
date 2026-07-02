# Handoff Protocol

## When to use

Read this before writing or reading any pipeline handoff artifact. It defines the mechanics shared by all five agents: output paths, directory creation, validation, size limits, and escalation format. Domain-specific content (what goes *inside* each handoff) lives in each agent definition and its template under `${CLAUDE_PLUGIN_ROOT}/templates/`.

## Output Path Construction

Paths are constructed from values in `.artifacts/aet/state.json`:

- `feature_slug`: e.g. `"social-feed"`
- `run_timestamp`: e.g. `"2026-02-18-143022"`

Output: `.artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-{artifact-type}.md`

where `{artifact-type}` is one of: `architecture-blueprint`, `module-setup`, `implementation-report`, `ui-report`, `test-report`, `code-review-report`.

For pipelines without a feature name (e.g. `architecture-review`, `build-optimization`), `feature_slug` equals the pipeline type.

Create the directory if needed before writing:

```bash
mkdir -p .artifacts/aet/handoffs/{feature_slug}
```

The first agent in a pipeline (android-architect) receives `feature_slug` and `run_timestamp` from the pipeline orchestrator via the task prompt.

## Reading Upstream Handoffs

Resolve upstream artifact paths from `.artifacts/aet/state.json` under `artifacts.{artifact-type}` (e.g. `artifacts.architecture-blueprint`) rather than guessing filenames.

## Validation

Required sections for each artifact type are defined by the validator (`${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py`, `REQUIRED_SECTIONS`) and mirrored by the matching template in `${CLAUDE_PLUGIN_ROOT}/templates/` — read the template before writing the handoff.

Run the validator on the handoff before completing:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/validate-handoff.py .artifacts/aet/handoffs/{feature_slug}/{run_timestamp}-{artifact-type}.md
```

It must exit 0. Beyond section presence, the validator also rejects:

- Sections with fewer than 3 non-empty content lines
- Placeholder text (`[TODO]`, `[FILL IN]`, `[TBD]`, `<placeholder>`, `lorem ipsum`)
- `Artifacts Created` sections without real file paths
- Generic filler in `Next Steps` ("continue development", "TBD", ...)

## Size and Style

- Keep the completed handoff under 200 lines. Reference files by path instead of quoting content; include optional template sections only when relevant.
- Be specific: file paths, class names, signatures, measurable constraints.
- Next Steps must be actionable items addressed to a named downstream agent.

## Escalation

When blocked by an upstream decision, a missing prerequisite, or a constraint that cannot be met, do not silently deviate. Escalate to the responsible agent (via the pipeline orchestrator) or the user using this format:

- **Problem** — what is blocked and where (file paths)
- **Impact** — what downstream work this stalls
- **Options** — 2-3 alternatives with trade-offs
- **Recommendation** — the option you would pick and why

Record unresolved escalations in the handoff so the downstream agent sees them.
