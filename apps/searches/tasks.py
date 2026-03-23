from celery import shared_task

from .models import SearchSubscription
from .services import SearchPollingService


@shared_task
def poll_active_searches() -> int:
    queued = 0
    subscription_ids = list(
        SearchSubscription.objects.filter(status="active").values_list("id", flat=True)
    )
    for subscription_id in subscription_ids:
        poll_subscription.delay(subscription_id)
        queued += 1
    return queued


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def poll_subscription(subscription_id: int) -> int:
    subscription = SearchSubscription.objects.filter(pk=subscription_id).select_related("user").first()
    if subscription is None:
        return 0
    return SearchPollingService().run_subscription(subscription)
