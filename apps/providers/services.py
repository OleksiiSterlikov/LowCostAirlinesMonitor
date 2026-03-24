from importlib import import_module

from .bootstrap import DEFAULT_PROVIDER_DEFINITIONS
from .models import AirlineProvider


def load_adapter(provider: AirlineProvider):
    module_path, class_name = provider.adapter_path.rsplit('.', 1)
    module = import_module(module_path)
    adapter_cls = getattr(module, class_name)
    try:
        return adapter_cls(provider=provider)
    except TypeError:
        return adapter_cls()


def get_active_providers() -> list[AirlineProvider]:
    return list(AirlineProvider.objects.filter(is_active=True).order_by('name'))


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

    return created_count, updated_count
