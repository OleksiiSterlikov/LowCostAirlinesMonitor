from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("subscription/<int:pk>/", views.subscription_detail, name="subscription_detail"),
    path("subscription/<int:pk>/cancel/", views.cancel_subscription, name="cancel_subscription"),
]
