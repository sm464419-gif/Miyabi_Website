
from decimal import Decimal

from django.conf import settings
from django.db import models


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("mobile_banking", "Mobile Banking"),
    ]

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pos_sales",
    )

    receipt_number = models.CharField(
        max_length=40,
        unique=True,
        blank=True,
    )

    customer_name = models.CharField(
        max_length=120,
        blank=True,
        default="Walk-in customer",
    )

    customer_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    amount_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    change_due = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.receipt_number or f"POS Sale #{self.pk}"


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "app.Product",
        on_delete=models.PROTECT,
        related_name="pos_sale_items",
    )

    product_name = models.CharField(max_length=255)

    quantity = models.PositiveIntegerField()

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
