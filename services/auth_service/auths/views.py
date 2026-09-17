from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

from .serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UserSerializer,
)

from authlib.jose import JsonWebKey


def get_tokens_for_user(user):
    """Generate simplejwt access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh_token": str(refresh),
        "access_token": str(refresh.access_token),
    }


class RegisterView(APIView):
    """API view for user registration."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        response_data = {
            "user": UserSerializer(user).data,
            "refresh_token": tokens["refresh_token"],
            "access_token": tokens["access_token"],
        }

        return Response(
            {
                "success": True,
                "message": "User registered successfully.",
                "data": [response_data],
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """API view for user authentication / login."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Authentication failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data["user"]
        tokens = get_tokens_for_user(user)

        response_data = {
            "user": UserSerializer(user).data,
            "refresh_token": tokens["refresh_token"],
            "access_token": tokens["access_token"],
        }

        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": [response_data],
            },
            status=status.HTTP_200_OK,
        )


class RefreshTokenView(APIView):
    """API view for refreshing JWT access tokens."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Token refresh failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh_instance = serializer.validated_data["refresh_instance"]
        access_token = str(refresh_instance.access_token)
        refresh_token = serializer.validated_data.get("token_str")

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh_instance.blacklist()
                except AttributeError:
                    pass
            refresh_instance.set_jti()
            refresh_instance.set_exp()
            refresh_token = str(refresh_instance)

        response_data = {
            "refresh_token": refresh_token,
            "access_token": access_token,
        }

        return Response(
            {
                "success": True,
                "message": "Token refreshed successfully.",
                "data": [response_data],
            },
            status=status.HTTP_200_OK,
        )


class JWKSView(APIView):
    """API view to serve the JSON Web Key Set (JWKS)."""

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        key = JsonWebKey.import_key(settings.PUBLIC_KEY, {"kty": "RSA"})
        jwk_dict = key.as_dict()

        jwk_dict.update(
            {
                "kid": "key-id-v1",
                "use": "sig",
                "alg": "RS256",
            }
        )

        return Response(
            {
                "keys": [jwk_dict],
            },
            status=status.HTTP_200_OK,
        )
