# CI/CD & Infrastructure Reference — Read on demand when relevant

## When to use

Read this reference when the review involves CI/CD pipelines, Dockerfile/container builds, Kubernetes/Helm manifests, deployment strategies (blue-green, canary), IaC (Terraform, CloudFormation), or release automation. Use to cite platform-specific patterns in findings. Skip for pure code/logic reviews with no infra surface.

## CI/CD Platform & Infrastructure Detection

**Detect deployment infrastructure:**

```bash
# CI/CD platforms
test -d .github/workflows && echo "✓ GitHub Actions"
test -f .gitlab-ci.yml && echo "✓ GitLab CI"
test -f .circleci/config.yml && echo "✓ CircleCI"
test -f azure-pipelines.yml && echo "✓ Azure Pipelines"
test -f .travis.yml && echo "✓ Travis CI"

# Container platforms
test -f Dockerfile && echo "✓ Docker"
test -f docker-compose.yml && echo "✓ Docker Compose"
test -d .docker && echo "✓ Docker configurations"

# Orchestration
test -d k8s && echo "✓ Kubernetes manifests"
test -d helm && echo "✓ Helm charts"
test -f skaffold.yaml && echo "✓ Skaffold"

# Deployment platforms
test -f vercel.json && echo "✓ Vercel"
test -d .aws && echo "✓ AWS configurations"
test -f cloudbuild.yaml && echo "✓ Google Cloud Build"
test -f .platform.app.yaml && echo "✓ Platform.sh"
test -f fly.toml && echo "✓ Fly.io"
```

## Platform-Specific Recommendations

### GitHub Actions

**Best practices to check:**
- **Caching**: `actions/cache@v3` for dependencies, build artifacts
- **Matrix testing**: Test across Node versions, OS (ubuntu, macos, windows)
- **Secrets management**: Use encrypted secrets, not plaintext in workflow files
- **Security**: Pin action versions to SHA (not @v2 - can be hijacked)
- **Concurrency**: Cancel in-progress runs for same PR

**Example finding:**
```
⚠️ MEDIUM: GitHub Actions has no dependency caching
Current: npm install takes 2m 30s on every run
Recommendation: Add actions/cache@v3 with key: ${{ hashFiles('package-lock.json') }}
Impact: Reduce CI time from 5min to 1.5min (save 3.5min per run)
```

**Security finding:**
```
❌ HIGH: Actions pinned to @v2 instead of commit SHA
Risk: Action maintainer could push malicious code to @v2 tag
Recommendation: Pin to SHA: actions/checkout@a81bbbf8298c0fa03ea29cdc473d45769f953675
Reference: GitHub Actions security hardening guide
```

### Docker

**Best practices:**
- Multi-stage builds (reduce image size)
- Non-root user (security)
- .dockerignore (exclude unnecessary files)
- Layer caching optimization (COPY package.json before source)
- Scan for vulnerabilities (trivy, grype)

**Example finding:**
```
❌ MEDIUM: Dockerfile runs as root user
Risk: Container escape gives root access to host
Recommendation: Add USER directive with non-privileged user
```

### Kubernetes

**Resource limits:**
```
❌ HIGH: No resource limits defined in deployment.yaml
Risk: Single pod can consume entire node resources
Recommendation: Add resources.limits (CPU: 500m, memory: 512Mi) and requests
```

**Health checks:**
```
⚠️ MEDIUM: Missing readinessProbe
Impact: Traffic routed to pod before app is ready
Recommendation: Add HTTP probe on /health endpoint
```

**Deployment strategy:**
- Rolling update: maxSurge, maxUnavailable
- Horizontal pod autoscaling (HPA) based on CPU/memory
- Pod disruption budgets (PDB) for availability

## Infrastructure as Code

**Detect IaC tools:**
```bash
test -d terraform && echo "✓ Terraform"
test -f pulumi.yaml && echo "✓ Pulumi"
test -d .aws-sam && echo "✓ AWS SAM"
test -f serverless.yml && echo "✓ Serverless Framework"
```

**Best practices:**
- State management (remote backend, locking)
- Secrets in state files (use encrypted backends)
- Drift detection (terraform plan in CI)
- Modular organization (separate VPC, compute, data)
