from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from apps.providers.adapters.base import SearchQuery
from apps.providers.adapters.wizzair import WizzAirAdapter, WizzAirRateLimitError
from apps.providers.models import AirlineProvider


def test_wizzair_adapter_maps_flights_from_api_payload(db):
    provider = AirlineProvider.objects.create(
        code="wizzair-test",
        name="Wizz Air Test",
        adapter_path="apps.providers.adapters.wizzair.WizzAirAdapter",
    )
    client = Mock()
    client.post.return_value = Mock(
        status_code=200,
        raise_for_status=Mock(),
        json=Mock(
            return_value={
                "outboundFlights": [
                    {
                        "departureDateTime": "2026-05-15T06:10:00",
                        "fares": [
                            {
                                "fareType": "BASIC",
                                "amount": 29.99,
                                "currencyCode": "EUR",
                            }
                        ],
                    }
                ]
            }
        ),
    )
    adapter = WizzAirAdapter(provider=provider, client=client)

    fares = adapter.search(
        SearchQuery(
            origin="BUD",
            destination="FCO",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
        )
    )

    assert len(fares) == 1
    assert fares[0].outbound_date == date(2026, 5, 15)
    assert fares[0].amount == Decimal("29.99")
    assert fares[0].currency == "EUR"
    assert fares[0].fare_name == "BASIC"
    assert fares[0].deeplink.startswith("https://www.wizzair.com/en-gb/booking/select-flight/")


def test_wizzair_adapter_supports_direct_price_shape(db):
    provider = AirlineProvider.objects.create(
        code="wizzair-direct-price",
        name="Wizz Air Direct Price",
        adapter_path="apps.providers.adapters.wizzair.WizzAirAdapter",
    )
    client = Mock()
    client.post.return_value = Mock(
        status_code=200,
        raise_for_status=Mock(),
        json=Mock(
            return_value={
                "flights": [
                    {
                        "departureDate": "2026-05-16T06:10:00",
                        "price": {"amount": 32.49, "currencyCode": "EUR"},
                    }
                ]
            }
        ),
    )
    adapter = WizzAirAdapter(provider=provider, client=client)

    fares = adapter.search(
        SearchQuery(
            origin="BUD",
            destination="FCO",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
        )
    )

    assert len(fares) == 1
    assert fares[0].amount == Decimal("32.49")


def test_wizzair_adapter_retries_and_raises_on_rate_limit(db):
    provider = AirlineProvider.objects.create(
        code="wizzair-rate-limit",
        name="Wizz Air Rate Limit",
        adapter_path="apps.providers.adapters.wizzair.WizzAirAdapter",
    )
    response = Mock(status_code=429, request=Mock())
    response.raise_for_status = Mock()
    client = Mock()
    client.post.return_value = response
    adapter = WizzAirAdapter(provider=provider, client=client)

    with pytest.raises(WizzAirRateLimitError):
        adapter.search(
            SearchQuery(
                origin="BUD",
                destination="FCO",
                date_from=date(2026, 5, 1),
                date_to=date(2026, 5, 31),
            )
        )

    assert client.post.call_count == 3
