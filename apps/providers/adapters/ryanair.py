from .base import FareOption, SearchQuery


class RyanairAdapter:
    provider_code = "ryanair"
    provider_name = "Ryanair"

    def search(self, query: SearchQuery) -> list[FareOption]:
        # TODO: implement real integration
        return []
