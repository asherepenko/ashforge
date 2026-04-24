# Observability Stack Reference — Read on demand when relevant

## When to use

Read this reference when the review involves logging, metrics, distributed tracing, APM, alerting thresholds, or data pipeline instrumentation. Use to cite stack-specific patterns (Winston/Pino, Prometheus, OpenTelemetry, Sentry, etc.) in findings. Skip for reviews that don't touch observability surface.

## Observability Stack Detection

**Detect monitoring and observability infrastructure:**

```bash
# Logging frameworks
grep -q "winston\|pino\|bunyan" package.json 2>/dev/null && echo "✓ Structured logging (Node.js)"
grep -q "logback\|slf4j\|log4j" build.gradle* 2>/dev/null && echo "✓ Logging (Java/Kotlin)"
grep -q "logging" requirements.txt 2>/dev/null && echo "✓ Python logging"

# Metrics collection
grep -q "prometheus\|statsd\|datadog" package.json 2>/dev/null && echo "✓ Metrics collection"
test -f prometheus.yml && echo "✓ Prometheus configured"

# Distributed tracing
grep -q "opentelemetry\|@opentelemetry" package.json 2>/dev/null && echo "✓ OpenTelemetry"
grep -q "jaeger\|zipkin" package.json 2>/dev/null && echo "✓ Distributed tracing"

# Application Performance Monitoring
grep -q "newrelic\|datadog-apm\|sentry" package.json 2>/dev/null && echo "✓ APM configured"
grep -q "@sentry" package.json 2>/dev/null && echo "✓ Error tracking"

# Database query monitoring
grep -q "pg-query-stream\|sequelize.logging" package.json 2>/dev/null && echo "✓ Query logging"
```

## Stack-Specific Recommendations

### Prometheus (Metrics)

**Naming conventions:**
- Metric names: snake_case (e.g., `http_requests_total`)
- Label names: snake_case (e.g., `status_code`, `endpoint`)
- Counter suffix: `_total` (e.g., `api_errors_total`)
- Gauge: current value (e.g., `queue_depth`)
- Histogram: `_bucket`, `_sum`, `_count` suffixes

**Example finding:**
```
❌ MEDIUM: Metric named `apiRequestCount` violates Prometheus conventions
Recommendation: Use `api_requests_total` (snake_case with _total suffix)
Reference: Prometheus naming best practices
```

**Cardinality checks:**
```
⚠️ HIGH: Metric has unbounded label cardinality (user_id as label)
Issue: 1M users = 1M metric series (memory explosion)
Recommendation: Use aggregated metrics, log individual user events separately
```

### OpenTelemetry (Distributed Tracing)

**Span context propagation:**
- W3C Trace Context headers (traceparent, tracestate)
- Span attributes (http.method, http.status_code, db.statement)
- Span events for significant operations
- Span links for async causality

**Example finding:**
```
❌ HIGH: Service calls don't propagate trace context
Issue: Distributed traces will be fragmented, debugging impossible
Recommendation: Add OpenTelemetry auto-instrumentation or manual context propagation
Reference: OpenTelemetry semantic conventions
```

### Sentry (Error Tracking)

**Best practices:**
- Breadcrumbs for debugging context
- Custom tags for filtering (environment, user_id, feature_flag)
- Release tracking for regression detection
- Source maps for readable stack traces

**Example finding:**
```
⚠️ MEDIUM: Sentry configured but no release tracking
Recommendation: Add `sentry-cli releases new` in deployment pipeline
Benefit: Track which deploy introduced each error
```

## Logging Standards

**Structured logging format:**
```json
{
  "timestamp": "2026-02-13T10:30:00Z",
  "level": "ERROR",
  "message": "Payment processing failed",
  "context": {
    "user_id": "12345",
    "order_id": "67890",
    "amount": 99.99,
    "error_code": "PAYMENT_DECLINED"
  },
  "trace_id": "abc-123-def"
}
```

**Anti-patterns to flag:**
```
❌ MEDIUM: Using console.log instead of structured logging
Recommendation: Use winston/pino with JSON formatter
Benefit: Searchable, parseable logs in production
```

## Database Observability

**Query performance monitoring:**
- Slow query logging (>100ms threshold)
- Query plan analysis (EXPLAIN for N+1 detection)
- Connection pool monitoring (active, idle, waiting)

**Example finding:**
```
❌ HIGH: No slow query logging configured
Recommendation: Enable PostgreSQL log_min_duration_statement = 100
Benefit: Identify performance bottlenecks before they impact users
```
