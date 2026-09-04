# order_service/models.py
from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]
    user_id = models.IntegerField()  # Logical reference to user
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.IntegerField()  # Logical reference to Product Service
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot price
    quantity = models.PositiveIntegerField(default=1)
