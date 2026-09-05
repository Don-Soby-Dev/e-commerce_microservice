from services.product_client import ProductServiceClient, ProductClientSerializer
from decimal import Decimal


def validate_order_products(items_data, product_client=None):
    """
    Helper function to validate products with ProductServiceClient.
    Checks product existence, stock availability, and calculates item unit prices and total amount.
    Returns (processed_items, total_amount, error_dict).
    """
    if not items_data:
        return None, None, {"items": "Order must contain at least one item."}

    if product_client is None:
        product_client = ProductServiceClient()

    total_amount = Decimal("0.00")
    processed_items = []

    for item in items_data:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)

        product_data = product_client.get_product(product_id)
        if not product_data:
            return (
                None,
                None,
                {
                    "items": f"Product with ID {product_id} not found or Product Service is unreachable."
                },
            )

        # Validate product payload structure if necessary
        prod_serializer = ProductClientSerializer(data=product_data)
        if prod_serializer.is_valid():
            product_data = prod_serializer.validated_data

        stock = product_data.get("stock", 0)
        if stock < quantity:
            return (
                None,
                None,
                {
                    "items": f"Insufficient stock for product {product_id}. Available: {stock}, requested: {quantity}."
                },
            )

        unit_price = Decimal(str(product_data["price"]))

        total_amount += unit_price * quantity
        processed_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
            }
        )

    return processed_items, total_amount, None


def deduct_product_stock(product_id, quantity, product_client=None):

    if product_client is None:
        product_client = ProductServiceClient()

    is_deducted = product_client.deduct_stock(product_id, quantity)

    if not is_deducted:
        return (
            is_deducted,
            {
                "item": f"Product with ID {product_id} not found or Product Service is unreachable."
            },
        )

    return is_deducted, None


def inject_product_stock(product_id, quantity, product_client=None):

    if product_client is None:
        product_client = ProductServiceClient()

    is_injected = product_client.inject_stock(product_id, quantity)

    if not is_injected:
        return (
            is_injected,
            {
                "item": f"Product with ID {product_id} not found or Product Service is unreachable."
            },
        )

    return is_injected, None
