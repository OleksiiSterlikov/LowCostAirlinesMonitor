from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import ForcedPasswordChangeForm, LoginForm, ProfileForm, RegistrationRequestForm


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm


class LogoutView(auth_views.LogoutView):
    pass


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = ForcedPasswordChangeForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.temporary_password_issued = False
        self.request.user.save(update_fields=["must_change_password", "temporary_password_issued"])
        messages.success(self.request, "Пароль змінено.")
        return response


def register_request(request):
    if request.method == "POST":
        form = RegistrationRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Запит на реєстрацію надіслано. Очікуйте підтвердження адміністратора.")
            return redirect("login")
    else:
        form = RegistrationRequestForm()
    return render(request, "accounts/register_request.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль оновлено.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
