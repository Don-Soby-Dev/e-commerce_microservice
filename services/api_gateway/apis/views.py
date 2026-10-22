import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import JWTGatewayAuthenticaion


class AuthProxyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, endpoint=None):
        auth_service_url = settings.AUTH_SERVICE_URL.rstrip("/")
        target_url = f"{auth_service_url}/{endpoint}/" if endpoint else f"{auth_service_url}/"
        try:
            response = requests.post(target_url, json=request.data)
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text}
            return Response(data=data, status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Auth service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class OrderProxyView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTGatewayAuthenticaion]

    def list(self, request):
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            params = {}
            if hasattr(request, "user") and getattr(request.user, "id", None):
                params["user_id"] = request.user.id
            response = requests.get(
                order_service_url,
                params=params,
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def create(self, request):
        order_service_url = settings.ORDER_SERVICE_URL
        payload = dict(request.data) if isinstance(request.data, dict) else request.data
        if hasattr(request, "user") and getattr(request.user, "id", None):
            payload["user_id"] = request.user.id
        try:
            response = requests.post(
                order_service_url,
                json=payload,
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def retrieve(self, request, pk=None):
        order_service_url = settings.ORDER_SERVICE_URL.rstrip("/")
        try:
            response = requests.get(
                f"{order_service_url}/{pk}/",
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def update(self, request, pk=None):
        order_service_url = settings.ORDER_SERVICE_URL.rstrip("/")
        try:
            response = requests.put(
                f"{order_service_url}/{pk}/",
                json=request.data,
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def partial_update(self, request, pk=None):
        order_service_url = settings.ORDER_SERVICE_URL.rstrip("/")
        try:
            response = requests.patch(
                f"{order_service_url}/{pk}/",
                json=request.data,
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def destroy(self, request, pk=None):
        order_service_url = settings.ORDER_SERVICE_URL.rstrip("/")
        try:
            response = requests.delete(
                f"{order_service_url}/{pk}/",
                headers={"Authorization": request.headers.get("Authorization")},
            )
            if response.status_code == 204:
                return Response(status=status.HTTP_204_NO_CONTENT)
            try:
                data = response.json()
            except Exception:
                data = None
            return Response(data=data, status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class ProductProxyView(viewsets.ViewSet):
    authentication_classes = [JWTGatewayAuthenticaion]

    def get_permissions(self):
        if getattr(self, "action", None) in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        product_service_url = settings.PRODUCT_SERVICE_URL
        try:
            response = requests.get(product_service_url, params=request.query_params)
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Product service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def retrieve(self, request, pk=None):
        product_service_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        try:
            response = requests.get(f"{product_service_url}/{pk}/")
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Product service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def create(self, request):
        product_service_url = settings.PRODUCT_SERVICE_URL
        try:
            response = requests.post(product_service_url, json=request.data)
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Product service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def update(self, request, pk=None):
        product_service_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        try:
            response = requests.put(f"{product_service_url}/{pk}/", json=request.data)
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Product service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def partial_update(self, request, pk=None):
        product_service_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        try:
            response = requests.patch(f"{product_service_url}/{pk}/", json=request.data)
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Product service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def destroy(self, request, pk=None):
        product_service_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        try:
            response = requests.delete(f"{product_service_url}/{pk}/")
            if response.status_code == 204:
                return Response(status=status.HTTP_204_NO_CONTENT)
            try:
                data = response.json()
            except Exception:
                data = None
            return Response(data=data, status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Product service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
