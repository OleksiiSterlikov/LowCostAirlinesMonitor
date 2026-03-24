# DATA_MODEL.md

## Purpose
This document defines the current domain model, its relationships, and the invariants that must remain stable while the implementation evolves.

The application monitors low-cost airline fares for one passenger without baggage, stores all discovered fare options, and notifies the user when a tracked fare changes price.

## Core entities

### User
Represents an account that can log in to the system and own search subscriptions.

Key attributes:
- `username`
- `email`
- `first_name`
- `last_name`
- `telegram_chat_id`
- `is_active`
- `is_approved`
- `must_change_password`
- `temporary_password_issued`

Rules:
- `email` must be unique.
- A user may exist but still be blocked from normal usage if `is_approved=False`.
- If a temporary password is issued, the user must complete a password change on first login.
- Contact data must support at least email and optional Telegram delivery.

### RegistrationRequest
Represents a self-registration request that must be reviewed by an administrator before it becomes a real user account.

Key attributes:
- `first_name`
- `last_name`
- `email`
- `telegram_chat_id`
- `status`
- `reviewed_by`
- `review_comment`

Allowed statuses:
- `pending`
- `approved`
- `rejected`

Rules:
- `email` must be unique among registration requests.
- Approval does not mean silent auto-login. Approval creates or activates a real `User` through an explicit workflow.
- The review action should be auditable.

Lifecycle:
1. A visitor creates a `RegistrationRequest`.
2. The request starts in `pending`.
3. An admin reviews it.
4. The request becomes `approved` or `rejected`.
5. If approved, the system creates or activates a `User` and issues onboarding credentials.

### AirlineProvider
Represents a provider configuration record stored in the database.

Key attributes:
- `code`
- `name`
- `is_active`
- `adapter_path`
- `website_url`
- `config_json`
- `last_success_at`
- `last_failure_at`
- `last_error_message`
- `consecutive_failures`
- `cooldown_until`

Rules:
- `code` must be unique.
- `adapter_path` must point to an implementation compatible with the provider adapter contract.
- `config_json` stores provider-specific settings, not secrets hardcoded in code.
- Disabling a provider must stop polling that provider without deleting historical fare data.
- Provider runtime health is operational state and may change on each polling cycle.
- `cooldown_until` temporarily suppresses polling for providers that are currently rate-limited or unstable.

### Airport
Represents a searchable airport catalog entry used for route normalization and UI suggestions.

Key attributes:
- `iata_code`
- `city_name`
- `airport_name`
- `country_name`
- `is_active`

Rules:
- `iata_code` must be unique and stored in uppercase.
- A user-facing route input may begin as a city or airport name, but the persisted subscription must store the normalized IATA code.
- The catalog is an operational reference dataset, not user-owned transactional data.
- Autocomplete suggestions and name-to-code resolution must use only active airport records.

### SearchSubscription
Represents a user-owned route and date-window to monitor until cancelled or expired.

Key attributes:
- `user`
- `origin`
- `destination`
- `date_from`
- `date_to`
- `currency`
- `notify_via`
- `status`
- `next_run_at`
- `last_run_at`

Allowed `notify_via` values:
- `email`
- `telegram`

Allowed statuses:
- `active`
- `cancelled`
- `expired`

Rules:
- A subscription belongs to exactly one user.
- Only active subscriptions are polled.
- `date_from` must be less than or equal to `date_to`.
- Currency is currently expected to be `EUR`.
- `origin` and `destination` must be stored as normalized IATA airport codes before provider polling.
- A subscription expires when its date window is no longer relevant for polling.
- A cancelled or expired subscription keeps its historical snapshots and events.

Lifecycle:
1. User creates a subscription.
2. Subscription starts as `active`.
3. Polling runs repeatedly while the subscription is active and within the monitored period.
4. The user may cancel it, which changes status to `cancelled`.
5. The system may mark it `expired` once the monitored period has passed.

### FareSnapshot
Represents one observed fare option returned by one provider during polling.

Key attributes:
- `subscription`
- `provider`
- `outbound_date`
- `return_date`
- `fare_name`
- `price_amount`
- `currency`
- `deeplink`
- `raw_payload`
- `content_hash`
- `created_at`

Rules:
- All prices must be stored as `Decimal`.
- Every fare returned by a provider should be persisted, not only the cheapest one.
- `raw_payload` preserves the raw provider data needed for troubleshooting and mapping review.
- A snapshot is immutable historical data once written.

### PriceChangeEvent
Represents a detected price transition for a tracked fare identity.

Key attributes:
- `subscription`
- `provider`
- `old_price`
- `new_price`
- `currency`
- `outbound_date`
- `return_date`
- `is_initial_observation`
- `created_at`

Rules:
- A price change event is created when the current observed price differs from the previous observed price for the same fare identity.
- The first observation may create an event flagged with `is_initial_observation=True`, but it should not trigger a user notification by default.
- Notifications are sent for actual changes, not for the initial discovery.

## Provider contract objects

### SearchQuery
The normalized input passed from the domain into a provider adapter.

Fields:
- `origin`
- `destination`
- `date_from`
- `date_to`
- `currency`
- `passengers`
- `baggage`

Rules:
- Current scope is one passenger and no baggage.
- `origin` and `destination` must already be normalized to provider-safe airport codes before adapter execution.
- Provider-specific code must adapt from this normalized query instead of leaking provider parameters into views or models.

### FareOption
The normalized output returned by a provider adapter.

Fields:
- `provider_code`
- `provider_name`
- `origin`
- `destination`
- `outbound_date`
- `return_date`
- `amount`
- `currency`
- `fare_name`
- `deeplink`
- `raw_payload`

Rules:
- `amount` must be `Decimal`.
- `currency` should be normalized before persistence.
- `raw_payload` should contain enough original data to debug mapping issues without storing secrets.

## Relationships
- `User` 1:N `SearchSubscription`
- `User` 1:N `RegistrationRequest` as reviewer through `reviewed_by`
- `Airport` is referenced logically by `SearchSubscription.origin` and `SearchSubscription.destination` through normalized IATA codes
- `SearchSubscription` 1:N `FareSnapshot`
- `SearchSubscription` 1:N `PriceChangeEvent`
- `AirlineProvider` 1:N `FareSnapshot`
- `AirlineProvider` 1:N `PriceChangeEvent`

## Fare identity and change detection
Price-change detection depends on identifying when two observations refer to the same fare option.

Current implementation approximates fare identity by:
- provider
- subscription
- outbound date
- return date
- fare name

This is enough for the skeleton, but not necessarily enough for real integrations. Real provider implementations may require a stronger identity key, for example:
- provider-specific fare code
- cabin or bundle identifier
- route and trip structure
- flight numbers or segment identifiers

Decision:
- The domain should compare prices on a stable fare identity, not simply on “latest snapshot from the provider”.
- If a provider can expose a stronger identifier, the domain model should be extended before production rollout.

## Domain invariants
- Prices are stored as `Decimal`, never `float`.
- Timezone is `Europe/Kyiv`.
- Historical snapshots are append-only.
- Polling logic must not live in model methods.
- Provider-specific scraping or API logic must stay behind the adapter abstraction.
- Notifications must be driven by domain events, not by view logic.
- Secrets and tokens must not be stored in code or fixtures.
- User-entered route labels must be normalized against the airport catalog before polling.

## Planned model clarifications
The following areas are intentionally left open and should be refined before implementation hardening:
- whether `RegistrationRequest.email` should also be unique against `User.email`
- whether `next_run_at` becomes a real scheduling field or is removed
- whether `PriceChangeEvent` should reference the exact triggering snapshots
- whether user approval needs separate activation timestamps and audit records
- how broad the airport catalog seed should be and whether it later syncs from an external open dataset
