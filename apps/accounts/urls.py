from django.urls import path

from .views import LoginView, LogoutView, PasswordChangeView, profile, register_request

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("register/", register_request, name="register_request"),
    path("profile/", profile, name="profile"),
]
