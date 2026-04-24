# Security Tooling & OWASP Reference — Read on demand when relevant

## When to use

Read this reference when the review involves authentication/authorization, payment processing, PII handling, secrets management, dependency audits, or any OWASP Top 10 concern. Skip when the review is purely UI styling, documentation, or internal tooling with no data exposure.

## Security Tooling Integration

**Detect security scanning infrastructure:**

```bash
# Static Application Security Testing (SAST)
test -f .github/workflows/*sast*.yml && echo "✓ SAST configured in CI"
command -v semgrep &>/dev/null && echo "✓ Semgrep available"
test -f .semgrep.yml && echo "✓ Semgrep rules configured"

# Dependency scanning
test -f .github/dependabot.yml && echo "✓ Dependabot active"
command -v snyk &>/dev/null && echo "✓ Snyk CLI available"
grep -q "npm audit" .github/workflows/*.yml 2>/dev/null && echo "✓ npm audit in CI"

# Secret scanning
test -f .github/workflows/*secret*.yml && echo "✓ Secret scanning active"
test -f .gitleaks.toml && echo "✓ gitleaks configured"
command -v git-secrets &>/dev/null && echo "✓ git-secrets available"

# Security headers
grep -q "helmet\|cors\|csp" package.json 2>/dev/null && echo "✓ Security middleware detected"
```

## Recommend Security Scans in Findings

**If SAST tools available:**
```bash
# Run Semgrep with security rules
semgrep --config=auto --config=p/security-audit .

# Check specific frameworks
semgrep --config=p/owasp-top-ten .
semgrep --config=p/react .
```

**If dependency scanning available:**
```bash
# Check for known vulnerabilities
npm audit --audit-level=moderate
snyk test --severity-threshold=high
pip-audit  # Python
```

**If secret scanning available:**
```bash
# Scan for exposed secrets
git secrets --scan
gitleaks detect --source=.
```

## Enhanced Finding Format

**Reference scan results in findings:**

```
❌ CRITICAL: Hardcoded AWS credentials in config/aws.ts:12
Detected by: Manual review (git-secrets would have caught this)
Recommendation:
1. Remove credentials from code immediately
2. Move to AWS Secrets Manager or environment variables
3. Add git-secrets pre-commit hook to prevent future commits
4. Rotate compromised credentials
Reference: OWASP A07:2021 - Identification and Authentication Failures
```

**When tools NOT available:**
```
⚠️ HIGH: No SAST configured in CI
Recommendation: Add Semgrep or similar to .github/workflows/security.yml
Example: semgrep --config=auto prevents 80% of common vulnerabilities
```

## OWASP Top 10 (2021) Quick Reference

**For citation in findings:**

| ID | Vulnerability | Common Instances |
|----|---------------|------------------|
| A01 | Broken Access Control | IDOR, missing authorization, privilege escalation |
| A02 | Cryptographic Failures | Weak encryption, plaintext secrets, insecure key storage |
| A03 | Injection | SQL injection, command injection, NoSQL injection, LDAP |
| A04 | Insecure Design | Missing threat modeling, insecure patterns |
| A05 | Security Misconfiguration | Default credentials, unnecessary features, verbose errors |
| A06 | Vulnerable Components | Outdated dependencies, known CVEs, supply chain |
| A07 | Auth Failures | Weak passwords, missing MFA, broken session management |
| A08 | Data Integrity Failures | Insecure deserialization, untrusted data acceptance |
| A09 | Security Logging Failures | Missing audit logs, log injection, insufficient monitoring |
| A10 | SSRF | Server-side request forgery, internal service access |

**Use in findings:**
```
❌ CRITICAL: SQL injection vulnerability (UserRepository.ts:45)
Reference: OWASP A03:2021 - Injection
Severity: CRITICAL (enables data theft, modification, deletion)
```
