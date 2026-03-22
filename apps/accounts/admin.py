from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import RegistrationRequest, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Application fields",
            {"fields": ("telegram_chat_id", "must_change_password", "is_approved", "temporary_password_issued")},
        ),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_approved", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "telegram_chat_id")


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "status", "created_at")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("status",)
