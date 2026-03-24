from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import QuerySet
from django.utils import timezone

from apps.searches.models import FareSnapshot


@dataclass(frozen=True)
class BestOfferWindow:
    slug: str
    title: str
    date_from: date
    date_to: date


class BestOfferService:
    def get_dashboard_offers(self, reference_date: date | None = None) -> list[dict]:
        today = reference_date or timezone.localdate()
        offers = []

        for window in self._build_windows(today):
            snapshot = self._get_best_snapshot(window)
            offers.append(
                {
                    "slug": window.slug,
                    "title": window.title,
                    "date_from": window.date_from,
                    "date_to": window.date_to,
                    "snapshot": snapshot,
                }
            )

        return offers

    def _build_windows(self, today: date) -> list[BestOfferWindow]:
        week_end = today + timedelta(days=(6 - today.weekday()))
        next_week_start = week_end + timedelta(days=1)
        next_week_end = next_week_start + timedelta(days=6)

        if today.month == 12:
            next_month_year = today.year + 1
            next_month = 1
        else:
            next_month_year = today.year
            next_month = today.month + 1
        next_month_start = date(next_month_year, next_month, 1)
        next_month_end = date(
            next_month_year,
            next_month,
            monthrange(next_month_year, next_month)[1],
        )

        return [
            BestOfferWindow("this_week", "Цей тиждень", today, week_end),
            BestOfferWindow("next_week", "Наступний тиждень", next_week_start, next_week_end),
            BestOfferWindow("next_month", "Наступний місяць", next_month_start, next_month_end),
        ]

    def _get_best_snapshot(self, window: BestOfferWindow):
        return (
            self._base_queryset()
            .filter(outbound_date__gte=window.date_from, outbound_date__lte=window.date_to)
            .order_by("price_amount", "outbound_date", "-created_at")
            .first()
        )

    def _base_queryset(self) -> QuerySet[FareSnapshot]:
        return FareSnapshot.objects.select_related("provider", "subscription")
