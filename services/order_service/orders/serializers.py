from decimal import Decimal
from rest_framework import serializers

from .models import Order, OrderItem
from services.product_client import (
    ProductServiceClient,
    ProductClientSerializer,
    ProductStockDeductSerializer,
    ProductStockInjectSerializer,
)


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual order items.
    """

    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    product_id = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ("id", "product_id", "unit_price", "quantity")
        read_only_fields = ("id", "unit_price")


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order including nested items and total amount.
    Product validation logic is handled in views.py.
    """

    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "user_id", "status", "total_amount", "created_at", "items")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {
            "user_id": {"required": True},
            "status": {"required": False},
            "total_amount": {"required": False},
        }

    def validate(self, attrs):
        items = attrs.get("items")
        if items is not None and len(items) == 0:
            raise serializers.ValidationError(
                {"items": "Order must contain at least one item."}
            )
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    items = OrderItemInputSerializer(many=True)
