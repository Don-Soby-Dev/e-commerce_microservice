from typing import Any, Optional
import jwt
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class CustomAccessToken(AccessToken):
    """Custom AccessToken that includes 'kid' in the header and custom claims."""

    def __init__(self, *args, **kwargs):
        token = args[0] if args else kwargs.get("token")
        if token is not None:
            try:
                self.header = jwt.get_unverified_header(str(token))
            except Exception:
                self.header = {}
        else:
            self.header = getattr(self, "header", {})

        super().__init__(*args, **kwargs)
        self.header["kid"] = "key-id-v1"

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["user_id"] = user.id
        token["username"] = user.username
        return token

    def __str__(self) -> str:
        backend = self.get_token_backend()
        jwt_payload = self.payload.copy()
        if backend.audience is not None:
            jwt_payload["aud"] = backend.audience
        if backend.issuer is not None:
            jwt_payload["iss"] = backend.issuer

        token = jwt.encode(
            jwt_payload,
            backend.prepared_signing_key,
            algorithm=backend.algorithm,
            headers=getattr(self, "header", None),
            json_encoder=backend.json_encoder,
        )
        if isinstance(token, bytes):
            return token.decode("utf-8")
        return token


class CustomRefreshToken(RefreshToken):
    """Custom RefreshToken that includes 'kid' in the header, 'user_id' and 'username' claims,
    and produces CustomAccessToken instances."""

    access_token_class = CustomAccessToken

    def __init__(self, *args, **kwargs):
        token = args[0] if args else kwargs.get("token")
        if token is not None:
            try:
                self.header = jwt.get_unverified_header(str(token))
            except Exception:
                self.header = {}
        else:
            self.header = getattr(self, "header", {})

        super().__init__(*args, **kwargs)
        self.header["kid"] = "key-id-v1"

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token["user_id"] = user.id
        token["username"] = user.username
        return token

    def __str__(self) -> str:
        backend = self.get_token_backend()
        jwt_payload = self.payload.copy()
        if backend.audience is not None:
            jwt_payload["aud"] = backend.audience
        if backend.issuer is not None:
            jwt_payload["iss"] = backend.issuer

        token = jwt.encode(
            jwt_payload,
            backend.prepared_signing_key,
            algorithm=backend.algorithm,
            headers=getattr(self, "header", None),
            json_encoder=backend.json_encoder,
        )
        if isinstance(token, bytes):
            return token.decode("utf-8")
        return token
