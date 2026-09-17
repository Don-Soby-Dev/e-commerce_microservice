from django.urls import re_path
from .views import AuthProxyView

urlpatterns = [
    re_path(
        r"^api/auth/(?P<endpoint>login|register|refresh)/?$",
        AuthProxyView.as_view(),
        name="auth-proxy",
    ),
]
