from django import forms
from django.core.exceptions import ValidationError

from apps.airports.services import AirportCatalogService
from .models import SearchSubscription


class SearchSubscriptionForm(forms.ModelForm):
    origin = forms.CharField(
        label="Звідки",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "list": "origin-suggestions",
                "placeholder": "Наприклад: Cologne або CGN",
                "data-airport-input": "origin",
            }
        ),
    )
    destination = forms.CharField(
        label="Куди",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "list": "destination-suggestions",
                "placeholder": "Наприклад: Bologna або BLQ",
                "data-airport-input": "destination",
            }
        ),
    )

    class Meta:
        model = SearchSubscription
        fields = ["origin", "destination", "date_from", "date_to", "notify_via"]
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.airport_catalog = AirportCatalogService()

    def clean_origin(self) -> str:
        return self._resolve_airport_code("origin")

    def clean_destination(self) -> str:
        return self._resolve_airport_code("destination")

    def _resolve_airport_code(self, field_name: str) -> str:
        raw_value = self.cleaned_data[field_name]
        airport = self.airport_catalog.resolve_query(raw_value)
        if airport is None:
            raise ValidationError(
                "Не вдалося визначити аеропорт. Введи код або обери значення з підказки."
            )
        return airport.iata_code
