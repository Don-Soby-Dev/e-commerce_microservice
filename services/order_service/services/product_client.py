import requests
from django.conf import settings


class ProductServiceClient:
    def __init__(self, base_url=None, timeout=3.0):
        self.base_url = base_url or settings.PRODUCT_SERVICE_URL
        self.timeout = timeout

    def get_product(self, product_id):
        # Calls GET /api/products/{id}/
        pass

    def deduct_stock(self, product_id, qty):
        # Calls PUT /api/product/{id}/deduct
        pass
