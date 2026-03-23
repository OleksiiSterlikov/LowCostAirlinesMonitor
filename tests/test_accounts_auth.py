from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def test_user_can_log_in_with_username(db):
    user_model = get_user_model()
    user_model.objects.create_user(
        username="traveler",
        email="traveler@example.com",
        password="StrongPass123!",
    )

    client = Client()
    response = client.post(
        reverse("login"),
        {"username": "traveler", "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("dashboard:home")


def test_user_can_log_in_with_email(db):
    user_model = get_user_model()
    user_model.objects.create_user(
        username="farewatcher",
        email="farewatcher@example.com",
        password="StrongPass123!",
    )

    client = Client()
    response = client.post(
        reverse("login"),
        {"username": "farewatcher@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("dashboard:home")


def test_email_login_is_case_insensitive(db):
    user_model = get_user_model()
    user_model.objects.create_user(
        username="skyline",
        email="skyline@example.com",
        password="StrongPass123!",
    )

    client = Client()
    response = client.post(
        reverse("login"),
        {"username": "SkyLine@Example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("dashboard:home")
