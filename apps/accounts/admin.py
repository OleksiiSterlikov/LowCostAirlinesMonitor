from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import RegistrationRequest, User
from .services import RegistrationApprovalError, RegistrationApprovalService


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
    readonly_fields = ("reviewed_by", "review_comment")
    actions = ("approve_requests", "reject_requests")

    @admin.action(description="Approve selected registration requests")
    def approve_requests(self, request, queryset):
        service = RegistrationApprovalService()
        approved_count = 0

        for registration in queryset.order_by("created_at"):
            try:
                user, temporary_password = service.approve(registration, request.user)
            except RegistrationApprovalError as exc:
                self.message_user(
                    request,
                    f"{registration.email}: {exc}",
                    level="ERROR",
                )
                continue

            approved_count += 1
            self.message_user(
                request,
                (
                    f"{registration.email} approved. "
                    f"User: {user.username}. Temporary password: {temporary_password}"
                ),
            )

        if approved_count:
            self.message_user(request, f"Approved {approved_count} registration request(s).")

    @admin.action(description="Reject selected registration requests")
    def reject_requests(self, request, queryset):
        service = RegistrationApprovalService()
        rejected_count = 0

        for registration in queryset.order_by("created_at"):
            try:
                service.reject(registration, request.user)
            except RegistrationApprovalError as exc:
                self.message_user(
                    request,
                    f"{registration.email}: {exc}",
                    level="ERROR",
                )
                continue

            rejected_count += 1

        if rejected_count:
            self.message_user(request, f"Rejected {rejected_count} registration request(s).")
