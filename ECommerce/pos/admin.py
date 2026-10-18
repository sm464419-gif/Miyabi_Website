
from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    can_delete = False

    readonly_fields = (
        "product",
        "product_name",
        "quantity",
        "unit_price",
        "subtotal",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "customer_name",
        "payment_method",
        "total_amount",
        "cashier",
        "created_at",
    )

    list_filter = (
        "payment_method",
        "created_at",
    )

    search_fields = (
        "receipt_number",
        "customer_name",
        "customer_phone",
        "cashier__username",
    )

    readonly_fields = (
        "cashier",
        "receipt_number",
        "customer_name",
        "customer_phone",
        "payment_method",
        "total_amount",
        "amount_received",
        "change_due",
        "created_at",
    )

    inlines = [SaleItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
