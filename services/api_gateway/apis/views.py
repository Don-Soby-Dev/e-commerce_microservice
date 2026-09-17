from django.shortcuts import render
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from .authentication import JWTGatewayAuthenticaion
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class AuthProxyView(APIView):

    def post(self, request):
        # Forward the request to the authentication service
        auth_service_url = settings.AUTH_SERVICE_URL
        try:
            response = requests.post(auth_service_url, json=request.data)
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Auth service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class OrderProxyView(viewsets.ViewSet):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTGatewayAuthenticaion]

    def list(self, request):
        # Forward the request to the order service
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            response = requests.get(
                order_service_url,
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def create(self, request):
        # Forward the request to the order service
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            response = requests.post(
                order_service_url,
                json=request.data,
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def retrieve(self, request, pk=None):
        # Forward the request to the order service
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            response = requests.get(
                f"{order_service_url}{pk}/",
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

    def update(self, request, pk=None):
        # Forward the request to the order service
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            response = requests.put(
                f"{order_service_url}{pk}/",
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
        # Forward the request to the order service
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            response = requests.patch(
                f"{order_service_url}{pk}/",
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
        # Forward the request to the order service
        order_service_url = settings.ORDER_SERVICE_URL
        try:
            response = requests.delete(
                f"{order_service_url}{pk}/",
                headers={"Authorization": request.headers.get("Authorization")},
            )
            return Response(data=response.json(), status=response.status_code)
        except requests.RequestException as e:
            return Response(
                {"error": f"Order service unreachable: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
