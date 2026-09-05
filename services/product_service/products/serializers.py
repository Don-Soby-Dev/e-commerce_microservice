from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model supporting full CRUD operations.
    """

    class Meta:
        model = Product
        fields = ("id", "name", "description", "price", "stock", "created_at")
        read_only_fields = ("id", "created_at")


class StockAdjustmentSerializer(serializers.Serializer):
    """
    Serializer for stock deduction and injection requests.
    """

    quantity = serializers.IntegerField(min_value=1)
    product_id = serializers.IntegerField(min_value=1, required=False)
