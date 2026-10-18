
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.apps import apps
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import Sale, SaleItem


CENT = Decimal("0.01")

PAYMENT_METHODS = {
    choice[0] for choice in Sale.PAYMENT_CHOICES
}


def money(value):
    return Decimal(str(value)).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )


def get_product_model():
    # Change this if your product app has another label.
    return apps.get_model("products", "Product")


def selling_price(product):
    normal_price = money(product.price)

    offer = getattr(product, "offer_price", None)

    if offer is not None:
        offer = money(offer)

        if Decimal("0.00") < offer < normal_price:
            return offer

    return normal_price


@staff_member_required
@ensure_csrf_cookie
def dashboard(request):
    today = timezone.localdate()

    todays_sales = Sale.objects.filter(
        created_at__date=today
    )

    context = {
        "today_total": (
            todays_sales.aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0.00")
        ),
        "today_count": todays_sales.count(),
        "recent_sales": Sale.objects.select_related(
            "cashier"
        )[:8],
    }

    return render(
        request,
        "pos/dashboard.html",
        context,
    )


@staff_member_required
@require_GET
def product_search(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"results": []})

    Product = get_product_model()

    products = Product.objects.filter(
        name__icontains=query
    ).order_by("name")[:20]

    results = []

    for product in products:
        stock = int(getattr(product, "stock", 0) or 0)

        results.append({
            "id": product.pk,
            "name": product.name,
            "price": str(selling_price(product)),
            "stock": stock,
            "available": stock > 0,
        })

    return JsonResponse({"results": results})


@staff_member_required
@require_POST
def checkout(request):
    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request data.",
            },
            status=400,
        )

    items = payload.get("items")
    payment_method = payload.get("payment_method")

    customer_name = str(
        payload.get("customer_name") or "Walk-in customer"
    ).strip()[:120]

    customer_phone = str(
        payload.get("customer_phone") or ""
    ).strip()[:30]

    if not isinstance(items, list) or not items:
        return JsonResponse(
            {
                "success": False,
                "error": "Add at least one product.",
            },
            status=400,
        )

    if payment_method not in PAYMENT_METHODS:
        return JsonResponse(
            {
                "success": False,
                "error": "Select a valid payment method.",
            },
            status=400,
        )

    # Combine duplicate products in the submitted cart.
    quantities = defaultdict(int)

    try:
        for row in items:
            product_id = int(row.get("id"))
            quantity = int(row.get("quantity"))

            if (
                product_id <= 0
                or quantity <= 0
                or quantity > 10000
            ):
                raise ValueError

            quantities[product_id] += quantity

    except (AttributeError, TypeError, ValueError):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid product or quantity.",
            },
            status=400,
        )

    try:
        amount_received = money(
            payload.get("amount_received") or "0"
        )

        if amount_received < 0:
            raise InvalidOperation

    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid amount received.",
            },
            status=400,
        )

    Product = get_product_model()

    with transaction.atomic():
        products = {
            product.pk: product
            for product in Product.objects.select_for_update()
            .filter(pk__in=quantities.keys())
            .order_by("pk")
        }

        if len(products) != len(quantities):
            return JsonResponse(
                {
                    "success": False,
                    "error": "One or more products no longer exist.",
                },
                status=400,
            )

        computed_items = []
        total = Decimal("0.00")

        for product_id, quantity in quantities.items():
            product = products[product_id]

            stock = getattr(product, "stock", None)

            if stock is None:
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            "Your Product model needs a stock field "
                            "or the inventory logic must be adapted."
                        ),
                    },
                    status=400,
                )

            if quantity > int(stock):
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            f"Not enough stock for {product.name}. "
                            f"Available: {stock}."
                        ),
                    },
                    status=400,
                )

            unit_price = selling_price(product)
            subtotal = money(unit_price * quantity)

            total += subtotal

            computed_items.append(
                (product, quantity, unit_price, subtotal)
            )

        total = money(total)

        if payment_method == "cash":
            if amount_received < total:
                return JsonResponse(
                    {
                        "success": False,
                        "error": (
                            f"Cash received must be at least ৳{total}."
                        ),
                    },
                    status=400,
                )

            change_due = money(amount_received - total)

        else:
            # Payment-method recording only.
            # This does not process a real electronic payment.
            amount_received = total
            change_due = Decimal("0.00")

        sale = Sale.objects.create(
            cashier=request.user,
            customer_name=customer_name or "Walk-in customer",
            customer_phone=customer_phone,
            payment_method=payment_method,
            total_amount=total,
            amount_received=amount_received,
            change_due=change_due,
        )

        sale.receipt_number = (
            f"MIY-{timezone.localdate():%Y%m%d}-{sale.pk:06d}"
        )

        sale.save(update_fields=["receipt_number"])

        for product, quantity, unit_price, subtotal in computed_items:
            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            )

            product.stock = int(product.stock) - quantity

            product.save(update_fields=["stock"])

    return JsonResponse({
        "success": True,
        "message": "Sale completed successfully.",
        "receipt_url": reverse(
            "pos:receipt",
            args=[sale.pk],
        ),
        "receipt_number": sale.receipt_number,
        "total": str(sale.total_amount),
        "change_due": str(sale.change_due),
    })


@staff_member_required
def receipt(request, sale_id):
    sale = get_object_or_404(
        Sale.objects.select_related(
            "cashier"
        ).prefetch_related("items"),
        pk=sale_id,
    )

    return render(
        request,
        "pos/receipt.html",
        {"sale": sale},
    )


@staff_member_required
def sales_history(request):
    sales = (
        Sale.objects.select_related("cashier")
        .prefetch_related("items")[:100]
    )

    return render(
        request,
        "pos/sales_history.html",
        {"sales": sales},
    )


@staff_member_required
def daily_report(request):
    today = timezone.localdate()

    sales = Sale.objects.filter(
        created_at__date=today
    )

    summary = sales.aggregate(
        total=Sum("total_amount"),
        count=Count("id"),
    )

    by_payment = (
        sales.values("payment_method")
        .annotate(
            count=Count("id"),
            total=Sum("total_amount"),
        )
        .order_by("payment_method")
    )

    payment_labels = dict(Sale.PAYMENT_CHOICES)

    for row in by_payment:
        row["payment_label"] = payment_labels.get(
            row["payment_method"],
            row["payment_method"],
        )

    context = {
        "report_date": today,
        "total": summary["total"] or Decimal("0.00"),
        "count": summary["count"] or 0,
        "by_payment": by_payment,
        "sales": sales.select_related(
            "cashier"
        ).order_by("-created_at"),
    }

    return render(
        request,
        "pos/daily_report.html",
        context,
    )
