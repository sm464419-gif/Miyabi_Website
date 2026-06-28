import requests
from django.conf import settings


def create_steadfast_order(order):

    url = "https://portal.packzy.com/api/v1/create_order"

    payload = {
        "invoice": f"INV-{order.id}",
        "recipient_name": order.user.username,
        "recipient_phone": order.phone,
        "recipient_address": order.address,
        "cod_amount": order.total,
        "note": "Ecommerce Order"
    }

    headers = {
        "Api-Key": settings.STEADFAST_API_KEY,
        "Secret-Key": settings.STEADFAST_SECRET_KEY,
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        return response.json()

    except requests.exceptions.RequestException as e:

        return {
            "status": "error",
            "message": str(e)
        }