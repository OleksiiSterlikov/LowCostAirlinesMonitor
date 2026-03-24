from django.http import JsonResponse

from .services import AirportCatalogService


def airport_suggestions(request):
    query = request.GET.get("q", "")
    suggestions = AirportCatalogService().suggest(query)
    return JsonResponse(
        {
            "results": [
                {
                    "iata_code": suggestion.iata_code,
                    "city_name": suggestion.city_name,
                    "airport_name": suggestion.airport_name,
                    "country_name": suggestion.country_name,
                    "label": suggestion.label,
                }
                for suggestion in suggestions
            ]
        }
    )
