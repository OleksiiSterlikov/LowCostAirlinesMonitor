from datetime import timedelta

from django.utils import timezone

from apps.providers.models import AirlineProvider
from apps.providers.services import get_provider_runtime_statuses, provider_is_in_cooldown


def test_provider_is_in_cooldown_clears_expired_value(db):
    provider = AirlineProvider.objects.get(code="wizzair")
    provider.cooldown_until = timezone.now() - timedelta(minutes=1)
    provider.save(update_fields=["cooldown_until", "updated_at"])

    is_in_cooldown = provider_is_in_cooldown(provider)
    provider.refresh_from_db()

    assert is_in_cooldown is False
    assert provider.cooldown_until is None


def test_get_provider_runtime_statuses_clears_expired_cooldowns(db):
    wizzair_provider = AirlineProvider.objects.get(code="wizzair")
    ryanair_provider = AirlineProvider.objects.get(code="ryanair")

    wizzair_provider.cooldown_until = timezone.now() - timedelta(minutes=2)
    ryanair_provider.cooldown_until = timezone.now() + timedelta(minutes=5)
    wizzair_provider.save(update_fields=["cooldown_until", "updated_at"])
    ryanair_provider.save(update_fields=["cooldown_until", "updated_at"])

    statuses = get_provider_runtime_statuses()

    status_by_code = {provider.code: provider for provider in statuses}
    assert status_by_code["wizzair"].cooldown_until is None
    assert status_by_code["ryanair"].cooldown_until is not None
