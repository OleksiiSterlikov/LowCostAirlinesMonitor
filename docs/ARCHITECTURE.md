# ARCHITECTURE.md

## Architecture style
The application is a modular Django monolith with asynchronous orchestration through Celery.

This means:
- Django owns the web UI, admin, auth, and most domain logic wiring.
- MySQL stores transactional and historical domain data.
- Redis is used for Celery broker and result backend.
- Celery workers execute background orchestration.
- Celery beat schedules recurring polling.

The system is intentionally designed as a monolith first so that domain boundaries are clear before introducing more operational complexity.

## High-level components

### Web application
Responsibilities:
- authentication
- registration request flow
- profile management
- dashboard screens
- admin actions
- airport autocomplete for route entry

The web layer should stay thin. It accepts input, delegates to services, and renders responses.

### Domain and service layer
Responsibilities:
- validating domain workflows
- normalizing user-entered route labels into airport codes
- building normalized provider queries
- persisting snapshots
- detecting price changes
- preparing notification triggers

Business rules belong here, not in Django views and not in model methods.

### Provider integration layer
Responsibilities:
- translating `SearchQuery` into provider-specific requests
- handling provider-specific API or scraping mechanics
- mapping provider responses into normalized `FareOption` objects
- applying provider-specific throttling, retry, and error handling

Each airline integration must live behind the `AirlineAdapter` contract.

### Background orchestration
Responsibilities:
- polling active subscriptions
- dispatching provider integration work
- sending notifications
- retrying transient failures

Tasks should orchestrate workflows. They should not absorb business rules that belong in domain services.

## Bounded contexts

### `accounts`
Scope:
- `User`
- `RegistrationRequest`
- approval workflow
- temporary password onboarding
- forced password change

### `providers`
Scope:
- `AirlineProvider`
- adapter loading
- provider configuration
- normalized query/response contract

### `airports`
Scope:
- airport catalog records
- airport search and suggestion services
- route label to IATA normalization

### `searches`
Scope:
- `SearchSubscription`
- `FareSnapshot`
- `PriceChangeEvent`
- polling and price-change detection

### `notifications`
Scope:
- email delivery
- Telegram delivery
- notification composition and dispatch

### `dashboard`
Scope:
- authenticated user UI
- subscription management screens
- fare history views

## Runtime flow

### Registration and approval flow
1. A visitor submits a registration request.
2. The system stores `RegistrationRequest(status='pending')`.
3. An administrator reviews the request.
4. On approval, the system creates or activates a `User`, issues temporary credentials, and marks the request as reviewed.
5. On first login, middleware forces the user to change the temporary password.

### Subscription lifecycle flow
1. An approved user creates a `SearchSubscription`.
2. The input route labels are normalized through the airport catalog into IATA codes.
3. The subscription becomes `active`.
4. Celery beat periodically schedules polling.
5. A worker picks active subscriptions and executes the polling service.
6. The polling service loads active providers and calls their adapters.
7. Returned `FareOption` items are persisted as `FareSnapshot`.
8. The service compares each observation against the previous observation of the same fare identity.
9. When the price changes, the system creates `PriceChangeEvent`.
10. Notification delivery is triggered for non-initial price changes.
11. The subscription remains active until the user cancels it or the monitored period expires.

## Synchronous and asynchronous boundaries

Synchronous by default:
- user-facing form submission
- admin review submission
- basic domain validation
- airport lookup and route normalization
- writing core transactional state

Asynchronous by default:
- periodic polling
- provider network calls
- notification delivery
- retries for transient failures

Rule:
- views should not call provider integrations directly.
- provider integrations should not run inside request-response flows.
- heavy notification or network work should be queued rather than performed inline.

## Provider adapter contract

Every provider integration must implement the same logical contract:
- input: `SearchQuery`
- output: `list[FareOption]`

The adapter layer must guarantee:
- provider isolation
- no leakage of provider-specific objects into the rest of the domain
- normalized monetary values
- predictable error boundaries

Required responsibilities of a real adapter:
- build provider request from normalized input
- map raw provider response to `FareOption`
- apply rate limiting and throttling
- handle retryable failures
- log failures without leaking secrets
- if needed, use provider-specific browser automation fallback behind the same adapter contract rather than leaking browser code into tasks or views

## Polling architecture

### Scheduler
Celery beat triggers the recurring polling entry point on an hourly schedule.

### Polling task
The polling task is responsible for:
- loading active subscriptions
- delegating per-subscription processing to a service
- recording task-level failures

### Polling service
The polling service is responsible for:
- constructing `SearchQuery`
- loading active providers
- invoking adapters
- persisting snapshots
- generating price change events
- updating subscription runtime metadata

### Future hardening direction
Before scaling, the polling path should evolve toward:
- per-provider exception isolation
- retry/backoff for transient integration errors
- optional fan-out into per-subscription or per-provider tasks
- structured logging and metrics

## Failure handling policy

### Provider failures
- One broken provider must not block polling for other providers.
- Transient provider failures should be retried with backoff.
- Permanent mapping or contract failures should be logged and surfaced for investigation.
- Providers may enter a temporary cooldown window after repeated failures or explicit rate-limit responses.
- Provider operational state should be visible in admin and user-facing diagnostics, not hidden behind an empty result set.

### Notification failures
- Notification delivery should be retried independently from price detection.
- A notification failure must not roll back a successfully persisted snapshot or event.

### Data consistency
- Snapshot persistence and event creation should remain transactionally coherent.
- External side effects should happen after durable domain state is recorded or in a separate async step.

## Data storage strategy

MySQL stores:
- users and registration requests
- provider configuration
- subscriptions
- immutable fare snapshots
- price change events

Redis stores:
- Celery broker data
- Celery results if enabled

Storage principles:
- snapshots are append-only historical records
- provider config is data-driven through `AirlineProvider`
- raw payload is stored for traceability and mapping review
- airport catalog data is stored locally to support deterministic normalization and autocomplete

## Extensibility rules
- New providers are added as separate adapters under `apps/providers/adapters/`.
- Provider configuration is stored in the database, not hardcoded in branching logic.
- Domain services work with normalized contracts, not provider-specific DTOs.
- UI code must not contain scraping or integration logic.
- Route normalization logic must rely on the airport catalog service rather than ad-hoc string handling in views.

## Security and operational constraints
- Secrets are loaded from environment variables.
- Provider polling must respect rate limits and legal constraints.
- Logs must not expose passwords, tokens, or session cookies.
- Telegram and email credentials must remain outside the repository.

## Observability direction
The current skeleton has minimal observability. Production hardening should add:
- structured logs around polling and notification workflows
- task-level metrics and error counters
- visibility into provider latency and failure rates
- alerting for repeated polling failures

## Known skeleton limitations
- no migrations yet
- no real provider integrations yet
- no production retry/circuit-breaker policy yet
- no hardened notification delivery yet
- no formal audit trail yet for approval actions
