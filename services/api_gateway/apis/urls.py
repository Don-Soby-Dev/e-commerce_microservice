from django.urls import re_path
from rest_framework.routers import DefaultRouter

from .views import AuthProxyView, OrderProxyView, ProductProxyView

router = DefaultRouter()
router.register(r"orders", OrderProxyView, basename="order")
router.register(r"products", ProductProxyView, basename="product")

urlpatterns = [
    re_path(
        r"^auth/(?P<endpoint>login|register|refresh)/?$",
        AuthProxyView.as_view(),
        name="auth-proxy",
    ),
]

urlpatterns += router.urls
