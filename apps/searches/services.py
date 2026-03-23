import logging
from collections.abc import Iterable
from datetime import timedelta
from hashlib import sha256

from django.db import transaction
from django.utils import timezone

from apps.notifications.tasks import send_price_change_notification
from apps.providers.adapters.base import FareOption, SearchQuery
from apps.providers.services import get_active_providers, load_adapter

from .models import FareSnapshot, PriceChangeEvent, SearchSubscription

logger = logging.getLogger(__name__)


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
            try:
                adapter = load_adapter(provider)
                fares = adapter.search(query)
            except Exception:
                logger.exception(
                    "Provider polling failed for subscription=%s provider=%s",
                    subscription.pk,
                    provider.code,
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
            content_hash = sha256(
                f"{provider.id}|{fare.outbound_date}|{fare.return_date}|{fare.amount}|{fare.fare_name}".encode()
            ).hexdigest()
            latest = (
                FareSnapshot.objects.filter(
                    subscription=subscription,
                    provider=provider,
                    outbound_date=fare.outbound_date,
                    return_date=fare.return_date,
                    fare_name=fare.fare_name,
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
        for event_id in event_ids:
            send_price_change_notification.delay(event_id)
