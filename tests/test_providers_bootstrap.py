from django.core.management import call_command

from apps.providers.models import AirlineProvider
from apps.providers.services import sync_default_providers


def test_sync_default_providers_is_idempotent_with_seeded_records(db):
    created, updated = sync_default_providers()

    provider_codes = set(AirlineProvider.objects.values_list("code", flat=True))

    assert created == 0
    assert updated == 2
    assert provider_codes == {"ryanair", "wizzair"}


def test_sync_default_providers_updates_existing_records(db):
    provider = AirlineProvider.objects.get(code="ryanair")
    provider.name = "Old Ryanair"
    provider.is_active = False
    provider.adapter_path = "old.path.Adapter"
    provider.website_url = "https://old.example.com/"
    provider.config_json = {"legacy": True}
    provider.save()

    created, updated = sync_default_providers()
    provider = AirlineProvider.objects.get(code="ryanair")

    assert created == 0
    assert updated == 2
    assert provider.name == "Ryanair"
    assert provider.is_active is True
    assert provider.adapter_path == "apps.providers.adapters.ryanair.RyanairAdapter"
    assert provider.config_json["fare_identity_keys"] == [
        "outbound.flightKey",
        "outbound.departureDate",
    ]


def test_sync_airline_providers_management_command(db):
    call_command("sync_airline_providers")

    assert AirlineProvider.objects.filter(code="ryanair").exists()
    assert AirlineProvider.objects.filter(code="wizzair").exists()
