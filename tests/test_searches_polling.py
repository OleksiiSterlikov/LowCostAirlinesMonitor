from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth import get_user_model

from apps.providers.adapters.base import FareOption
from apps.providers.models import AirlineProvider
from apps.searches.models import PriceChangeEvent, SearchSubscription
from apps.searches.services import SearchPollingService
from apps.searches.tasks import poll_active_searches


def test_run_subscription_continues_when_one_provider_fails(monkeypatch, db):
    user = get_user_model().objects.create_user(
        username="polling-user",
        email="polling@example.com",
        password="StrongPass123!",
    )
    subscription = SearchSubscription.objects.create(
        user=user,
        origin="WAW",
        destination="BCN",
        date_from=date(2026, 3, 25),
        date_to=date(2026, 3, 28),
        notify_via="email",
    )
    failing_provider = AirlineProvider.objects.create(
        code="broken",
        name="Broken",
        adapter_path="broken.Adapter",
    )
    healthy_provider = AirlineProvider.objects.create(
        code="healthy",
        name="Healthy",
        adapter_path="healthy.Adapter",
    )
    fare = FareOption(
        provider_code="healthy",
        provider_name="Healthy",
        origin="WAW",
        destination="BCN",
        outbound_date=date(2026, 3, 26),
        return_date=None,
        amount=Decimal("49.99"),
        currency="EUR",
    )

    monkeypatch.setattr(
        "apps.searches.services.get_active_providers",
        lambda: [failing_provider, healthy_provider],
    )

    def fake_load_adapter(provider):
        if provider.code == "broken":
            raise RuntimeError("provider unavailable")
        return SimpleNamespace(search=lambda query: [fare])

    monkeypatch.setattr("apps.searches.services.load_adapter", fake_load_adapter)

    processed = SearchPollingService().run_subscription(subscription)

    assert processed == 1
    assert subscription.snapshots.count() == 1
    assert subscription.price_events.count() == 1


def test_price_change_notifications_are_queued_for_non_initial_changes(
    monkeypatch,
    db,
    django_capture_on_commit_callbacks,
):
    user = get_user_model().objects.create_user(
        username="notify-user",
        email="notify@example.com",
        password="StrongPass123!",
    )
    subscription = SearchSubscription.objects.create(
        user=user,
        origin="BUD",
        destination="FCO",
        date_from=date(2026, 4, 1),
        date_to=date(2026, 4, 8),
        notify_via="email",
    )
    provider = AirlineProvider.objects.create(
        code="ryanair-test",
        name="Ryanair Test",
        adapter_path="apps.providers.adapters.ryanair.RyanairAdapter",
    )
    first_fare = FareOption(
        provider_code="ryanair-test",
        provider_name="Ryanair Test",
        origin="BUD",
        destination="FCO",
        outbound_date=date(2026, 4, 2),
        return_date=None,
        amount=Decimal("51.00"),
        currency="EUR",
    )
    second_fare = FareOption(
        provider_code="ryanair-test",
        provider_name="Ryanair Test",
        origin="BUD",
        destination="FCO",
        outbound_date=date(2026, 4, 2),
        return_date=None,
        amount=Decimal("45.00"),
        currency="EUR",
    )

    delay_mock = Mock()
    monkeypatch.setattr(
        "apps.searches.services.send_price_change_notification.delay",
        delay_mock,
    )

    service = SearchPollingService()
    service._persist_results(subscription, provider, [first_fare])
    with django_capture_on_commit_callbacks(execute=True):
        service._persist_results(subscription, provider, [second_fare])

    event = PriceChangeEvent.objects.filter(is_initial_observation=False).get()

    delay_mock.assert_called_once_with(event.pk)


def test_poll_active_searches_queues_only_active_subscriptions(monkeypatch, db):
    SearchSubscription.objects.all().delete()
    user = get_user_model().objects.create_user(
        username="queue-user",
        email="queue@example.com",
        password="StrongPass123!",
    )
    active_subscription = SearchSubscription.objects.create(
        user=user,
        origin="KRK",
        destination="ATH",
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 9),
        notify_via="email",
        status="active",
    )
    SearchSubscription.objects.create(
        user=user,
        origin="KRK",
        destination="MAD",
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 9),
        notify_via="email",
        status="cancelled",
    )

    delay_mock = Mock()
    monkeypatch.setattr("apps.searches.tasks.poll_subscription.delay", delay_mock)

    queued = poll_active_searches()

    assert queued == 1
    delay_mock.assert_called_once_with(active_subscription.pk)
