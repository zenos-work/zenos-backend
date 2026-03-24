# SR-024 Social Media Integration Plan

| SR | Feature | Status | Progress |
|---|---|---|---|
| SR-024 | Webhooks and external integrations | ⏳ Planned | Not started |

## Objective

Define MVP3-ready integration steps for outbound and inbound integrations with LinkedIn, X, and Facebook without implementing code yet.

## Scope Boundaries

- This document is planning only.
- No API keys, app setup secrets, or production code changes are included here.
- Integration sequence covers architecture, compliance, rollout, and observability.

## Delivery Steps

1. Product and policy definition
- Finalize what is being integrated first: share-on-publish, social preview validation, inbound webhooks, or all three.
- Define allowed audience and role permissions for each integration action.
- Define content policy guardrails for outbound posting (draft state restrictions, moderation constraints, legal constraints).

2. Platform app registration and credentials
- Create platform apps in LinkedIn Developer Portal, X Developer Portal, and Meta for Developers.
- Register callback URLs for OAuth and webhook endpoints per environment (dev/staging/prod).
- Request required scopes/permissions only for MVP3 to minimize review risk.
- Store credentials in environment secrets and define rotation policy.

3. Unified integration domain model
- Define provider-agnostic entities:
  - `integration_connections` (per user/org provider connection)
  - `integration_webhook_events` (raw payload + signature status)
  - `integration_dispatch_jobs` (outbound publish/retry queue)
- Define provider state machine:
  - `CONNECTED`, `TOKEN_EXPIRED`, `REVOKED`, `DISABLED`, `ERROR`.

4. OAuth connection flows
- Implement connect/disconnect flows per provider.
- Implement secure token storage and refresh token logic where supported.
- Implement consent/state validation and anti-CSRF protection.
- Add account-level constraints (one account vs multiple accounts/pages).

5. Outbound publishing pipeline
- Define outbound message builder from article metadata:
  - title, canonical URL, summary, optional image.
- Add channel-specific formatter/adapters for LinkedIn, X, Facebook constraints.
- Implement dispatch job queue with retry/backoff and dead-letter handling.
- Add idempotency keys so duplicate posts are prevented.

6. Inbound webhooks pipeline
- Create provider webhook endpoints and verify signatures:
  - LinkedIn webhook verification/signing approach
  - X webhook auth/signature approach
  - Meta webhook verify token + signature headers
- Persist raw webhook payloads before processing.
- Normalize events into a common internal event contract.
- Handle deduplication by provider event ID.

7. Security and compliance controls
- Enforce strict signature validation on all webhook endpoints.
- Encrypt tokens at rest and redact in logs.
- Add request throttling and abuse controls on integration endpoints.
- Define user-initiated revoke and data deletion flows.

8. Operational monitoring and alerting
- Add metrics:
  - outbound success/failure by provider
  - webhook verification failures
  - token refresh failures
  - retry queue depth and age
- Add dashboards and alerts for sustained delivery failures.
- Add audit logs for connect/disconnect, publish attempts, and webhook processing results.

9. QA and sandbox validation
- Build provider sandbox test matrix:
  - OAuth connect/disconnect
  - publish success/failure paths
  - webhook signature success/failure
  - token expiry/refresh scenarios
- Run staged load test for burst webhook ingestion.
- Run failure-injection tests for downstream provider outages.

10. Progressive rollout strategy
- Phase 1: internal users only.
- Phase 2: selected beta users with feature flags.
- Phase 3: general availability once error budget remains stable.
- Define rollback plan by provider and by feature flag.

## Recommended MVP3 Sequence

1. LinkedIn outbound publishing + OAuth (lowest surface complexity)
2. X outbound publishing + OAuth
3. Facebook Page publishing + OAuth
4. Inbound webhooks across all three providers
5. Cross-provider analytics, retries, and governance hardening

## Acceptance Criteria (Planning Level)

- A complete architecture/design doc is approved.
- Security review signs off on token/webhook handling.
- Sandbox integration tests pass for all three providers.
- Observability dashboards and alerts are in place before GA.
- Feature flags enable provider-by-provider progressive rollout.
