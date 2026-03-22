from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import RegistrationRequest, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Логін або email")


class RegistrationRequestForm(forms.ModelForm):
    class Meta:
        model = RegistrationRequest
        fields = ["first_name", "last_name", "email", "telegram_chat_id"]


class AdminUserCreateForm(UserCreationForm):
    temporary_password = forms.CharField(required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "telegram_chat_id",
            "is_active",
            "is_approved",
            "must_change_password",
        ]


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "telegram_chat_id"]


class ForcedPasswordChangeForm(PasswordChangeForm):
    pass
