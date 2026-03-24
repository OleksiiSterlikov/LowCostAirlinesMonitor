from django.urls import path

from .views import airport_suggestions

app_name = "airports"

urlpatterns = [
    path("suggestions/", airport_suggestions, name="suggestions"),
]
