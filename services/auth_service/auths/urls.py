from django.urls import path
from .views import LoginView, RefreshTokenView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register", RegisterView.as_view(), name="register-noslash"),
    path("login/", LoginView.as_view(), name="login"),
    path("login", LoginView.as_view(), name="login-noslash"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh"),
    path("refresh", RefreshTokenView.as_view(), name="refresh-noslash"),
]

