from django.contrib import admin

from .models import Airport


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("iata_code", "city_name", "airport_name", "country_name", "is_active")
    list_filter = ("country_name", "is_active")
    search_fields = ("iata_code", "city_name", "airport_name", "country_name")
