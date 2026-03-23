import pytest


@pytest.fixture(scope="session")
def django_db_setup():
    from django.conf import settings

    settings.DATABASES["default"] = {
        **settings.DATABASES["default"],
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
