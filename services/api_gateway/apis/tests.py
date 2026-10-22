from unittest.mock import MagicMock, patch
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from apis.authentication import ServiceUser
from apis.views import AuthProxyView, OrderProxyView, ProductProxyView


class AuthProxyViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apis.views.requests.post")
    def test_auth_proxy_login_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Login successful.",
            "data": [{"access_token": "token123", "refresh_token": "refresh123"}],
        }
        mock_post.return_value = mock_response

        payload = {"username": "testuser", "password": "password123"}
        response = self.client.post("/api/auth/login/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertTrue(called_url.endswith("/login/"))

    @patch("apis.views.requests.post")
    def test_auth_proxy_register_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "message": "User registered successfully.",
        }
        mock_post.return_value = mock_response

        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
        }
        response = self.client.post("/api/auth/register/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertTrue(called_url.endswith("/register/"))

    @patch("apis.views.requests.post")
    def test_auth_proxy_service_unreachable(self, mock_post):
        import requests
        mock_post.side_effect = requests.RequestException("Connection refused")

        payload = {"username": "testuser", "password": "password123"}
        response = self.client.post("/api/auth/login/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)


class OrderProxyViewTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = ServiceUser({"user_id": 42, "username": "alice"})

    @patch("apis.views.requests.post")
    def test_order_create_injects_authenticated_user_id(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "user_id": 42,
            "status": "CONFIRMED",
            "total_amount": "50.00",
        }
        mock_post.return_value = mock_response

        request = self.factory.post(
            "/api/orders/",
            {"items": [{"product_id": 1, "quantity": 2}]},
            format="json",
        )
        force_authenticate(request, user=self.user)

        view = OrderProxyView.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_post.assert_called_once()
        # Verify that user_id was injected into the json payload sent to order service
        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(sent_payload["user_id"], 42)

    @patch("apis.views.requests.post")
    def test_order_create_overwrites_spoofed_user_id(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1}
        mock_post.return_value = mock_response

        # Attacker tries to pass user_id: 999
        request = self.factory.post(
            "/api/orders/",
            {"user_id": 999, "items": [{"product_id": 1, "quantity": 1}]},
            format="json",
        )
        force_authenticate(request, user=self.user)

        view = OrderProxyView.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sent_payload = mock_post.call_args[1]["json"]
        self.assertEqual(sent_payload["user_id"], 42)

    @patch("apis.views.requests.get")
    def test_order_list_filters_by_user_id(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "user_id": 42}]
        mock_get.return_value = mock_response

        request = self.factory.get("/api/orders/")
        force_authenticate(request, user=self.user)

        view = OrderProxyView.as_view({"get": "list"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get.assert_called_once()
        params = mock_get.call_args[1]["params"]
        self.assertEqual(params.get("user_id"), 42)


class ProductProxyViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = ServiceUser({"user_id": 42, "username": "alice"})

    @patch("apis.views.requests.get")
    def test_product_list_public_access(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "name": "Keyboard", "price": "75.00", "stock": 10}
        ]
        mock_get.return_value = mock_response

        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Keyboard")

    @patch("apis.views.requests.get")
    def test_product_retrieve_public_access(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Keyboard",
            "price": "75.00",
            "stock": 10,
        }
        mock_get.return_value = mock_response

        response = self.client.get("/api/products/1/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Keyboard")
        called_url = mock_get.call_args[0][0]
        self.assertTrue(called_url.endswith("/1/"))

    def test_product_create_requires_auth(self):
        response = self.client.post(
            "/api/products/",
            {"name": "Mouse", "price": "25.00", "stock": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apis.views.requests.post")
    def test_product_create_authenticated(self, mock_post):
        factory = APIRequestFactory()
        request = factory.post(
            "/api/products/",
            {"name": "Mouse", "price": "25.00", "stock": 5},
            format="json",
        )
        force_authenticate(request, user=self.user)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 2,
            "name": "Mouse",
            "price": "25.00",
            "stock": 5,
        }
        mock_post.return_value = mock_response

        view = ProductProxyView.as_view({"post": "create"})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Mouse")
