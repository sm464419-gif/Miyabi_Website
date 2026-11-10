from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.views.static import serve
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

    # ── Custom admin: products (insert / edit / list / delete) ──
    path('dashboard/products/',                  views.admin_product_list,   name='admin_product_list'),
    path('dashboard/products/add/',              views.admin_product_add,    name='admin_product_add'),
    path('dashboard/products/<int:pk>/edit/',    views.admin_product_edit,   name='admin_product_edit'),
    path('dashboard/products/<int:pk>/delete/',  views.admin_product_delete, name='admin_product_delete'),

    # ── AJAX: chained Category -> Sub Category -> Child Category dropdowns ──
    path('ajax/subcategories/',     views.load_subcategories,     name='load_subcategories'),
    path('ajax/child-categories/',  views.load_child_categories,  name='load_child_categories'),

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
    path('order/',            views.Your_Order,      name='order'),
    path('product/',          views.Product_page,    name='product'),

    # Product detail: old id URL keeps working, new slug URL added.
    # Both share the name 'product_detail' -> {% url 'product_detail' id=... %}
    # and {% url 'product_detail' slug=... %} both reverse correctly.
    path('product/<int:id>',       views.Product_detail, name='product_detail'),
    path('product/<slug:slug>/',   views.Product_detail, name='product_detail'),

    path('about/',             views.about,             name='about'),
    path('privacy-policy/',    views.privacy_policy,    name='privacy_policy'),
    path('terms/',             views.terms,             name='terms'),
    path('shipping-delivery/', views.shipping_delivery, name='shipping_delivery'),
    path('refund-returns/',    views.refund_returns,    name='refund_returns'),

    path('pos/', include('pos.urls')),

    # ── Uploaded media (product images, reels) ──
    # django.conf.urls.static.static() does nothing when DEBUG=False (Render),
    # so media is served explicitly here.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),

]
