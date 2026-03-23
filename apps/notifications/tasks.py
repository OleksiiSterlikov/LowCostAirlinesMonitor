from celery import shared_task

from .services import NotificationDispatcher


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_price_change_notification(event_id: int) -> None:
    from apps.searches.models import PriceChangeEvent

    event = (
        PriceChangeEvent.objects.select_related("subscription__user", "provider")
        .filter(pk=event_id)
        .first()
    )
    if event is None:
        return

    NotificationDispatcher().send_price_change(event)
