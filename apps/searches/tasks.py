from celery import shared_task

from .models import SearchSubscription
from .services import SearchPollingService


@shared_task
def poll_active_searches() -> int:
    service = SearchPollingService()
    total = 0
    for subscription in SearchSubscription.objects.filter(status="active").select_related("user"):
        total += service.run_subscription(subscription)
    return total
