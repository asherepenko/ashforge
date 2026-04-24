# Architecture Pattern Library Reference — Read on demand when relevant

## When to use

Read this reference when the review involves service decomposition, microservice boundaries, distributed systems patterns (CQRS, Saga, event sourcing), caching strategies, or resilience patterns (circuit breakers, bulkheads). Use to cite established patterns with authoritative sources. Skip for single-module or UI-only reviews.

**Well-known patterns for authoritative citations in findings:**

## Microservices Patterns

**Service Communication:**
- **Synchronous**: REST, gRPC (tight coupling, cascading failures)
- **Asynchronous**: Message queues, event streams (loose coupling, eventual consistency)
- **Circuit Breaker**: Resilience4j, Hystrix (prevent cascade failures)
- **Service Mesh**: Istio, Linkerd (observability, traffic management, mTLS)

**Example finding:**
```
❌ HIGH: Service calls UserService synchronously without circuit breaker
Risk: UserService downtime cascades to all dependent services
Recommendation: Add Resilience4j circuit breaker with fallback strategy
Reference: Release It! Design Patterns (Michael Nygard) - Stability Anti-patterns
Metrics: 99.9% availability requires circuit breakers between services
```

**Data Patterns:**
- **Database per service**: Isolation, independent scaling (recommended)
- **Shared database**: Simpler, tight coupling (anti-pattern for microservices)
- **Event sourcing**: Audit trail, time travel, replay
- **CQRS**: Separate read/write models (complex, use when needed)
- **Saga pattern**: Distributed transactions with compensation

## Caching Strategies

**Cache patterns:**
- **Cache-aside**: App reads cache, DB on miss, writes cache (most common)
- **Read-through**: Cache fetches from DB automatically on miss
- **Write-through**: Write to cache and DB synchronously (slower writes, consistency)
- **Write-behind**: Write to cache immediately, DB asynchronously (fast, eventual consistency)

**Example finding:**
```
⚠️ HIGH: No caching for getUserProfile() called on every page load
Current: 200ms DB query per request
Recommendation: Add Redis cache-aside with 5-minute TTL
Impact: Reduce latency from 200ms to 2ms, reduce DB load by 95%
```

**Cache invalidation:**
- TTL-based (simple, may serve stale data)
- Event-driven (complex, always fresh)
- Versioned keys (user:123:v2)

## Scalability Patterns

**Horizontal vs Vertical Scaling:**
- Horizontal: Add more servers (distributed system complexity)
- Vertical: Bigger servers (simpler, hardware limits)

**Load Balancing:**
- Round robin (simple, unaware of load)
- Least connections (better for varying request durations)
- Consistent hashing (sticky sessions, cache affinity)

**Database Scaling:**
- Read replicas for read-heavy workloads
- Sharding for write-heavy workloads (horizontal partitioning)
- Vertical partitioning (split tables by access patterns)

**Example finding:**
```
⚠️ MEDIUM: Architecture assumes vertical scaling only
Current limit: 32 cores, 128GB RAM on single instance
Recommendation: Design for horizontal scaling with stateless app servers
Reference: 12-Factor App - Processes (scale out via process model)
```

## Performance Analysis

**Big-O analysis patterns:**
```
❌ CRITICAL: findUsersByName() is O(n) on 10M user table
Current: 8 seconds for search query
Recommendation: Add B-tree index on users.name column
Impact: Reduce to O(log n) - sub-100ms queries
```

**Common complexity issues:**
- N+1 queries: 1 query + N queries in loop
- Cartesian product: JOIN without proper WHERE
- Full table scans: Missing indexes
