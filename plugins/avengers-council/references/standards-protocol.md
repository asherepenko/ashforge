# Standards Detection & Validation Protocol

## Overview

Every Avengers Council review session begins with comprehensive standards detection. Captain America's job is to surface what standards exist in the project and validate whether the plan or code aligns with them.

For detailed examples, see @references/standards-examples.md

## Table of Contents

- [Phase 1 — Discover Project Standards](#phase-1-discover-project-standards) — locate CLAUDE.md files, supporting docs, index conventions
- [Phase 2 — Categorize Standards by Impact](#phase-2-categorize-standards-by-impact) — mandatory / strong guidance / aspirational
- [Phase 3 — Apply Standards During Review](#phase-3-apply-standards-during-review) — plan and code validation checklists
- [Phase 4 — Document Standards Impact in Verdict](#phase-4-document-standards-impact-in-verdict) — compliance status, violations
- [Phase 5 — Determine Verdict Based on Standards](#phase-5-determine-verdict-based-on-standards) — automatic downgrade rules
- [Tips for Council Members](#tips-for-council-members) — how to cite and challenge

## Phase 1: Discover Project Standards

### Locate CLAUDE.md Files (Hierarchy)

Search in this order; stop when found:

1. **Project level**: `./CLAUDE.md` (shared team conventions)
2. **Local level**: `./.claude/CLAUDE.md` (local overrides)
3. **Global level**: `~/.claude/CLAUDE.md` (user's personal preferences)

### Locate Additional Standards Documents

Check for: `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `docs/standards/`, `docs/contributing/`

### Index Standards Found

Create an index of all conventions discovered, covering:
- Naming conventions (files, functions, variables)
- Testing standards (coverage targets, required test types)
- Commit format requirements
- Security/compliance review triggers
- Documentation requirements
- Performance baselines
- Deprecated/restricted technologies

## Phase 2: Categorize Standards by Impact

### Mandatory Standards (MUST comply)

Security/compliance requirements, legal/regulatory mandates, anti-pattern blockers, process requirements tied to tooling or team agreement.

**Violation handling:** Any violation automatically triggers "NEEDS REVISION" minimum

### Strong Guidance (SHOULD comply)

Naming conventions, code style/formatting, testing coverage targets, documentation standards, commit message format.

**Violation handling:** Violations flagged as HIGH severity, don't automatically block approval

### Aspirational Guidance (NICE to have)

Performance optimization tips, architecture patterns, code comment density, refactoring suggestions.

**Violation handling:** Flagged as MEDIUM or LOW, noted for future improvement

## Phase 3: Apply Standards During Review

### For Plans

**Standards Validation Checklist:**
- [ ] Technology choices follow approved stack
- [ ] Naming conventions for new resources consistent
- [ ] Process/workflow follows documented practice
- [ ] Documentation plan includes required updates
- [ ] Testing strategy meets project baseline
- [ ] Security/compliance review required?
- [ ] Performance SLAs stated and achievable?

### For Code

**Standards Validation Checklist:**
- [ ] Naming convention violations?
- [ ] Code style violations?
- [ ] Testing coverage below project baseline?
- [ ] Commit message format violated?
- [ ] Deprecated/discouraged tech patterns used?
- [ ] Documentation not updated?
- [ ] Security-sensitive code without review/audit?

## Phase 4: Document Standards Impact in Verdict

Include in the verdict: applicable standards, compliance status (met/violated/conditional), specific violations with severity, location, and recommendation.

## Phase 5: Determine Verdict Based on Standards

### Automatic Downgrade Rules

1. **CRITICAL mandatory standard violation** → minimum "NEEDS REVISION"
2. **Unmitigated CRITICAL security finding** → minimum "NEEDS REVISION"
3. **Missing required documentation for deployment** → minimum "APPROVED WITH CONDITIONS"

### Standard Compliance Consensus Rules

Apply consensus rules per `verdict-rules.md` (single source of truth), with the automatic downgrade rules above applied first.

## Tips for Council Members

1. **Reference CLAUDE.md by line number** — makes it easy for the user to find context
2. **Distinguish mandatory from guidance** — mandatory violation = HIGH minimum, strong = MEDIUM, aspirational = LOW
3. **Offer a fix** — don't just cite the violation, provide a concrete recommendation
4. **Challenge other members** on standards interpretation — debate the standard's intent
5. **Give Captain America clear signals** — if a violation blocks your approval, say so explicitly
