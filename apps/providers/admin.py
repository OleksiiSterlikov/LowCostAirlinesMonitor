from django.contrib import admin

from .models import AirlineProvider


@admin.register(AirlineProvider)
class AirlineProviderAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "adapter_path", "updated_at")
    search_fields = ("code", "name", "adapter_path")
    list_filter = ("is_active",)
