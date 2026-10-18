from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from . import views


# ── Redirect /admin/ to custom dashboard for staff ──
def admin_redirect(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('/admin/login/')


cart_urlpatterns = ([
    path('add/<int:id>/',            views.cart_add,       name='cart_add'),
    path('item_clear/<int:id>/',     views.item_clear,     name='item_clear'),
    path('item_increment/<int:id>/', views.item_increment, name='item_increment'),
    path('item_decrement/<int:id>/', views.item_decrement, name='item_decrement'),
    path('cart_clear/',              views.cart_clear,     name='cart_clear'),
    path('cart_detail/',             views.cart_detail,    name='cart_detail'),
    path('apply-coupon/',            views.apply_coupon,   name='apply_coupon'),
    path('remove-coupon/',           views.remove_coupon,  name='remove_coupon'),
], 'cart')


urlpatterns = [

    # ── Custom admin dashboard ──
    path('dashboard/',        views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/orders/', views.admin_orders,    name='admin_orders'),

    # ── Django built-in admin (keep for superuser raw access) ──
    # IMPORTANT: must come AFTER dashboard paths
    path('admin/', admin_redirect),           # ← redirects to dashboard
    path('admin/portal/', admin.site.urls),   # ← real Django admin at new URL

    path('base/', views.Base, name='base'),
    path('', views.Index, name='index'),
    path('signup', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('account/',          views.account,         name='account'),
    path('account/edit/',     views.account_edit,    name='account_edit'),
    path('account/password/', views.change_password, name='change_password'),
    path('account/email/',    views.change_email,    name='change_email'),

    path('cart/', include(cart_urlpatterns)),

    path('contact_us',        views.Contact_Page,    name='contact_page'),
    path('checkout/',         views.Checkout,        name='checkout'),
    path('order/',            views.Your_Order,       name='order'),
    path('product/',          views.Product_page,    name='product'),
    path('product/<str:id>',  views.Product_detail,  name='product_detail'),

    path('about/',             views.about,             name='about'),
    path('privacy-policy/',    views.privacy_policy,    name='privacy_policy'),
    path('terms/',             views.terms,             name='terms'),
    path('shipping-delivery/', views.shipping_delivery, name='shipping_delivery'),
    path('refund-returns/',    views.refund_returns,    name='refund_returns'),
                  path("pos/", include("pos.urls")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)