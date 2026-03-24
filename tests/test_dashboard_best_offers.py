from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.dashboard.services import BestOfferService
from apps.providers.models import AirlineProvider
from apps.searches.models import FareSnapshot, SearchSubscription


def test_best_offer_service_selects_lowest_price_per_window(db):
    FareSnapshot.objects.all().delete()
    user = get_user_model().objects.create_user(
        username="dashboard-user",
        email="dashboard@example.com",
        password="StrongPass123!",
    )
    provider = AirlineProvider.objects.get(code="ryanair")
    subscription = SearchSubscription.objects.create(
        user=user,
        origin="WAW",
        destination="BCN",
        date_from=date(2026, 3, 24),
        date_to=date(2026, 4, 30),
        notify_via="email",
    )

    FareSnapshot.objects.create(
        subscription=subscription,
        provider=provider,
        outbound_date=date(2026, 3, 25),
        fare_name="basic",
        price_amount=Decimal("55.00"),
        currency="EUR",
        content_hash="this-week-a",
    )
    FareSnapshot.objects.create(
        subscription=subscription,
        provider=provider,
        outbound_date=date(2026, 3, 27),
        fare_name="basic",
        price_amount=Decimal("41.00"),
        currency="EUR",
        content_hash="this-week-b",
    )
    FareSnapshot.objects.create(
        subscription=subscription,
        provider=provider,
        outbound_date=date(2026, 3, 31),
        fare_name="basic",
        price_amount=Decimal("49.00"),
        currency="EUR",
        content_hash="next-week-a",
    )
    FareSnapshot.objects.create(
        subscription=subscription,
        provider=provider,
        outbound_date=date(2026, 4, 10),
        fare_name="basic",
        price_amount=Decimal("62.00"),
        currency="EUR",
        content_hash="next-month-a",
    )

    offers = BestOfferService().get_dashboard_offers(reference_date=date(2026, 3, 24))

    assert [offer["slug"] for offer in offers] == ["this_week", "next_week", "next_month"]
    assert offers[0]["snapshot"].price_amount == Decimal("41.00")
    assert offers[1]["snapshot"].price_amount == Decimal("49.00")
    assert offers[2]["snapshot"].price_amount == Decimal("62.00")


def test_best_offer_service_returns_empty_window_when_no_snapshot_exists(db):
    FareSnapshot.objects.all().delete()
    offers = BestOfferService().get_dashboard_offers(reference_date=date(2026, 3, 24))

    assert len(offers) == 3
    assert all(offer["snapshot"] is None for offer in offers)
