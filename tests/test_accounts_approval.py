from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse

from apps.accounts.models import RegistrationRequest
from apps.accounts.services import RegistrationApprovalService


def test_approve_registration_request_creates_user_and_marks_password_change(db):
    registration = RegistrationRequest.objects.create(
        first_name="Olena",
        last_name="Traveler",
        email="olena@example.com",
        telegram_chat_id="12345",
    )
    reviewer = get_user_model().objects.create_superuser(
        username="admin-approval-1",
        email="admin-approval-1@example.com",
        password="StrongPass123!",
    )

    user, temporary_password = RegistrationApprovalService().approve(registration, reviewer)

    registration.refresh_from_db()
    user.refresh_from_db()

    assert registration.status == "approved"
    assert registration.reviewed_by == reviewer
    assert user.email == "olena@example.com"
    assert user.is_approved is True
    assert user.must_change_password is True
    assert user.temporary_password_issued is True
    assert user.check_password(temporary_password)


def test_approve_registration_request_updates_existing_unapproved_user(db):
    user_model = get_user_model()
    existing_user = user_model.objects.create_user(
        username="traveler",
        email="traveler@example.com",
        password="StrongPass123!",
        is_active=False,
        is_approved=False,
    )
    registration = RegistrationRequest.objects.create(
        first_name="Taras",
        last_name="Sky",
        email="traveler@example.com",
        telegram_chat_id="tg-77",
    )
    reviewer = user_model.objects.create_superuser(
        username="admin-approval-2",
        email="admin-approval-2@example.com",
        password="StrongPass123!",
    )

    approved_user, temporary_password = RegistrationApprovalService().approve(registration, reviewer)

    registration.refresh_from_db()
    existing_user.refresh_from_db()

    assert approved_user.pk == existing_user.pk
    assert existing_user.first_name == "Taras"
    assert existing_user.telegram_chat_id == "tg-77"
    assert existing_user.is_active is True
    assert existing_user.is_approved is True
    assert existing_user.check_password(temporary_password)
    assert registration.status == "approved"


def test_admin_action_approves_registration_request(admin_client, db):
    registration = RegistrationRequest.objects.create(
        first_name="Iryna",
        last_name="Boarding",
        email="iryna@example.com",
    )

    response = admin_client.post(
        reverse("admin:accounts_registrationrequest_changelist"),
        {
            "action": "approve_requests",
            "_selected_action": [str(registration.pk)],
        },
        follow=True,
    )

    registration.refresh_from_db()
    user = get_user_model().objects.get(email="iryna@example.com")
    messages = [message.message for message in get_messages(response.wsgi_request)]

    assert response.status_code == 200
    assert registration.status == "approved"
    assert user.is_approved is True
    assert any("Temporary password:" in message for message in messages)


def test_admin_action_rejects_registration_request(admin_client, db):
    registration = RegistrationRequest.objects.create(
        first_name="Maksym",
        last_name="Rejected",
        email="maksym@example.com",
    )

    response = admin_client.post(
        reverse("admin:accounts_registrationrequest_changelist"),
        {
            "action": "reject_requests",
            "_selected_action": [str(registration.pk)],
        },
        follow=True,
    )

    registration.refresh_from_db()

    assert response.status_code == 200
    assert registration.status == "rejected"
    assert registration.reviewed_by is not None
