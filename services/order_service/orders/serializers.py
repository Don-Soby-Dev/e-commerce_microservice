from rest_framework import serializers


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    items = OrderItemInputSerializer(many=True)
