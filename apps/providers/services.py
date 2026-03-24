import logging
from importlib import import_module
from datetime import timedelta

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
    return bool(provider.cooldown_until and provider.cooldown_until > timezone.now())


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
    provider.last_failure_at = timezone.now()
    provider.last_error_message = error_message[:500]
    provider.consecutive_failures += 1
    if cooldown_minutes:
        provider.cooldown_until = timezone.now() + timedelta(minutes=cooldown_minutes)
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
    return list(AirlineProvider.objects.filter(is_active=True).order_by("name"))


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
