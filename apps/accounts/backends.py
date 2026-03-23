from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get("email")
        if login_value is None or password is None:
            return None

        user_model = get_user_model()
        try:
            user = user_model.objects.get(email__iexact=login_value)
        except user_model.DoesNotExist:
            try:
                user = user_model.objects.get(username=login_value)
            except user_model.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
