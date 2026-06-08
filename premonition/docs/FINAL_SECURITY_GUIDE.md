# PREMONITION — Final Security Guide

## Authentication

1. **JWT Bearer** — primary for web/mobile (`Authorization: Bearer <token>`)
2. **Managed API Keys** — service-to-service (`X-API-Key`)
3. **Dev mode** — disabled auth when no JWT secret configured

## RBAC

### Platform Roles
| Role | Key Permissions |
|------|-----------------|
| admin | Full access + tenant management |
| clinician | predict, explain, copilot, realtime |
| executive | analytics, executive copilot |
| auditor | read-only audit and metrics |

### Tenant Roles (hierarchy)
`platform_admin > org_admin > hospital_admin > department_head > clinician > executive > auditor > viewer`

## Tenant Isolation

- Row-level security: every record stamped with `tenant_id`
- Cross-tenant access raises `TenantIsolationError`
- Isolated directories: `logs/tenants/{tenant_id}/{audit,copilot,models,...}`

## API Security

- CSRF protection on mutating requests
- Rate limiting middleware
- OWASP security headers (CSP, X-Frame-Options, etc.)
- WAF rules in cloud deployment (rate limit 2000 req/min/IP)

## AI Security

- Every copilot response audited with actor, prompt version, citations
- Retrieval trace logged for compliance
- Mock LLM default — no external data leakage

## Production Checklist

- [ ] Set strong `PREMONITION_JWT_SECRET` (32+ chars)
- [ ] Disable dev mode (configure JWT secret)
- [ ] Enable HTTPS/TLS termination
- [ ] Configure CORS to specific origins
- [ ] Rotate API keys quarterly
- [ ] Enable WAF in cloud deployment
- [ ] Review tenant billing limits
