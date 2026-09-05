from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer, StockAdjustmentSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing, creating, updating, and deleting products,
    as well as managing product stock (deduction and injection).
    """

    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer

    @action(detail=True, methods=["put", "post"], url_path="deduct")
    def deduct_stock(self, request, pk=None):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            product = Product.objects.select_for_update().filter(pk=pk).first()
            if not product:
                return Response(
                    {"detail": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if product.stock < quantity:
                return Response(
                    {
                        "error": "Insufficient stock.",
                        "available_stock": product.stock,
                        "requested_quantity": quantity,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.stock -= quantity
            product.save()

        return Response(
            {
                "detail": "Stock deducted successfully.",
                "product_id": product.id,
                "stock": product.stock,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["put", "post"], url_path="inject")
    def inject_stock(self, request, pk=None):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quantity = serializer.validated_data["quantity"]

        with transaction.atomic():
            product = Product.objects.select_for_update().filter(pk=pk).first()
            if not product:
                return Response(
                    {"detail": "Product not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            product.stock += quantity
            product.save()

        return Response(
            {
                "detail": "Stock injected successfully.",
                "product_id": product.id,
                "stock": product.stock,
            },
            status=status.HTTP_200_OK,
        )
