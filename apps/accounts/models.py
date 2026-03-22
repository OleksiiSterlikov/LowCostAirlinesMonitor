from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    email = models.EmailField(unique=True)
    telegram_chat_id = models.CharField(max_length=64, blank=True)
    must_change_password = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    temporary_password_issued = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class RegistrationRequest(TimeStampedModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telegram_chat_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
    )
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_registrations",
    )
    review_comment = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.email} ({self.status})"
