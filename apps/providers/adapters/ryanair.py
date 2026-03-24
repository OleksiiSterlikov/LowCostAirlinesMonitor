from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .base import FareOption, SearchQuery


class RyanairAdapter:
    provider_code = "ryanair"
    provider_name = "Ryanair"
    default_base_url = "https://www.ryanair.com/api/farfnd/v4"

    def __init__(self, provider=None, client: httpx.Client | None = None) -> None:
        config = provider.config_json if provider is not None else {}
        self.provider = provider
        self.base_url = config.get("base_url", self.default_base_url).rstrip("/")
        self.market = config.get("market", "en-gb")
        self.language = config.get("language", "en")
        self.timeout = config.get("timeout", 30.0)
        self.max_price = config.get("max_price", 1000)
        self.client = client or httpx.Client(
            timeout=self.timeout,
            headers={"User-Agent": "LowCostMonitor/1.0 (+https://www.ryanair.com/)"},
        )

    def search(self, query: SearchQuery) -> list[FareOption]:
        fares: list[FareOption] = []
        next_page: str | None = None

        while True:
            data = self._fetch_page(query, next_page)
            fares.extend(self._map_fares(data.get("fares", []), query))
            next_page = data.get("nextPage")
            if not next_page:
                break

        return sorted(fares, key=lambda fare: fare.outbound_date)

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _fetch_page(self, query: SearchQuery, next_page: str | None = None) -> dict[str, Any]:
        if next_page:
            response = self.client.get(next_page)
        else:
            response = self.client.get(
                f"{self.base_url}/oneWayFares",
                params={
                    "departureAirportIataCode": query.origin,
                    "arrivalAirportIataCode": query.destination,
                    "outboundDepartureDateFrom": query.date_from.isoformat(),
                    "outboundDepartureDateTo": query.date_to.isoformat(),
                    "language": self.language,
                    "market": self.market,
                    "adultPaxCount": query.passengers,
                    "priceValueTo": self.max_price,
                    "promoCode": "",
                },
            )

        response.raise_for_status()
        return response.json()

    def _map_fares(self, fares: list[dict[str, Any]], query: SearchQuery) -> list[FareOption]:
        mapped_fares: list[FareOption] = []

        for fare in fares:
            outbound = fare["outbound"]
            summary_price = fare.get("summary", {}).get("price") or outbound["price"]
            mapped_fares.append(
                FareOption(
                    provider_code=self.provider_code,
                    provider_name=self.provider_name,
                    origin=query.origin,
                    destination=query.destination,
                    outbound_date=date.fromisoformat(outbound["departureDate"][:10]),
                    return_date=None,
                    amount=Decimal(str(summary_price["value"])),
                    currency=summary_price["currencyCode"],
                    fare_name="basic",
                    deeplink=self._build_deeplink(query, outbound["departureDate"][:10]),
                    raw_payload=fare,
                )
            )

        return mapped_fares

    def _build_deeplink(self, query: SearchQuery, departure_date: str) -> str:
        return (
            f"https://www.ryanair.com/{self.market}/en/trip/flights/select"
            f"?adults={query.passengers}"
            f"&teens=0&children=0&infants=0"
            f"&dateOut={departure_date}"
            f"&dateIn="
            f"&isConnectedFlight=false&discount=0&promoCode="
            f"&originIata={query.origin}&destinationIata={query.destination}"
        )
