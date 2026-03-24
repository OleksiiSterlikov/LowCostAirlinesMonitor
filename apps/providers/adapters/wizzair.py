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
    default_site_base_url = "https://www.wizzair.com"

    def __init__(self, provider=None, client: httpx.Client | None = None) -> None:
        config = provider.config_json if provider is not None else {}
        self.provider = provider
        self.base_url = config.get("base_url", self.default_base_url).rstrip("/")
        self.site_base_url = config.get("site_base_url", self.default_site_base_url).rstrip("/")
        self.market = config.get("market", "en-gb")
        self.timeout = config.get("timeout", 30.0)
        self.bootstrap_enabled = config.get("bootstrap_enabled", True)
        self.cookie_header = config.get("cookie_header", "")
        self.playwright_fallback_enabled = config.get("playwright_fallback_enabled", True)
        self.playwright_headless = config.get("playwright_headless", True)
        self.playwright_timeout_ms = config.get("playwright_timeout_ms", 45000)
        self.client = client or httpx.Client(
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                "Origin": "https://www.wizzair.com",
                "Referer": f"{self.site_base_url}/{self.market}",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-GB,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            },
        )
        if self.cookie_header:
            self.client.headers["Cookie"] = self.cookie_header

    def search(self, query: SearchQuery) -> list[FareOption]:
        self._bootstrap_session(query)
        try:
            data = self._fetch_results(query)
        except WizzAirRateLimitError as exc:
            if not self.playwright_fallback_enabled:
                raise
            try:
                data = self._fetch_results_with_playwright(query)
            except ModuleNotFoundError:
                raise exc
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

    def _bootstrap_session(self, query: SearchQuery) -> None:
        if not self.bootstrap_enabled:
            return

        homepage_url = f"{self.site_base_url}/{self.market}"
        booking_url = self._build_deeplink(query, query.date_from)

        for url in (homepage_url, booking_url):
            response = self.client.get(
                url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none" if url == homepage_url else "same-origin",
                },
                follow_redirects=True,
            )
            response.raise_for_status()

    def _fetch_results_with_playwright(self, query: SearchQuery) -> dict[str, Any]:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.playwright_headless)
            context = browser.new_context(
                locale="en-GB",
                user_agent=self.client.headers["User-Agent"],
            )
            page = context.new_page()
            try:
                page.set_default_timeout(self.playwright_timeout_ms)
                page.goto(f"{self.site_base_url}/{self.market}", wait_until="domcontentloaded")
                page.goto(self._build_deeplink(query, query.date_from), wait_until="domcontentloaded")

                def _is_search_response(response):
                    return (
                        "/Api/search/search" in response.url
                        and response.request.method.upper() == "POST"
                    )

                try:
                    with page.expect_response(_is_search_response, timeout=self.playwright_timeout_ms) as response_info:
                        page.reload(wait_until="domcontentloaded")
                    response = response_info.value
                    if response.status == 200:
                        return response.json()
                except PlaywrightTimeoutError:
                    pass

                payload = page.evaluate(
                    """
                    async ({ apiUrl, requestBody }) => {
                        const response = await fetch(apiUrl, {
                            method: "POST",
                            headers: {
                                "accept": "application/json, text/plain, */*",
                                "content-type": "application/json;charset=UTF-8"
                            },
                            credentials: "include",
                            body: JSON.stringify(requestBody),
                        });
                        const text = await response.text();
                        return {
                            status: response.status,
                            body: text,
                        };
                    }
                    """,
                    {
                        "apiUrl": f"{self.base_url}/search/search",
                        "requestBody": {
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
                    },
                )
                if payload["status"] == 429:
                    raise WizzAirRateLimitError(
                        "Wizz Air Playwright fallback was also rate-limited.",
                        request=None,
                        response=None,
                    )
                if payload["status"] >= 400:
                    raise httpx.HTTPStatusError(
                        f"Wizz Air Playwright fallback failed with status {payload['status']}.",
                        request=None,
                        response=None,
                    )
                return httpx.Response(200, text=payload["body"]).json()
            finally:
                context.close()
                browser.close()

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
            f"{self.site_base_url}/{self.market}/booking/select-flight/"
            f"{query.origin}/{query.destination}/{departure_date.isoformat()}/null/"
            f"{query.passengers}/0/0/null"
        )
