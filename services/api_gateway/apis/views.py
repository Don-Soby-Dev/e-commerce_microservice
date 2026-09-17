from django.shortcuts import render
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

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
