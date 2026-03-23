# ROADMAP.md

## Current state
- The repository has moved beyond the initial skeleton stage and now has a stable foundation.
- Core domain and architecture documentation have been expanded and aligned with the codebase.
- Initial migrations, provider bootstrap, username-or-email login, admin approval workflow, and polling hardening are implemented.
- The main remaining gap is real provider integration and operational hardening around production polling.

## Immediate next steps
1. Implement the first real provider adapter with proper mapping, throttling, and tests.
2. Add structured logging and observability around polling, adapters, and notifications.
3. Replace the static dashboard best-offers panel with data derived from persisted fare snapshots.
4. Continue strengthening integration-level tests around polling tasks and notification dispatch.

## Completed foundation
- Expanded `docs/DATA_MODEL.md` and `docs/ARCHITECTURE.md`.
- Added initial Django migrations.
- Added username-or-email authentication.
- Implemented admin approval and rejection workflow for registration requests.
- Added bootstrap and synchronization for default airline providers.
- Hardened polling orchestration with provider isolation and async notification dispatch.

## Documentation work first
- Expand `docs/DATA_MODEL.md` with entity states, lifecycle transitions, and domain invariants.
- Expand `docs/ARCHITECTURE.md` with the provider contract, polling flow, notification flow, and retry boundaries.
- Document how a fare is identified across polling runs for price-change detection.
- Document what is synchronous, what must run in Celery, and what should be retried.

## Foundation work
- Generate migrations for all current apps and verify they apply cleanly.
- Add initial provider records for Wizz Air and Ryanair.
- Align local setup, Docker commands, and developer docs with the real workflow.
- Add a minimal health-check path and basic runbook notes for local development.

## Accounts and access workflow
- Add a custom authentication backend for login by username or email.
- Add admin actions for approving or rejecting registration requests.
- Define how temporary passwords are issued, rotated, and forced to change on first login.
- Add audit-friendly handling for approval actions and user activation state.

## Search and orchestration
- Revisit `SearchSubscription` scheduling fields and define whether `next_run_at` is used or removed.
- Isolate provider failures so one broken adapter does not block polling for other providers.
- Move notification sending behind asynchronous task boundaries where appropriate.
- Add retry/backoff policy and structured logging around polling and integrations.

## Testing priorities
- Unit tests for approval flow and forced password change.
- Unit tests for polling and price-change detection.
- Integration tests for Celery tasks and notification dispatch boundaries.
- Adapter tests per provider, including raw response mapping to `FareOption`.

## Later milestones
- Implement real adapters for Wizz Air and Ryanair with throttling and legal/ToS review.
- Add observability, metrics, and better production hardening.
- Add REST API or richer UI improvements after the core workflows are stable.

## Next implementation block
The next focused block should be:
- one real provider adapter end-to-end
- adapter/service tests for that provider
- structured logging for polling and provider failures
- best-offers dashboard data sourced from real `FareSnapshot` records
