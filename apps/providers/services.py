import logging
from importlib import import_module
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .bootstrap import DEFAULT_PROVIDER_DEFINITIONS
from .models import AirlineProvider

logger = logging.getLogger(__name__)


def load_adapter(provider: AirlineProvider):
    module_path, class_name = provider.adapter_path.rsplit('.', 1)
    module = import_module(module_path)
    adapter_cls = getattr(module, class_name)
    logger.info("Loading provider adapter provider=%s adapter=%s", provider.code, provider.adapter_path)
    try:
        return adapter_cls(provider=provider)
    except TypeError:
        return adapter_cls()


def get_active_providers() -> list[AirlineProvider]:
    return list(AirlineProvider.objects.filter(is_active=True).order_by('name'))


def provider_is_in_cooldown(provider: AirlineProvider) -> bool:
    if not provider.cooldown_until:
        return False

    now = timezone.now()
    if provider.cooldown_until > now:
        return True

    # Cooldown expired: normalize runtime state so UI does not show stale values.
    provider.cooldown_until = None
    provider.save(update_fields=["cooldown_until", "updated_at"])
    return False


def claim_provider_poll_slot(
    provider: AirlineProvider,
    *,
    force: bool = False,
) -> tuple[bool, int | None]:
    now = timezone.now()

    if force:
        provider.last_polled_at = now
        provider.save(update_fields=["last_polled_at", "updated_at"])
        return True, None

    config = provider.config_json or {}
    min_interval_seconds = int(config.get("min_poll_interval_seconds", 0))

    if min_interval_seconds <= 0:
        provider.last_polled_at = now
        provider.save(update_fields=["last_polled_at", "updated_at"])
        return True, None

    threshold = now - timedelta(seconds=min_interval_seconds)
    updated_rows = (
        AirlineProvider.objects
        .filter(pk=provider.pk)
        .filter(Q(last_polled_at__isnull=True) | Q(last_polled_at__lte=threshold))
        .update(last_polled_at=now, updated_at=now)
    )

    if updated_rows:
        provider.last_polled_at = now
        return True, None

    provider.refresh_from_db(fields=["last_polled_at"])
    if provider.last_polled_at is None:
        return False, min_interval_seconds

    next_allowed_at = provider.last_polled_at + timedelta(seconds=min_interval_seconds)
    retry_after_seconds = max(1, int((next_allowed_at - now).total_seconds()))
    return False, retry_after_seconds


def mark_provider_success(provider: AirlineProvider) -> None:
    provider.last_success_at = timezone.now()
    provider.last_error_message = ""
    provider.consecutive_failures = 0
    provider.cooldown_until = None
    provider.save(
        update_fields=[
            "last_success_at",
            "last_error_message",
            "consecutive_failures",
            "cooldown_until",
            "updated_at",
        ]
    )


def mark_provider_failure(
    provider: AirlineProvider,
    error_message: str,
    *,
    cooldown_minutes: int | None = None,
) -> None:
    now = timezone.now()
    provider.last_failure_at = now
    provider.last_error_message = error_message[:500]
    provider.consecutive_failures += 1
    if cooldown_minutes:
        # Keep existing cooldown window to avoid creating a sliding lockout when
        # repeated manual checks fail while the provider is already throttled.
        if not provider.cooldown_until or provider.cooldown_until <= now:
            provider.cooldown_until = now + timedelta(minutes=cooldown_minutes)
    provider.save(
        update_fields=[
            "last_failure_at",
            "last_error_message",
            "consecutive_failures",
            "cooldown_until",
            "updated_at",
        ]
    )


def get_provider_runtime_statuses() -> list[AirlineProvider]:
    providers = list(AirlineProvider.objects.filter(is_active=True).order_by("name"))
    now = timezone.now()
    expired_provider_ids = [
        provider.pk
        for provider in providers
        if provider.cooldown_until and provider.cooldown_until <= now
    ]

    if expired_provider_ids:
        AirlineProvider.objects.filter(pk__in=expired_provider_ids).update(
            cooldown_until=None,
            updated_at=now,
        )
        for provider in providers:
            if provider.pk in expired_provider_ids:
                provider.cooldown_until = None

    return providers


def sync_default_providers() -> tuple[int, int]:
    created_count = 0
    updated_count = 0

    for provider_definition in DEFAULT_PROVIDER_DEFINITIONS:
        provider, created = AirlineProvider.objects.update_or_create(
            code=provider_definition["code"],
            defaults={
                "name": provider_definition["name"],
                "is_active": provider_definition["is_active"],
                "adapter_path": provider_definition["adapter_path"],
                "website_url": provider_definition["website_url"],
                "config_json": provider_definition["config_json"],
            },
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    logger.info(
        "Default provider sync completed created=%s updated=%s",
        created_count,
        updated_count,
    )
    return created_count, updated_count
