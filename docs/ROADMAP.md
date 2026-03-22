# ROADMAP.md

## Current state
- The repository is a Django/Celery skeleton with the main bounded contexts already separated.
- The core domain is outlined, but the documentation is still too thin for safe continuation without clarifying workflows and invariants.
- The codebase includes stubs for provider adapters, notifications, and polling orchestration, but it is not yet a production-ready implementation.

## Immediate next steps
1. Clarify and expand domain documentation before changing the model.
2. Add and verify Django migrations for the existing apps.
3. Implement authentication by username or email.
4. Implement the admin approval workflow and temporary-password onboarding flow.
5. Strengthen polling orchestration, provider error isolation, and notification dispatch.
6. Add service-level and integration tests for the critical workflows.
7. Only after that, start implementing real provider adapters.

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
