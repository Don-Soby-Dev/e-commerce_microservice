import jwt
from jwt import PyJWKClient, PyJWTError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from config.settings import JWKS_SERVING_URL

jwks_client = PyJWKClient(
    JWKS_SERVING_URL,
    cache_keys=True,
    max_cached_keys=16,
    cache_jwk_set=True,
    lifespan=3600,
)


class ServiceUser:
    """Lightweight user object for microservices without a local user database."""

    def __init__(self, token_payload):
        self.payload = token_payload
        self.id = token_payload.get("user_id") or token_payload.get("sub")
        self.username = token_payload.get("username", "")
        self.is_authenticated = True

    def __str__(self):
        return f"ServiceUser(id={self.id}, username={self.username})"


class JWTGatewayAuthenticaion(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None  # No authentication header provided

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer":
            raise AuthenticationFailed("Invalid token format")
        token = parts[1]

        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            raise AuthenticationFailed("Invalid token header")

        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg")

        if not kid or not alg:
            raise AuthenticationFailed("Missing 'kid' or 'alg' in token header")
        if alg != "RS256":
            raise AuthenticationFailed("Invalid token algorithm")

        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token).key

            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"verify_exp": True},
            )
        except PyJWTError as exc:
            raise AuthenticationFailed(f"Token verification failed: {str(exc)}")
        except Exception as exc:
            raise AuthenticationFailed(
                f"An error occurred during token verification: {str(exc)}"
            )

        return (ServiceUser(payload), payload)
