# Security Policy

## Reporting

Please report vulnerabilities privately to the maintainers. Do not open public issues for sensitive findings.

## Practices implemented

- Invite tokens stored as SHA-256 hashes only
- Webhook secret validation
- JWT-protected admin API
- Redis idempotency for Telegram updates and payments
- Rate limiting for support requests
- Secrets loaded from environment variables only
- Structured logging without secrets or full private message bodies

## Out of scope

This project does not provide hosted infrastructure hardening beyond Docker Compose defaults. For production, place the API behind TLS termination, restrict admin endpoints by network policy, and rotate secrets regularly.
