from django.urls import re_path
from .views import AuthProxyView, OrderProxyView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"orders", OrderProxyView, basename="order")

urlpatterns = [
    re_path(
        r"^api/auth/(?P<endpoint>login|register|refresh)/?$",
        AuthProxyView.as_view(),
        name="auth-proxy",
    ),
]

urlpatterns += router.urls
