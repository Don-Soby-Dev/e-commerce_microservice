from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.username = "testuser"
        self.email = "testuser@example.com"
        self.password = "SecurePassword123!"
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
        )

    def test_register_success(self):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SuperStrongPassword123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post("/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)
        self.assertEqual(len(data["data"]), 1)

        result_item = data["data"][0]
        self.assertIn("refresh_token", result_item)
        self.assertIn("access_token", result_item)
        self.assertIn("user", result_item)
        self.assertEqual(result_item["user"]["username"], "newuser")
        self.assertEqual(result_item["user"]["email"], "newuser@example.com")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_duplicate_username(self):
        payload = {
            "username": self.username,
            "email": "duplicate@example.com",
            "password": "Password123!",
        }
        response = self.client.post("/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("errors", data)
        self.assertIn("username", data["errors"])

    def test_register_missing_fields(self):
        payload = {"username": "missingpassword"}
        response = self.client.post("/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("password", data["errors"])

    def test_login_success(self):
        payload = {
            "username": self.username,
            "password": self.password,
        }
        response = self.client.post("/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)
        self.assertEqual(len(data["data"]), 1)

        result_item = data["data"][0]
        self.assertIn("refresh_token", result_item)
        self.assertIn("access_token", result_item)
        self.assertEqual(result_item["user"]["username"], self.username)

    def test_login_invalid_password(self):
        payload = {
            "username": self.username,
            "password": "WrongPassword123",
        }
        response = self.client.post("/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertFalse(data.get("success"))
        self.assertIn("errors", data)

    def test_login_nonexistent_user(self):
        payload = {
            "username": "nouserhere",
            "password": "SomePassword123",
        }
        response = self.client.post("/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertFalse(data.get("success"))

    def test_login_disabled_account(self):
        self.user.is_active = False
        self.user.save()
        payload = {
            "username": self.username,
            "password": self.password,
        }
        response = self.client.post("/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertFalse(data.get("success"))

    def test_refresh_token_success_with_refresh_token_key(self):
        refresh = RefreshToken.for_user(self.user)
        payload = {"refresh_token": str(refresh)}
        response = self.client.post("/refresh/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)
        self.assertEqual(len(data["data"]), 1)
        self.assertIn("access_token", data["data"][0])
        self.assertIn("refresh_token", data["data"][0])

    def test_refresh_token_success_with_refresh_key(self):
        refresh = RefreshToken.for_user(self.user)
        payload = {"refresh": str(refresh)}
        response = self.client.post("/refresh/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("access_token", data["data"][0])

    def test_refresh_token_invalid(self):
        payload = {"refresh_token": "invalid.token.value"}
        response = self.client.post("/refresh/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertFalse(data.get("success"))

    def test_refresh_token_missing(self):
        payload = {}
        response = self.client.post("/refresh/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertFalse(data.get("success"))

    def test_api_auth_prefixed_routes(self):
        # Verify /api/auth/login/ route
        login_res = self.client.post(
            "/api/auth/login/",
            {"username": self.username, "password": self.password},
            format="json",
        )
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertTrue(login_res.json()["success"])

        # Verify /api/auth/register/ route
        reg_res = self.client.post(
            "/api/auth/register/",
            {"username": "apiuser", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(reg_res.json()["success"])
