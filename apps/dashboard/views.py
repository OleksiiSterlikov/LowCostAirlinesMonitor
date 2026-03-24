from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.searches.forms import SearchSubscriptionForm
from apps.searches.models import SearchSubscription

from .services import BestOfferService


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
            "subscriptions": subscriptions,
        },
    )


@login_required
def subscription_detail(request, pk: int):
    subscription = get_object_or_404(SearchSubscription, pk=pk, user=request.user)
    snapshots = subscription.snapshots.select_related("provider").order_by("-created_at")[:200]
    return render(
        request,
        "dashboard/subscription_detail.html",
        {"subscription": subscription, "snapshots": snapshots},
    )


@login_required
def cancel_subscription(request, pk: int):
    subscription = get_object_or_404(SearchSubscription, pk=pk, user=request.user)
    subscription.status = "cancelled"
    subscription.save(update_fields=["status", "updated_at"])
    messages.info(request, "Моніторинг зупинено.")
    return redirect("dashboard:home")
