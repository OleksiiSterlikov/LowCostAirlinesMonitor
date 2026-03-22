from .base import FareOption, SearchQuery


class WizzAirAdapter:
    provider_code = "wizzair"
    provider_name = "Wizz Air"

    def search(self, query: SearchQuery) -> list[FareOption]:
        # TODO: implement real integration
        return []
