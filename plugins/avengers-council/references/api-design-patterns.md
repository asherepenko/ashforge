# API Design Standards & Patterns Reference — Read on demand when relevant

## When to use

Read this reference when the review involves REST/GraphQL/gRPC contracts, HTTP semantics, pagination, versioning, or API error conventions. Use to cite authoritative standards (RFC 7231, RFC 5988, etc.) in findings. Skip for reviews with no API surface.

**Reference established API standards for authoritative findings:**

## RESTful API Standards

**HTTP Method Semantics (RFC 7231):**
- **GET**: Safe, idempotent, cacheable (retrieve resources)
- **POST**: Non-idempotent (create resources, actions)
- **PUT**: Idempotent (replace entire resource)
- **PATCH**: Idempotent (partial update)
- **DELETE**: Idempotent (remove resource)

**HTTP Status Codes:**
- **2xx Success**: 200 OK, 201 Created, 204 No Content
- **4xx Client Error**: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity
- **5xx Server Error**: 500 Internal Server Error, 503 Service Unavailable

**Example finding:**
```
❌ HIGH: GET /users/delete/{id} violates HTTP semantics
Issue: GET is safe method, should not have side effects (delete)
Recommendation: Use DELETE /users/{id}
Reference: RFC 7231 Section 4.2.1 - Safe Methods
```

**Pagination Patterns:**
- **Cursor-based**: Better for real-time data, stable under inserts
- **Offset-based**: Simpler but skips/duplicates with concurrent changes
- **Link headers**: RFC 5988 for rel="next", rel="prev"

**Versioning Strategies:**
- URI versioning: `/v1/users` (simple, explicit)
- Header versioning: `Accept: application/vnd.api+json;version=1` (cleaner URLs)
- Content negotiation: `Accept: application/vnd.api.v2+json`

## GraphQL Standards

**N+1 Query Detection:**
```
❌ HIGH: Resolver fetches users individually in loop (N+1 query)
Recommendation: Use DataLoader for batching
Impact: 1000 users = 1000 DB queries instead of 1
```

**Complexity Limits:**
- Query depth limits (prevent deeply nested queries)
- Query cost analysis (assign costs to fields)
- Timeout enforcement

**Error Handling:**
- Partial failures: return data + errors list
- Error codes: use extensions for structured errors

## gRPC Standards

**Service Design:**
- Unary RPC for simple request-response
- Server streaming for large result sets
- Client streaming for uploads
- Bidirectional streaming for real-time

**Retry Policies:**
- Exponential backoff with jitter
- Deadline propagation across services
- Idempotency keys for retries

## API Contract Testing

**Recommend contract testing:**
```
⚠️ MEDIUM: No contract tests between frontend and backend
Recommendation: Add Pact or OpenAPI schema validation
Prevents: Breaking changes shipping to production
```
