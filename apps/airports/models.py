from django.db import models

from apps.core.models import TimeStampedModel


class Airport(TimeStampedModel):
    iata_code = models.CharField(max_length=3, unique=True)
    city_name = models.CharField(max_length=128)
    airport_name = models.CharField(max_length=255)
    country_name = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["city_name", "airport_name", "iata_code"]

    def save(self, *args, **kwargs):
        self.iata_code = self.iata_code.upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.city_name} ({self.iata_code})"
