from dataclasses import dataclass
import re

from django.db.models import Q

from .models import Airport

IATA_IN_BRACKETS_RE = re.compile(r"\(([A-Za-z]{3})\)")


@dataclass(frozen=True)
class AirportSuggestion:
    iata_code: str
    city_name: str
    airport_name: str
    country_name: str

    @property
    def label(self) -> str:
        return f"{self.city_name} - {self.airport_name} ({self.iata_code})"


class AirportCatalogService:
    def resolve_query(self, query: str) -> Airport | None:
        normalized = (query or "").strip()
        if not normalized:
            return None

        inline_code_match = IATA_IN_BRACKETS_RE.search(normalized)
        if inline_code_match:
            airport = self._get_by_code(inline_code_match.group(1))
            if airport is not None:
                return airport

        airport = self._get_by_code(normalized)
        if airport is not None:
            return airport

        exact_matches = list(
            Airport.objects.filter(is_active=True).filter(
                Q(city_name__iexact=normalized) | Q(airport_name__iexact=normalized)
            )[:2]
        )
        if len(exact_matches) == 1:
            return exact_matches[0]

        prefix_matches = list(self._suggest_queryset(normalized)[:2])
        if len(prefix_matches) == 1:
            return prefix_matches[0]

        return None

    def suggest(self, query: str, limit: int = 8) -> list[AirportSuggestion]:
        normalized = (query or "").strip()
        if len(normalized) < 2:
            return []

        return [
            AirportSuggestion(
                iata_code=airport.iata_code,
                city_name=airport.city_name,
                airport_name=airport.airport_name,
                country_name=airport.country_name,
            )
            for airport in self._suggest_queryset(normalized)[:limit]
        ]

    def _get_by_code(self, value: str) -> Airport | None:
        return Airport.objects.filter(is_active=True, iata_code=value.upper()).first()

    def _suggest_queryset(self, normalized: str):
        return Airport.objects.filter(is_active=True).filter(
            Q(city_name__istartswith=normalized)
            | Q(airport_name__istartswith=normalized)
            | Q(iata_code__istartswith=normalized)
        )
