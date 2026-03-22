from django.db import models

from apps.core.models import TimeStampedModel


class AirlineProvider(TimeStampedModel):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    adapter_path = models.CharField(
        max_length=255,
        help_text="Python path to adapter class, e.g. apps.providers.adapters.wizzair.WizzAirAdapter",
    )
    website_url = models.URLField(blank=True)
    config_json = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.name
