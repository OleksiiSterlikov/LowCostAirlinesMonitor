from datetime import date
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from apps.searches.models import SearchSubscription


def test_check_subscription_now_queues_polling_for_active_subscription(monkeypatch, db):
    user = get_user_model().objects.create_user(
        username="dashboard-queue-user",
        email="dashboard-queue-user@example.com",
        password="StrongPass123!",
    )
    subscription = SearchSubscription.objects.create(
        user=user,
        origin="DTM",
        destination="KTW",
        date_from=date(2026, 8, 2),
        date_to=date(2026, 8, 9),
        notify_via="email",
        status="active",
    )
    delay_mock = Mock()
    monkeypatch.setattr("apps.dashboard.views.poll_subscription.delay", delay_mock)

    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("dashboard:check_subscription_now", args=[subscription.pk]),
        {"next": reverse("dashboard:home")},
        follow=True,
    )

    assert response.status_code == 200
    delay_mock.assert_called_once_with(subscription.pk)

    messages = [message.message for message in get_messages(response.wsgi_request)]
    assert any("додано в чергу" in message.lower() for message in messages)


def test_check_subscription_now_skips_non_active_subscription(monkeypatch, db):
    user = get_user_model().objects.create_user(
        username="dashboard-cancelled-user",
        email="dashboard-cancelled-user@example.com",
        password="StrongPass123!",
    )
    subscription = SearchSubscription.objects.create(
        user=user,
        origin="DTM",
        destination="KTW",
        date_from=date(2026, 8, 2),
        date_to=date(2026, 8, 9),
        notify_via="email",
        status="cancelled",
    )
    delay_mock = Mock()
    monkeypatch.setattr("apps.dashboard.views.poll_subscription.delay", delay_mock)

    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("dashboard:check_subscription_now", args=[subscription.pk]),
        {"next": reverse("dashboard:home")},
        follow=True,
    )

    assert response.status_code == 200
    delay_mock.assert_not_called()

    messages = [message.message for message in get_messages(response.wsgi_request)]
    assert any("лише для активних" in message.lower() for message in messages)
