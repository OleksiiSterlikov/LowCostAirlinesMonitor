from django.core.management import call_command

from apps.providers.models import AirlineProvider
from apps.providers.services import sync_default_providers


def test_sync_default_providers_creates_default_records(db):
    created, updated = sync_default_providers()

    provider_codes = set(AirlineProvider.objects.values_list("code", flat=True))

    assert created == 2
    assert updated == 0
    assert provider_codes == {"ryanair", "wizzair"}


def test_sync_default_providers_updates_existing_records(db):
    AirlineProvider.objects.create(
        code="ryanair",
        name="Old Ryanair",
        is_active=False,
        adapter_path="old.path.Adapter",
        website_url="https://old.example.com/",
        config_json={"legacy": True},
    )

    created, updated = sync_default_providers()
    provider = AirlineProvider.objects.get(code="ryanair")

    assert created == 1
    assert updated == 1
    assert provider.name == "Ryanair"
    assert provider.is_active is True
    assert provider.adapter_path == "apps.providers.adapters.ryanair.RyanairAdapter"


def test_sync_airline_providers_management_command(db):
    call_command("sync_airline_providers")

    assert AirlineProvider.objects.filter(code="ryanair").exists()
    assert AirlineProvider.objects.filter(code="wizzair").exists()
