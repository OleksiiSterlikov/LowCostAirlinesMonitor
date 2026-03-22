from django import forms

from .models import SearchSubscription


class SearchSubscriptionForm(forms.ModelForm):
    class Meta:
        model = SearchSubscription
        fields = ["origin", "destination", "date_from", "date_to", "notify_via"]
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
        }
