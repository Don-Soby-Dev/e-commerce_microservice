from decimal import Decimal
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Product
from .serializers import ProductSerializer, StockAdjustmentSerializer


class ProductSerializerTestCase(TestCase):
    def test_product_serializer_valid(self):
        data = {
            "name": "Mechanical Keyboard",
            "description": "RGB backlit mechanical keyboard",
            "price": "89.99",
            "stock": 25,
        }
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        product = serializer.save()
        self.assertEqual(product.name, "Mechanical Keyboard")
        self.assertEqual(product.price, Decimal("89.99"))
        self.assertEqual(product.stock, 25)

    def test_stock_adjustment_serializer_valid(self):
        serializer = StockAdjustmentSerializer(data={"quantity": 5})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["quantity"], 5)

    def test_stock_adjustment_serializer_invalid_quantity(self):
        serializer_zero = StockAdjustmentSerializer(data={"quantity": 0})
        self.assertFalse(serializer_zero.is_valid())
        self.assertIn("quantity", serializer_zero.errors)

        serializer_negative = StockAdjustmentSerializer(data={"quantity": -3})
        self.assertFalse(serializer_negative.is_valid())
        self.assertIn("quantity", serializer_negative.errors)

    def test_stock_adjustment_serializer_missing_quantity(self):
        serializer = StockAdjustmentSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)


class ProductViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            name="Gaming Mouse",
            description="High precision optical gaming mouse",
            price=Decimal("49.99"),
            stock=20,
        )

    def test_list_products(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Gaming Mouse")

    def test_create_product(self):
        payload = {
            "name": "USB-C Hub",
            "description": "7-in-1 multi-port adapter",
            "price": "34.50",
            "stock": 15,
        }
        response = self.client.post("/api/products/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "USB-C Hub")
        self.assertEqual(Decimal(str(response.data["price"])), Decimal("34.50"))
        self.assertEqual(response.data["stock"], 15)

    def test_retrieve_product(self):
        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.product.id)
        self.assertEqual(response.data["name"], "Gaming Mouse")
        self.assertEqual(Decimal(str(response.data["price"])), Decimal("49.99"))
        self.assertEqual(response.data["stock"], 20)

    def test_retrieve_product_not_found(self):
        response = self.client.get("/api/products/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        payload = {
            "name": "Gaming Mouse Pro",
            "description": "Updated description",
            "price": "59.99",
            "stock": 18,
        }
        response = self.client.put(
            f"/api/products/{self.product.id}/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Gaming Mouse Pro")
        self.assertEqual(self.product.price, Decimal("59.99"))

    def test_partial_update_product(self):
        payload = {"stock": 30}
        response = self.client.patch(
            f"/api/products/{self.product.id}/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 30)

    def test_delete_product(self):
        response = self.client.delete(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_deduct_stock_success(self):
        payload = {"quantity": 5}
        response = self.client.put(
            f"/api/products/{self.product.id}/deduct/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 15)
        self.assertEqual(response.data["stock"], 15)

    def test_deduct_stock_with_post_method(self):
        payload = {"quantity": 3}
        response = self.client.post(
            f"/api/products/{self.product.id}/deduct/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 17)

    def test_deduct_stock_exact_amount(self):
        payload = {"quantity": 20}
        response = self.client.put(
            f"/api/products/{self.product.id}/deduct/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)

    def test_deduct_stock_insufficient(self):
        payload = {"quantity": 25}
        response = self.client.put(
            f"/api/products/{self.product.id}/deduct/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 20)

    def test_deduct_stock_invalid_quantity(self):
        payload = {"quantity": 0}
        response = self.client.put(
            f"/api/products/{self.product.id}/deduct/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 20)

    def test_deduct_stock_product_not_found(self):
        payload = {"quantity": 2}
        response = self.client.put(
            "/api/products/99999/deduct/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inject_stock_success(self):
        payload = {"quantity": 10}
        response = self.client.put(
            f"/api/products/{self.product.id}/inject/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 30)
        self.assertEqual(response.data["stock"], 30)

    def test_inject_stock_with_post_method(self):
        payload = {"quantity": 5}
        response = self.client.post(
            f"/api/products/{self.product.id}/inject/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 25)

    def test_inject_stock_invalid_quantity(self):
        payload = {"quantity": -5}
        response = self.client.put(
            f"/api/products/{self.product.id}/inject/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 20)

    def test_inject_stock_product_not_found(self):
        payload = {"quantity": 5}
        response = self.client.put(
            "/api/products/99999/inject/", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductServiceClientCompatibilityTestCase(TestCase):
    """
    Validates that the responses from Product Service match the expectations
    of ProductServiceClient in order_service.
    """

    def setUp(self):
        self.client = APIClient()
        self.product = Product.objects.create(
            name="Wireless Mouse",
            description="Ergonomic mouse",
            price=Decimal("29.99"),
            stock=10,
        )

    def test_get_product_contract(self):
        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["id"], self.product.id)
        self.assertEqual(data["name"], "Wireless Mouse")
        self.assertEqual(data["description"], "Ergonomic mouse")
        self.assertEqual(data["price"], "29.99")
        self.assertEqual(data["stock"], 10)
        self.assertIn("created_at", data)

    def test_deduct_stock_contract(self):
        response = self.client.put(
            f"/api/products/{self.product.id}/deduct/",
            {"quantity": 4},
            format="json",
        )
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 6)

    def test_inject_stock_contract(self):
        response = self.client.put(
            f"/api/products/{self.product.id}/inject/",
            {"quantity": 4},
            format="json",
        )
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 14)

