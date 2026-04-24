# Council Member Registry

Single source of truth for the Avengers Council roster. The orchestration protocol reads this to determine which members to spawn.

## Core Members (always active)

Core members participate in every full council session. They define the council's identity.

| Name | subagent_type | Domain | Focus Tags |
|------|--------------|--------|------------|
| iron-man | avengers-council:iron-man | Architecture & Scalability | architecture, scalability, distributed-systems, infrastructure-costs |
| thor | avengers-council:thor | Backend & API | backend, api, database, microservices, caching |
| scarlet-witch | avengers-council:scarlet-witch | Frontend & UX | frontend, react, ux, accessibility, design-systems |
| hulk | avengers-council:hulk | Testing & QA | testing, qa, reliability, edge-cases, coverage |
| black-widow | avengers-council:black-widow | Security & Privacy | security, privacy, auth, compliance, threat-modeling |
| hawkeye | avengers-council:hawkeye | Mobile Platforms | mobile, android, ios, flutter, react-native |
| vision | avengers-council:vision | Data & Observability | data, monitoring, logging, metrics, alerting, etl |
| doctor-strange | avengers-council:doctor-strange | DevOps & Infrastructure | devops, cicd, deployment, containers, infrastructure-as-code |

**Captain America** (orchestrator) is always the session model — never spawned as a teammate. See `agents/captain-america.md`.

## Optional Members (topic-activated)

Optional members join the council when the review topic matches their invocation criteria. They are spawned alongside core members and participate in all debate rounds with full voting rights.

When optional members are active, the majority threshold adjusts automatically:
- **Formula**: majority = floor(N / 2) + 1, where N = total active voters (core + optional + Captain America)
- **Example**: 8 core + 1 optional + Cap = 10 voters → majority = 6

<!-- 
To add a new optional member:
1. Create an agent file in agents/ with frontmatter including `optional: true`
2. Add a row to the table below
3. That's it — the orchestration protocol picks it up automatically

Template for optional agent frontmatter:
---
name: member-name
description: One-line expertise summary
tools: Read, Glob, Grep
model: sonnet
optional: true
invoke_when: "Short description of when to invoke this member"
---
-->

| Name | subagent_type | Domain | Invoke When | Focus Tags |
|------|--------------|--------|-------------|------------|
| *(none yet)* | — | — | — | — |

## Quick Mode Member Selection

Quick Mode picks 2 relevant core members + Captain America = 3 voters. Optional members are NOT included in Quick Mode (cost control).

### Focus-to-Member Routing

| Focus | Members |
|-------|---------|
| security | black-widow + thor |
| mobile | hawkeye + doctor-strange |
| architecture | iron-man + doctor-strange |
| testing | hulk + iron-man |
| delivery | doctor-strange + hulk |
| frontend | scarlet-witch + thor |
| backend | thor + vision |
| devops | doctor-strange + iron-man |
| data | vision + thor |
| (auto) | Analyze topic, pick 2 most relevant |

### Code Review Auto-Selection (by affected files)

| Affected Area | Members |
|--------------|---------|
| API routes | thor + black-widow |
| UI components | scarlet-witch + hulk |
| Infrastructure/CI | doctor-strange + iron-man |
| Mobile code | hawkeye + doctor-strange |
| Data/models | vision + thor |
| Mixed | iron-man + hulk |

## How to Add a New Optional Member

1. **Create the agent file** at `agents/{name}.md` using this frontmatter:
   ```yaml
   ---
   name: member-name
   description: "One-line expertise summary"
   tools: Read, Glob, Grep
   model: sonnet
   optional: true
   invoke_when: "When the topic involves X, Y, or Z"
   ---
   ```

2. **Write the agent body** following the existing agent pattern:
   - Core Identity section (character, philosophy, signature phrase)
   - Expertise list
   - Planning Mode Checklist
   - Code Review Checklist
   - Debate Protocol (copy the standard 3-round block from any core member)
   - Debate Behavior (who they challenge, who they support)
   - Red Lines (add corresponding section to `references/red-lines.md`)
   - Communication Style

3. **Add a row** to the Optional Members table above with:
   - Name, subagent_type (`avengers-council:{name}`), Domain, Invoke When criteria, Focus Tags

4. **Optionally add Quick Mode routing** — if this member should be selectable in Quick Mode, add entries to the Focus-to-Member or Code Review Auto-Selection tables above.

5. **No other changes needed** — the orchestration protocol reads this registry and handles spawning, quorum adjustment, and verdict formatting automatically.
