from collections.abc import Iterable
from hashlib import sha256

from django.db import transaction
from django.utils import timezone

from apps.notifications.services import NotificationDispatcher
from apps.providers.adapters.base import FareOption, SearchQuery
from apps.providers.services import get_active_providers, load_adapter

from .models import FareSnapshot, PriceChangeEvent, SearchSubscription


class SearchPollingService:
    def run_subscription(self, subscription: SearchSubscription) -> int:
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
            adapter = load_adapter(provider)
            fares = adapter.search(query)
            found += self._persist_results(subscription, provider, fares)
        subscription.last_run_at = timezone.now()
        if subscription.date_to < timezone.localdate():
            subscription.status = "expired"
        subscription.save(update_fields=["last_run_at", "status", "updated_at"])
        return found

    @transaction.atomic
    def _persist_results(self, subscription: SearchSubscription, provider, fares: Iterable[FareOption]) -> int:
        count = 0
        dispatcher = NotificationDispatcher()
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
                    dispatcher.send_price_change(event)
            count += 1
        return count
