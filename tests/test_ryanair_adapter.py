from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import httpx
import pytest

from apps.providers.adapters.base import SearchQuery
from apps.providers.adapters.ryanair import RyanairAdapter
from apps.providers.models import AirlineProvider


def test_ryanair_adapter_maps_fares_from_api_payload(db):
    provider, _ = AirlineProvider.objects.update_or_create(
        code="ryanair",
        defaults={
            "name": "Ryanair",
            "adapter_path": "apps.providers.adapters.ryanair.RyanairAdapter",
            "config_json": {"market": "en-gb", "language": "en"},
        },
    )
    client = Mock()
    client.get.return_value = Mock(
        status_code=200,
        raise_for_status=Mock(),
        json=Mock(
            return_value={
                "fares": [
                    {
                        "outbound": {
                            "departureDate": "2026-05-19T20:00:00",
                            "price": {"value": 14.99, "currencyCode": "EUR"},
                        },
                        "summary": {
                            "price": {"value": 14.99, "currencyCode": "EUR"},
                        },
                    }
                ],
                "nextPage": None,
            }
        ),
    )
    adapter = RyanairAdapter(provider=provider, client=client)

    fares = adapter.search(
        SearchQuery(
            origin="DUB",
            destination="STN",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
        )
    )

    assert len(fares) == 1
    assert fares[0].provider_code == "ryanair"
    assert fares[0].outbound_date == date(2026, 5, 19)
    assert fares[0].amount == Decimal("14.99")
    assert fares[0].currency == "EUR"
    assert fares[0].deeplink.startswith("https://www.ryanair.com/en-gb/en/trip/flights/select")


def test_ryanair_adapter_handles_pagination(db):
    provider = AirlineProvider.objects.create(
        code="ryanair-page",
        name="Ryanair Page",
        adapter_path="apps.providers.adapters.ryanair.RyanairAdapter",
    )
    client = Mock()
    first_response = Mock(
        raise_for_status=Mock(),
        json=Mock(
            return_value={
                "fares": [
                    {
                        "outbound": {
                            "departureDate": "2026-05-20T10:00:00",
                            "price": {"value": 29.99, "currencyCode": "EUR"},
                        },
                        "summary": {"price": {"value": 29.99, "currencyCode": "EUR"}},
                    }
                ],
                "nextPage": "https://api.example.test/page-2",
            }
        ),
    )
    second_response = Mock(
        raise_for_status=Mock(),
        json=Mock(
            return_value={
                "fares": [
                    {
                        "outbound": {
                            "departureDate": "2026-05-21T10:00:00",
                            "price": {"value": 34.99, "currencyCode": "EUR"},
                        },
                        "summary": {"price": {"value": 34.99, "currencyCode": "EUR"}},
                    }
                ],
                "nextPage": None,
            }
        ),
    )
    client.get.side_effect = [first_response, second_response]
    adapter = RyanairAdapter(provider=provider, client=client)

    fares = adapter.search(
        SearchQuery(
            origin="DUB",
            destination="STN",
            date_from=date(2026, 5, 1),
            date_to=date(2026, 5, 31),
        )
    )

    assert len(fares) == 2
    assert fares[0].outbound_date == date(2026, 5, 20)
    assert fares[1].outbound_date == date(2026, 5, 21)


def test_ryanair_adapter_retries_http_errors(db):
    provider = AirlineProvider.objects.create(
        code="ryanair-retry",
        name="Ryanair Retry",
        adapter_path="apps.providers.adapters.ryanair.RyanairAdapter",
        config_json={"timeout": 1},
    )
    client = Mock()
    client.get.side_effect = httpx.ReadTimeout("timeout")
    adapter = RyanairAdapter(provider=provider, client=client)

    with pytest.raises(httpx.ReadTimeout):
        adapter.search(
            SearchQuery(
                origin="DUB",
                destination="STN",
                date_from=date(2026, 5, 1),
                date_to=date(2026, 5, 31),
            )
        )

    assert client.get.call_count == 3
