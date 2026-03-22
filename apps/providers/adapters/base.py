from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass
class SearchQuery:
    origin: str
    destination: str
    date_from: date
    date_to: date
    currency: str = "EUR"
    passengers: int = 1
    baggage: bool = False


@dataclass
class FareOption:
    provider_code: str
    provider_name: str
    origin: str
    destination: str
    outbound_date: date
    return_date: date | None
    amount: Decimal
    currency: str
    fare_name: str = "basic"
    deeplink: str = ""
    raw_payload: dict | None = None


class AirlineAdapter(Protocol):
    provider_code: str
    provider_name: str

    def search(self, query: SearchQuery) -> list[FareOption]: ...
