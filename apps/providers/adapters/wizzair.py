from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .base import FareOption, SearchQuery


class WizzAirRateLimitError(httpx.HTTPStatusError):
    pass


def _should_retry_wizzair_request(exc: BaseException) -> bool:
    if isinstance(exc, WizzAirRateLimitError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response is not None and exc.response.status_code >= 500
    return isinstance(exc, httpx.HTTPError)


class WizzAirAdapter:
    provider_code = "wizzair"
    provider_name = "Wizz Air"
    default_base_url = "https://be.wizzair.com/9.13.0/Api"

    def __init__(self, provider=None, client: httpx.Client | None = None) -> None:
        config = provider.config_json if provider is not None else {}
        self.provider = provider
        self.base_url = config.get("base_url", self.default_base_url).rstrip("/")
        self.timeout = config.get("timeout", 30.0)
        self.client = client or httpx.Client(
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Origin": "https://www.wizzair.com",
                "Referer": "https://www.wizzair.com/",
                "Accept": "application/json, text/plain, */*",
            },
        )

    def search(self, query: SearchQuery) -> list[FareOption]:
        data = self._fetch_results(query)
        return self._map_response(data, query)

    @retry(
        retry=retry_if_exception(_should_retry_wizzair_request),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _fetch_results(self, query: SearchQuery) -> dict[str, Any]:
        response = self.client.post(
            f"{self.base_url}/search/search",
            json={
                "flightList": [
                    {
                        "departureStation": query.origin,
                        "arrivalStation": query.destination,
                        "departureDate": query.date_from.isoformat(),
                    }
                ],
                "adultCount": query.passengers,
                "childCount": 0,
                "infantCount": 0,
                "wdc": False,
                "isFlightChange": False,
                "isSeniorOrStudent": False,
            },
        )
        if response.status_code == 429:
            raise WizzAirRateLimitError(
                "Wizz Air rate limit or bot protection triggered.",
                request=response.request,
                response=response,
            )

        response.raise_for_status()
        return response.json()

    def _map_response(self, data: dict[str, Any], query: SearchQuery) -> list[FareOption]:
        fares: list[FareOption] = []
        for flight in self._extract_flights(data):
            departure_value = (
                flight.get("departureDate")
                or flight.get("departureDateTime")
                or flight.get("departureDatetime")
                or flight.get("departureTime")
            )
            if not departure_value:
                continue

            amount, currency = self._extract_price(flight)
            if amount is None or currency is None:
                continue

            departure_date = date.fromisoformat(str(departure_value)[:10])
            fares.append(
                FareOption(
                    provider_code=self.provider_code,
                    provider_name=self.provider_name,
                    origin=query.origin,
                    destination=query.destination,
                    outbound_date=departure_date,
                    return_date=None,
                    amount=amount,
                    currency=currency,
                    fare_name=self._extract_fare_name(flight),
                    deeplink=self._build_deeplink(query, departure_date),
                    raw_payload=flight,
                )
            )

        return sorted(fares, key=lambda fare: fare.outbound_date)

    def _extract_flights(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("outboundFlights", "flights", "departureFlights"):
            flights = data.get(key)
            if isinstance(flights, list):
                return [flight for flight in flights if isinstance(flight, dict)]
        return []

    def _extract_price(self, flight: dict[str, Any]) -> tuple[Decimal | None, str | None]:
        fare_candidates = []

        if isinstance(flight.get("fares"), list):
            fare_candidates.extend(fare for fare in flight["fares"] if isinstance(fare, dict))
        if isinstance(flight.get("price"), dict):
            fare_candidates.append(flight["price"])
        if isinstance(flight.get("fare"), dict):
            fare_candidates.append(flight["fare"])

        for fare_candidate in fare_candidates:
            amount = (
                fare_candidate.get("amount")
                or fare_candidate.get("amountIncludingAdminFee")
                or fare_candidate.get("value")
            )
            currency = (
                fare_candidate.get("currencyCode")
                or fare_candidate.get("currency")
                or fare_candidate.get("currencyName")
            )
            if amount is not None and currency:
                return Decimal(str(amount)), str(currency)

        return None, None

    def _extract_fare_name(self, flight: dict[str, Any]) -> str:
        if isinstance(flight.get("fares"), list) and flight["fares"]:
            first_fare = flight["fares"][0]
            return first_fare.get("fareType") or first_fare.get("type") or "basic"
        return "basic"

    def _build_deeplink(self, query: SearchQuery, departure_date: date) -> str:
        return (
            "https://www.wizzair.com/en-gb/booking/select-flight/"
            f"{query.origin}/{query.destination}/{departure_date.isoformat()}/null/"
            f"{query.passengers}/0/0/null"
        )
