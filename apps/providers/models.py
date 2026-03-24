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
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    last_error_message = models.CharField(max_length=500, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    cooldown_until = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name
