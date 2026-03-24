from django.contrib import admin

from .models import AirlineProvider


@admin.register(AirlineProvider)
class AirlineProviderAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "is_active",
        "consecutive_failures",
        "cooldown_until",
        "last_success_at",
        "updated_at",
    )
    search_fields = ("code", "name", "adapter_path", "last_error_message")
    list_filter = ("is_active",)
