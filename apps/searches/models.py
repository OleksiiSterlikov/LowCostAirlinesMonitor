from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.providers.models import AirlineProvider


class SearchSubscription(TimeStampedModel):
    NOTIFY_CHOICES = [("email", "Email"), ("telegram", "Telegram")]
    STATUS_CHOICES = [("active", "Active"), ("cancelled", "Cancelled"), ("expired", "Expired")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    origin = models.CharField(max_length=16)
    destination = models.CharField(max_length=16)
    date_from = models.DateField()
    date_to = models.DateField()
    currency = models.CharField(max_length=3, default="EUR")
    notify_via = models.CharField(max_length=20, choices=NOTIFY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.origin}-{self.destination} [{self.user}]"


class FareSnapshot(TimeStampedModel):
    subscription = models.ForeignKey(SearchSubscription, on_delete=models.CASCADE, related_name="snapshots")
    provider = models.ForeignKey(AirlineProvider, on_delete=models.CASCADE, related_name="snapshots")
    outbound_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    fare_name = models.CharField(max_length=50, default="basic")
    price_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    deeplink = models.URLField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    content_hash = models.CharField(max_length=128, blank=True)


class PriceChangeEvent(TimeStampedModel):
    subscription = models.ForeignKey(SearchSubscription, on_delete=models.CASCADE, related_name="price_events")
    provider = models.ForeignKey(AirlineProvider, on_delete=models.CASCADE, related_name="price_events")
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    outbound_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    is_initial_observation = models.BooleanField(default=False)
