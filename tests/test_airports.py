from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.airports.models import Airport
from apps.searches.forms import SearchSubscriptionForm


def test_airport_seed_contains_expected_records(db):
    assert Airport.objects.filter(iata_code="CGN", city_name="Cologne").exists()
    assert Airport.objects.filter(iata_code="BLQ", city_name="Bologna").exists()


def test_search_subscription_form_resolves_city_names_to_iata_codes(db):
    form = SearchSubscriptionForm(
        data={
            "origin": "Cologne",
            "destination": "Bologna",
            "date_from": date(2026, 4, 13),
            "date_to": date(2026, 4, 24),
            "notify_via": "email",
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["origin"] == "CGN"
    assert form.cleaned_data["destination"] == "BLQ"


def test_airport_suggestions_endpoint_returns_prefix_matches(client, db):
    response = client.get(reverse("airports:suggestions"), {"q": "Col"})

    assert response.status_code == 200
    payload = response.json()
    labels = [item["label"] for item in payload["results"]]

    assert any("Cologne" in label and "CGN" in label for label in labels)


def test_dashboard_post_persists_iata_codes_from_human_labels(client, db):
    user = get_user_model().objects.create_user(
        username="airport-user",
        email="airport@example.com",
        password="StrongPass123!",
        is_approved=True,
    )
    client.force_login(user)

    response = client.post(
        reverse("dashboard:home"),
        data={
            "origin": "Cologne - Cologne Bonn Airport (CGN)",
            "destination": "Bologna - Bologna Guglielmo Marconi Airport (BLQ)",
            "date_from": "2026-04-13",
            "date_to": "2026-04-24",
            "notify_via": "email",
        },
    )

    assert response.status_code == 302
    subscription = user.subscriptions.get()
    assert subscription.origin == "CGN"
    assert subscription.destination == "BLQ"
