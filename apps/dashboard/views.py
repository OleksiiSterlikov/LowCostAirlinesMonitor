from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.providers.services import get_provider_runtime_statuses
from apps.searches.forms import SearchSubscriptionForm
from apps.searches.models import SearchSubscription
from apps.searches.tasks import poll_subscription

from .services import BestOfferService


def _resolve_redirect_target(request, subscription_pk: int) -> str:
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("dashboard:subscription_detail", kwargs={"pk": subscription_pk})


@login_required
def home(request):
    if request.method == "POST":
        form = SearchSubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.currency = "EUR"
            subscription.save()
            messages.success(request, "Пошук додано до моніторингу.")
            return redirect("dashboard:home")
    else:
        form = SearchSubscriptionForm()

    subscriptions = SearchSubscription.objects.filter(user=request.user).order_by("-created_at")
    best_offers = BestOfferService().get_dashboard_offers()
    return render(
        request,
        "dashboard/home.html",
        {
            "best_offers": best_offers,
            "form": form,
            "provider_statuses": get_provider_runtime_statuses(),
            "subscriptions": subscriptions,
        },
    )


@login_required
def subscription_detail(request, pk: int):
    subscription = get_object_or_404(SearchSubscription, pk=pk, user=request.user)
    snapshots = subscription.snapshots.select_related("provider").order_by("-created_at")[:200]
    provider_statuses = get_provider_runtime_statuses()
    return render(
        request,
        "dashboard/subscription_detail.html",
        {
            "provider_statuses": provider_statuses,
            "subscription": subscription,
            "snapshots": snapshots,
        },
    )


@login_required
@require_POST
def check_subscription_now(request, pk: int):
    subscription = get_object_or_404(SearchSubscription, pk=pk, user=request.user)
    if subscription.status != "active":
        messages.warning(request, "Ручна перевірка доступна лише для активних підписок.")
        return redirect(_resolve_redirect_target(request, subscription.pk))

    poll_subscription.delay(subscription.pk)
    messages.success(request, "Перевірку додано в чергу. Онови сторінку через кілька секунд.")
    return redirect(_resolve_redirect_target(request, subscription.pk))


@login_required
def cancel_subscription(request, pk: int):
    subscription = get_object_or_404(SearchSubscription, pk=pk, user=request.user)
    subscription.status = "cancelled"
    subscription.save(update_fields=["status", "updated_at"])
    messages.info(request, "Моніторинг зупинено.")
    return redirect("dashboard:home")
