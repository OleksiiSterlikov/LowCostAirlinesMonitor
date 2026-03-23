import re

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string

from .models import RegistrationRequest


class RegistrationApprovalError(ValueError):
    pass


class RegistrationApprovalService:
    @transaction.atomic
    def approve(self, registration: RegistrationRequest, reviewer) -> tuple[object, str]:
        if registration.status != "pending":
            raise RegistrationApprovalError("Only pending registration requests can be approved.")

        user_model = get_user_model()
        temporary_password = self._generate_temporary_password()
        existing_user = user_model.objects.filter(email__iexact=registration.email).first()

        if existing_user is None:
            user = user_model.objects.create_user(
                username=self._build_username(user_model, registration.email),
                email=registration.email,
                first_name=registration.first_name,
                last_name=registration.last_name,
                telegram_chat_id=registration.telegram_chat_id,
                is_active=True,
                is_approved=True,
                must_change_password=True,
                temporary_password_issued=True,
            )
        else:
            if existing_user.is_approved:
                raise RegistrationApprovalError("A user with this email is already approved.")

            user = existing_user
            user.first_name = registration.first_name
            user.last_name = registration.last_name
            user.telegram_chat_id = registration.telegram_chat_id
            user.is_active = True
            user.is_approved = True
            user.must_change_password = True
            user.temporary_password_issued = True

        user.set_password(temporary_password)
        user.save()

        registration.status = "approved"
        registration.reviewed_by = reviewer
        registration.review_comment = "Approved by administrator."
        registration.save(update_fields=["status", "reviewed_by", "review_comment", "updated_at"])
        return user, temporary_password

    @transaction.atomic
    def reject(self, registration: RegistrationRequest, reviewer, reason: str = "") -> None:
        if registration.status != "pending":
            raise RegistrationApprovalError("Only pending registration requests can be rejected.")

        registration.status = "rejected"
        registration.reviewed_by = reviewer
        registration.review_comment = reason or "Rejected by administrator."
        registration.save(update_fields=["status", "reviewed_by", "review_comment", "updated_at"])

    def _build_username(self, user_model, email: str) -> str:
        base_username = email.split("@", 1)[0].lower()
        base_username = re.sub(r"[^a-z0-9._+-]+", "-", base_username).strip("-") or "user"
        candidate = base_username
        suffix = 1

        while user_model.objects.filter(username=candidate).exists():
            suffix += 1
            candidate = f"{base_username}-{suffix}"

        return candidate

    def _generate_temporary_password(self) -> str:
        alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return get_random_string(12, alphabet)
