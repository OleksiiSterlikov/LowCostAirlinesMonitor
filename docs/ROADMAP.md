# ROADMAP.md

## Current state
- The repository has moved beyond the initial skeleton stage and now has a stable foundation.
- Core domain and architecture documentation have been expanded and aligned with the codebase.
- Initial migrations, provider bootstrap, username-or-email login, admin approval workflow, polling hardening, and real adapters for Ryanair and Wizz Air are implemented.
- Structured logging, dashboard best-offers from persisted fare data, and stronger fare identity are now in place.
- The main remaining gap is production-facing hardening around runtime observability, external adapter reliability, and user-facing workflow depth.

## Immediate next steps
1. Add richer observability beyond logs: failure counters, polling run metrics, and operational runbook notes.
2. Strengthen provider-specific configuration for markets, throttling, and anti-bot boundaries without weakening the adapter abstraction.
3. Continue strengthening integration-level tests around polling tasks, notification dispatch, and provider edge cases.
4. Build the next user-visible layer: REST API or richer dashboard interactions around real fare data.

## Completed foundation
- Expanded `docs/DATA_MODEL.md` and `docs/ARCHITECTURE.md`.
- Added initial Django migrations.
- Added username-or-email authentication.
- Implemented admin approval and rejection workflow for registration requests.
- Added bootstrap and synchronization for default airline providers.
- Hardened polling orchestration with provider isolation and async notification dispatch.
- Implemented real provider adapters for Ryanair and Wizz Air.
- Added structured logging for providers, polling, and notifications.
- Replaced the static best-offers dashboard panel with offers derived from persisted `FareSnapshot` data.
- Strengthened fare identity to use provider-specific keys from payloads and provider config.

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
- richer observability and operational diagnostics beyond plain logs
- provider-specific config evolution and safer handling of anti-bot/runtime limits
- deeper integration tests around polling, notifications, and adapter edge cases
- REST API or HTMX/UI enhancements on top of the now-real fare data
