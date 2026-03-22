from importlib import import_module

from .models import AirlineProvider


def load_adapter(provider: AirlineProvider):
    module_path, class_name = provider.adapter_path.rsplit('.', 1)
    module = import_module(module_path)
    adapter_cls = getattr(module, class_name)
    return adapter_cls()


def get_active_providers() -> list[AirlineProvider]:
    return list(AirlineProvider.objects.filter(is_active=True).order_by('name'))
