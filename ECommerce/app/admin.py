from django.contrib import admin
from django.db.models import Sum, Count
from django.utils.html import format_html
from .models import (
    Category, Subcategory, Brand, Product,
    Contact_us, Order, Reel, PolicyPage,
    SocialLink, Review, Coupon, Supplier,
    SMSPromotion, LandingPage, Attribute, AttributeValue
)


# ════════════════════════════════════════════════
#  CATEGORY / SUBCATEGORY / BRAND
# ════════════════════════════════════════════════
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Brand)
admin.site.register(Contact_us)
admin.site.register(Reel)


# ════════════════════════════════════════════════
#  PRODUCT
# ════════════════════════════════════════════════
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'subcategory', 'brand',
                     'price', 'offer_price', 'discount_badge',
                     'Availability', 'is_popular', 'date')
    list_filter   = ('category', 'brand', 'Availability', 'is_popular')
    list_editable = ('offer_price', 'is_popular')
    search_fields = ('name',)

    def discount_badge(self, obj):
        pct = obj.discount_percent
        if pct:
            return format_html(
                '<span style="background:#7B2CBF;color:#fff;'
                'padding:2px 8px;border-radius:12px;font-size:11px;">'
                '{}% OFF</span>', pct
            )
        return '—'
    discount_badge.short_description = 'Discount'


# ════════════════════════════════════════════════
#  COUPON
# ════════════════════════════════════════════════
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ('code', 'discount_type', 'discount', 'minimum_amount',
                     'valid_from', 'valid_to', 'usage_limit', 'used_count',
                     'is_active', 'status_badge')
    list_filter   = ('is_active', 'discount_type')
    list_editable = ('is_active',)
    search_fields = ('code',)
    readonly_fields = ('used_count',)

    def status_badge(self, obj):
        if obj.is_valid():
            return format_html(
                '<span style="background:#27ae60;color:#fff;'
                'padding:2px 10px;border-radius:12px;font-size:11px;">Valid</span>'
            )
        return format_html(
            '<span style="background:#e74c3c;color:#fff;'
            'padding:2px 10px;border-radius:12px;font-size:11px;">Expired/Inactive</span>'
        )
    status_badge.short_description = 'Status'


# ════════════════════════════════════════════════
#  ORDER
# ════════════════════════════════════════════════
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ('id', 'product', 'user', 'price', 'quantity',
                       'total', 'coupon', 'coupon_discount',
                       'status_badge', 'date')
    list_editable   = ('status',)
    list_filter     = ('status', 'date')
    search_fields   = ('product', 'user__username', 'phone')
    readonly_fields = ('date',)

    # override list_display to include status for list_editable
    list_display = ('id', 'product', 'user', 'price', 'quantity',
                    'total', 'coupon', 'coupon_discount', 'status', 'date')

    def status_badge(self, obj):
        colours = {
            'ordered':          '#3498db',
            'processing':       '#f39c12',
            'shipped':          '#8e44ad',
            'on_delivery':      '#e67e22',
            'partial_delivery': '#d35400',
            'delivered':        '#27ae60',
            'cancelled':        '#e74c3c',
            'returned':         '#7f8c8d',
        }
        colour = colours.get(obj.status, '#999')
        return format_html(
            '<span style="background:{};color:#fff;'
            'padding:2px 10px;border-radius:12px;font-size:11px;">{}</span>',
            colour, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ════════════════════════════════════════════════
#  POLICY PAGE
# ════════════════════════════════════════════════
@admin.register(PolicyPage)
class PolicyPageAdmin(admin.ModelAdmin):
    list_display    = ('title', 'slug', 'updated')
    readonly_fields = ('updated',)


# ════════════════════════════════════════════════
#  SOCIAL LINK
# ════════════════════════════════════════════════
@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display  = ('platform', 'url', 'chat_handle', 'show_in_chat', 'order')
    list_editable = ('show_in_chat', 'order')


# ════════════════════════════════════════════════
#  REVIEW
# ════════════════════════════════════════════════
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('product', 'user', 'rating', 'created')
    list_filter   = ('rating',)
    search_fields = ('user__username', 'product__name')


# ════════════════════════════════════════════════
#  SUPPLIER
# ════════════════════════════════════════════════
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display  = ('name', 'phone', 'email', 'address')
    search_fields = ('name', 'phone', 'email')


# ════════════════════════════════════════════════
#  SMS PROMOTION
# ════════════════════════════════════════════════
@admin.register(SMSPromotion)
class SMSPromotionAdmin(admin.ModelAdmin):
    list_display  = ('title', 'is_sent', 'sent_at')
    list_filter   = ('is_sent',)
    search_fields = ('title',)


# ════════════════════════════════════════════════
#  LANDING PAGE
# ════════════════════════════════════════════════
@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display        = ('title', 'slug', 'is_active', 'created_at')
    list_editable       = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields       = ('title',)


# ════════════════════════════════════════════════
#  ATTRIBUTE
# ════════════════════════════════════════════════
class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 2

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines      = [AttributeValueInline]

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display  = ('attribute', 'value')
    list_filter   = ('attribute',)
    search_fields = ('value',)


# ════════════════════════════════════════════════
#  ADMIN SITE CUSTOMISATION
# ════════════════════════════════════════════════
admin.site.site_header  = 'Miyabi Admin'
admin.site.site_title   = 'Miyabi Admin Portal'
admin.site.index_title  = 'Welcome to Miyabi Dashboard'