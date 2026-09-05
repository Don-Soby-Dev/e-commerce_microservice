import requests
from django.conf import settings
from rest_framework import serializers


class ProductClientSerializer(serializers.Serializer):
    """
    Serializer for product data returned from or sent to the Product Service.
    """

    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(min_value=0, default=0)
    created_at = serializers.DateTimeField(required=False)


# Aliases for convenience
ProductSerializer = ProductClientSerializer
ProductResponseSerializer = ProductClientSerializer


class ProductStockDeductSerializer(serializers.Serializer):
    """
    Serializer for stock deduction requests to the Product Service.
    """

    product_id = serializers.IntegerField(min_value=1, required=False)
    quantity = serializers.IntegerField(min_value=1)


# Alias for convenience
StockDeductionSerializer = ProductStockDeductSerializer


class ProductStockInjectSerializer(serializers.Serializer):
    """
    Serializer for stock injection requests to the Product Service.
    """

    product_id = serializers.IntegerField(min_value=1, required=False)
    quantity = serializers.IntegerField(min_value=1)


# Alias for convenience
StockInjectionSerializer = ProductStockInjectSerializer


class ProductServiceClient:
    def __init__(self, base_url=None, timeout=3.0):
        self.base_url = (
            base_url
            or getattr(settings, "PRODUCT_SERVICE_URL", "http://localhost:8001")
        ).rstrip("/")
        self.timeout = timeout

    def get_product(self, product_id):
        """
        Calls GET /api/products/{id}/
        Fetches product details from the Product Service and validates the response.
        """
        url = f"{self.base_url}/api/products/{product_id}/"
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                serializer = ProductClientSerializer(data=response.json())
                if serializer.is_valid():
                    return serializer.validated_data
                return response.json()
            elif response.status_code == 404:
                return None
            response.raise_for_status()
        except requests.RequestException:
            return None
        return None

    def deduct_stock(self, product_id, qty):
        """
        Calls PUT /api/products/{id}/deduct/
        Deducts stock for the given product in the Product Service.
        """
        serializer = ProductStockDeductSerializer(
            data={"product_id": product_id, "quantity": qty}
        )
        serializer.is_valid(raise_exception=True)
        url = f"{self.base_url}/api/products/{product_id}/deduct/"
        try:
            response = requests.put(url, json={"quantity": qty}, timeout=self.timeout)
            return response.status_code in (200, 204)
        except requests.RequestException:
            return False

    def inject_stock(self, product_id, qty):
        """
        Calls PUT /api/products/{id}/inject/
        Injects/adds stock for the given product in the Product Service.
        Returns True if successful, False otherwise.
        """
        serializer = ProductStockInjectSerializer(
            data={"product_id": product_id, "quantity": qty}
        )
        serializer.is_valid(raise_exception=True)
        url = f"{self.base_url}/api/products/{product_id}/inject/"
        try:
            response = requests.put(url, json={"quantity": qty}, timeout=self.timeout)
            return response.status_code in (200, 204)
        except requests.RequestException:
            return False