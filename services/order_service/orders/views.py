from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import OrderSerializer
from services.product_client import ProductServiceClient
from .utils import validate_order_products, deduct_product_stock, inject_product_stock


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating orders.
    Product validation and price/stock checks are handled here.
    """

    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        items_data = request.data.get("items", [])
        product_client = ProductServiceClient()

        # Validate products using ProductServiceClient
        processed_items, total_amount, error = validate_order_products(
            items_data, product_client=product_client
        )
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # Create Order instance
        user_id = validated_data["user_id"]
        order_status = validated_data.get("status", "PENDING")

        order = Order.objects.create(
            user_id=user_id,
            status=order_status,
            total_amount=total_amount,
        )

        deducted_items = []
        for item in processed_items:
            OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )

            is_deducted, error = deduct_product_stock(
                item["product_id"],
                quantity=item["quantity"],
                product_client=product_client,
            )
            if not is_deducted:
                # Rollback stock for previously deducted items
                for prev_item in deducted_items:
                    inject_product_stock(
                        prev_item["product_id"],
                        quantity=prev_item["quantity"],
                        product_client=product_client,
                    )
                order.delete()
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            
            deducted_items.append(item)

        output_serializer = self.get_serializer(order)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
