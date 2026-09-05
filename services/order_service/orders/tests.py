from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from orders.models import Order, OrderItem
from orders.serializers import (
    OrderSerializer,
    OrderItemSerializer,
    OrderItemInputSerializer,
    OrderCreateSerializer,
    ProductClientSerializer,
    ProductStockDeductSerializer,
    ProductStockInjectSerializer,
)
from orders.utils import validate_order_products
from services.product_client import ProductServiceClient, StockInjectionSerializer


class SerializersTestCase(TestCase):
    def test_product_client_serializer_valid(self):
        data = {
            "id": 1,
            "name": "Wireless Mouse",
            "description": "Ergonomic wireless mouse",
            "price": "29.99",
            "stock": 50,
        }
        serializer = ProductClientSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["price"], Decimal("29.99"))
        self.assertEqual(serializer.validated_data["stock"], 50)

    def test_product_client_serializer_invalid_stock(self):
        data = {
            "id": 1,
            "name": "Wireless Mouse",
            "price": "29.99",
            "stock": -5,
        }
        serializer = ProductClientSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("stock", serializer.errors)

    def test_stock_deduct_serializer_valid(self):
        serializer = ProductStockDeductSerializer(data={"quantity": 3})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["quantity"], 3)

    def test_stock_deduct_serializer_invalid_quantity(self):
        serializer = ProductStockDeductSerializer(data={"quantity": 0})
        self.assertFalse(serializer.is_valid())

    def test_stock_inject_serializer_valid(self):
        serializer = ProductStockInjectSerializer(data={"quantity": 10})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["quantity"], 10)
        self.assertIs(StockInjectionSerializer, ProductStockInjectSerializer)

    def test_stock_inject_serializer_invalid_quantity(self):
        serializer = ProductStockInjectSerializer(data={"quantity": -1})
        self.assertFalse(serializer.is_valid())

    def test_order_item_serializer(self):
        item_data = {
            "product_id": 10,
            "quantity": 2,
        }
        serializer = OrderItemSerializer(data=item_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["quantity"], 2)

    def test_order_serializer_basic_validation(self):
        order_data = {
            "user_id": 42,
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1},
            ],
        }
        serializer = OrderSerializer(data=order_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_order_serializer_empty_items(self):
        order_data = {
            "user_id": 1,
            "items": [],
        }
        serializer = OrderSerializer(data=order_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("items", serializer.errors)

    def test_order_create_serializer(self):
        input_serializer = OrderItemInputSerializer(
            data={"product_id": 1, "quantity": 2}
        )
        self.assertTrue(input_serializer.is_valid())

        create_serializer = OrderCreateSerializer(
            data={
                "user_id": 1,
                "items": [{"product_id": 1, "quantity": 2}],
            }
        )
        self.assertTrue(create_serializer.is_valid())


class ViewsAndUrlsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch.object(ProductServiceClient, "deduct_stock")
    @patch.object(ProductServiceClient, "get_product")
    def test_create_order_view_success(self, mock_get_product, mock_deduct_stock):
        mock_get_product.return_value = {
            "id": 100,
            "name": "Keyboard",
            "price": Decimal("75.00"),
            "stock": 10,
        }
        mock_deduct_stock.return_value = True

        payload = {
            "user_id": 99,
            "items": [
                {"product_id": 100, "quantity": 2},
            ],
        }
        response = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(str(response.data["total_amount"])), Decimal("150.00"))

        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user_id, 99)
        self.assertEqual(order.total_amount, Decimal("150.00"))
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.unit_price, Decimal("75.00"))
        self.assertEqual(item.quantity, 2)

    @patch.object(ProductServiceClient, "get_product")
    def test_create_order_insufficient_stock(self, mock_get_product):
        mock_get_product.return_value = {
            "id": 100,
            "name": "Keyboard",
            "price": Decimal("75.00"),
            "stock": 1,
        }

        payload = {
            "user_id": 99,
            "items": [
                {"product_id": 100, "quantity": 5},
            ],
        }
        response = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    @patch.object(ProductServiceClient, "get_product")
    def test_create_order_product_not_found(self, mock_get_product):
        mock_get_product.return_value = None

        payload = {
            "user_id": 99,
            "items": [
                {"product_id": 999, "quantity": 1},
            ],
        }
        response = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_create_order_empty_items(self):
        payload = {
            "user_id": 99,
            "items": [],
        }
        response = self.client.post("/api/orders/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_and_retrieve_orders(self):
        order = Order.objects.create(user_id=10, total_amount=Decimal("50.00"))
        OrderItem.objects.create(
            order=order, product_id=1, quantity=2, unit_price=Decimal("25.00")
        )

        list_response = self.client.get("/api/orders/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

        detail_response = self.client.get(f"/api/orders/{order.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["user_id"], 10)


class ProductClientTestCase(TestCase):
    @patch("services.product_client.requests.get")
    def test_product_client_get_product_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Headphones",
            "price": "99.99",
            "stock": 15,
        }
        mock_get.return_value = mock_response

        client = ProductServiceClient(base_url="http://mock-product-service")
        product = client.get_product(1)
        self.assertIsNotNone(product)
        self.assertEqual(product["name"], "Headphones")
        self.assertEqual(product["price"], Decimal("99.99"))

    @patch("services.product_client.requests.get")
    def test_product_client_get_product_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = ProductServiceClient(base_url="http://mock-product-service")
        product = client.get_product(999)
        self.assertIsNone(product)

    @patch("services.product_client.requests.put")
    def test_product_client_deduct_stock_success(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        client = ProductServiceClient(base_url="http://mock-product-service")
        result = client.deduct_stock(1, 2)
        self.assertTrue(result)

    @patch("services.product_client.requests.put")
    def test_product_client_deduct_stock_failure(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_put.return_value = mock_response

        client = ProductServiceClient(base_url="http://mock-product-service")
        result = client.deduct_stock(1, 999)
        self.assertFalse(result)

    @patch("services.product_client.requests.put")
    def test_product_client_inject_stock_success(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        client = ProductServiceClient(base_url="http://mock-product-service")
        result = client.inject_stock(1, 5)
        self.assertTrue(result)
        self.assertIsInstance(result, bool)

    @patch("services.product_client.requests.put")
    def test_product_client_inject_stock_failure(self, mock_put):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_put.return_value = mock_response

        client = ProductServiceClient(base_url="http://mock-product-service")
        result = client.inject_stock(1, 5)
        self.assertFalse(result)
        self.assertIsInstance(result, bool)
