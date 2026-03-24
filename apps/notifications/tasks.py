import logging

from celery import shared_task

from .services import NotificationDispatcher

logger = logging.getLogger(__name__)


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
        logger.warning("Notification event was not found event_id=%s", event_id)
        return

    logger.info("Dispatching price change notification event_id=%s", event_id)
    NotificationDispatcher().send_price_change(event)
