from smtplib import SMTPException
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from celery.exceptions import Retry

from apps.notifications.services import EmailNotifier
from apps.notifications.tasks import send_price_change_notification


def _patch_price_change_event_lookup(monkeypatch, event) -> None:
    class FakeManager:
        def select_related(self, *_args, **_kwargs):
            return self

        def filter(self, **_kwargs):
            return self

        def first(self):
            return event

    monkeypatch.setattr(
        "apps.searches.models.PriceChangeEvent",
        SimpleNamespace(objects=FakeManager()),
    )


def test_email_notifier_propagates_smtp_errors(monkeypatch):
    def fake_send_mail(*args, **kwargs):
        raise SMTPException("smtp is down")

    monkeypatch.setattr("apps.notifications.services.send_mail", fake_send_mail)

    with pytest.raises(SMTPException):
        EmailNotifier().send("user@example.com", "Subject", "Body")


def test_send_price_change_notification_task_has_retry_policy():
    assert send_price_change_notification.autoretry_for == (Exception,)
    assert send_price_change_notification.retry_backoff is True
    assert send_price_change_notification.retry_jitter is True
    assert send_price_change_notification.max_retries == 3


def test_send_price_change_notification_retries_on_smtp_errors(monkeypatch):
    _patch_price_change_event_lookup(monkeypatch, event=SimpleNamespace(pk=1))

    def raise_smtp(_event):
        raise SMTPException("smtp is down")

    monkeypatch.setattr(
        "apps.notifications.tasks.NotificationDispatcher",
        lambda: SimpleNamespace(send_price_change=raise_smtp),
    )
    retry_mock = Mock(side_effect=Retry())
    monkeypatch.setattr(send_price_change_notification, "retry", retry_mock)

    with pytest.raises(Retry):
        send_price_change_notification.run(1)

    assert retry_mock.call_count == 1
    assert isinstance(retry_mock.call_args.kwargs.get("exc"), SMTPException)
