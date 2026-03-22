from django.shortcuts import redirect
from django.urls import reverse


class RequirePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and getattr(user, "must_change_password", False)
            and request.path not in {reverse("password_change"), reverse("logout")}
            and not request.path.startswith("/admin/")
        ):
            return redirect("password_change")
        return self.get_response(request)
