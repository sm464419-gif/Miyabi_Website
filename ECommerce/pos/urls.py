
from django.urls import path
from . import views

app_name = "pos"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("search/", views.product_search, name="product_search"),
    path("checkout/", views.checkout, name="checkout"),
    path("receipt/<int:sale_id>/", views.receipt, name="receipt"),
    path("sales/", views.sales_history, name="sales_history"),
    path("reports/daily/", views.daily_report, name="daily_report"),
]
