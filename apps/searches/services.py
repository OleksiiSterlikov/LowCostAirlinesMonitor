import logging
from collections.abc import Iterable
from datetime import timedelta
from hashlib import sha256
from json import dumps

from django.db import transaction
from django.utils import timezone

from apps.notifications.tasks import send_price_change_notification
from apps.providers.adapters.base import FareOption, SearchQuery
from apps.providers.adapters.wizzair import WizzAirRateLimitError
from apps.providers.services import (
    get_active_providers,
    load_adapter,
    mark_provider_failure,
    mark_provider_success,
    provider_is_in_cooldown,
)

from .models import FareSnapshot, PriceChangeEvent, SearchSubscription

logger = logging.getLogger(__name__)


def _extract_payload_value(payload: dict, path: str):
    current = payload
    for segment in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
        if current is None:
            return None
    return current


def build_fare_identity(subscription: SearchSubscription, provider, fare: FareOption) -> str:
    payload = fare.raw_payload or {}
    provider_config = provider.config_json or {}
    identity_keys = provider_config.get("fare_identity_keys", [])

    identity_parts = [
        provider.code,
        subscription.origin,
        subscription.destination,
        fare.outbound_date.isoformat(),
        fare.return_date.isoformat() if fare.return_date else "",
        fare.fare_name,
        fare.currency,
    ]

    for path in identity_keys:
        value = _extract_payload_value(payload, path)
        if value not in (None, ""):
            identity_parts.append(f"{path}={value}")

    if len(identity_parts) == 7:
        identity_parts.append(f"deeplink={fare.deeplink}")
        identity_parts.append(f"payload={dumps(payload, sort_keys=True, default=str)}")

    return sha256("|".join(str(part) for part in identity_parts).encode()).hexdigest()


class SearchPollingService:
    def run_subscription(self, subscription: SearchSubscription) -> int:
        if subscription.status != "active":
            return 0

        if subscription.date_to < timezone.localdate():
            subscription.status = "expired"
            subscription.last_run_at = timezone.now()
            subscription.next_run_at = None
            subscription.save(update_fields=["status", "last_run_at", "next_run_at", "updated_at"])
            return 0

        query = SearchQuery(
            origin=subscription.origin,
            destination=subscription.destination,
            date_from=subscription.date_from,
            date_to=subscription.date_to,
            currency=subscription.currency,
            passengers=1,
            baggage=False,
        )
        found = 0
        for provider in get_active_providers():
            if provider_is_in_cooldown(provider):
                logger.info(
                    "Skipping provider in cooldown subscription=%s provider=%s cooldown_until=%s",
                    subscription.pk,
                    provider.code,
                    provider.cooldown_until,
                )
                continue
            try:
                adapter = load_adapter(provider)
                fares = adapter.search(query)
                mark_provider_success(provider)
                logger.info(
                    "Provider polling completed for subscription=%s provider=%s fare_count=%s",
                    subscription.pk,
                    provider.code,
                    len(fares),
                )
            except Exception as exc:
                cooldown_minutes = self._get_provider_cooldown_minutes(provider, exc)
                mark_provider_failure(
                    provider,
                    str(exc),
                    cooldown_minutes=cooldown_minutes,
                )
                logger.exception(
                    "Provider polling failed for subscription=%s provider=%s cooldown_minutes=%s",
                    subscription.pk,
                    provider.code,
                    cooldown_minutes,
                )
                continue

            try:
                found += self._persist_results(subscription, provider, fares)
            except Exception:
                logger.exception(
                    "Persisting polling results failed for subscription=%s provider=%s",
                    subscription.pk,
                    provider.code,
                )

        subscription.last_run_at = timezone.now()
        subscription.next_run_at = timezone.now() + timedelta(hours=1)
        subscription.save(update_fields=["last_run_at", "next_run_at", "status", "updated_at"])
        return found

    @transaction.atomic
    def _persist_results(self, subscription: SearchSubscription, provider, fares: Iterable[FareOption]) -> int:
        count = 0
        notification_event_ids: list[int] = []
        for fare in fares:
            payload = fare.raw_payload or {}
            content_hash = build_fare_identity(subscription, provider, fare)
            latest = (
                FareSnapshot.objects.filter(
                    subscription=subscription,
                    provider=provider,
                    content_hash=content_hash,
                )
                .order_by("-created_at")
                .first()
            )
            FareSnapshot.objects.create(
                subscription=subscription,
                provider=provider,
                outbound_date=fare.outbound_date,
                return_date=fare.return_date,
                fare_name=fare.fare_name,
                price_amount=fare.amount,
                currency=fare.currency,
                deeplink=fare.deeplink,
                raw_payload=payload,
                content_hash=content_hash,
            )
            if latest is None or latest.price_amount != fare.amount:
                event = PriceChangeEvent.objects.create(
                    subscription=subscription,
                    provider=provider,
                    old_price=latest.price_amount if latest else None,
                    new_price=fare.amount,
                    currency=fare.currency,
                    outbound_date=fare.outbound_date,
                    return_date=fare.return_date,
                    is_initial_observation=latest is None,
                )
                if latest is not None:
                    notification_event_ids.append(event.pk)
            count += 1

        if notification_event_ids:
            transaction.on_commit(
                lambda event_ids=notification_event_ids: self._queue_price_change_notifications(event_ids)
            )
        return count

    def _queue_price_change_notifications(self, event_ids: list[int]) -> None:
        logger.info("Queueing price change notifications event_count=%s", len(event_ids))
        for event_id in event_ids:
            send_price_change_notification.delay(event_id)

    def _get_provider_cooldown_minutes(self, provider, exc: Exception) -> int | None:
        config = provider.config_json or {}
        if provider.code == "wizzair" and isinstance(exc, WizzAirRateLimitError):
            return int(config.get("rate_limit_cooldown_minutes", 90))
        return int(config.get("cooldown_minutes", 5))
