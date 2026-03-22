from django.contrib import admin

from .models import FareSnapshot, PriceChangeEvent, SearchSubscription


@admin.register(SearchSubscription)
class SearchSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "origin", "destination", "date_from", "date_to", "notify_via", "status")
    list_filter = ("notify_via", "status")
    search_fields = ("origin", "destination", "user__email", "user__username")


@admin.register(FareSnapshot)
class FareSnapshotAdmin(admin.ModelAdmin):
    list_display = ("subscription", "provider", "outbound_date", "return_date", "price_amount", "currency", "created_at")
    list_filter = ("provider", "currency")


@admin.register(PriceChangeEvent)
class PriceChangeEventAdmin(admin.ModelAdmin):
    list_display = ("subscription", "provider", "old_price", "new_price", "currency", "outbound_date", "created_at")
    list_filter = ("provider", "currency")
