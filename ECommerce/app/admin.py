from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Subcategory, ChildCategory, Concern, Brand, Product,
    ProductImage, ProductVariant,
    Contact_us, Order, Reel, PolicyPage,
    SocialLink, Review, Coupon, Supplier,
    SMSPromotion, LandingPage, Attribute, AttributeValue
)


# ════════════════════════════════════════════════
#  CATEGORY / SUBCATEGORY / CHILD CATEGORY / CONCERN / BRAND
# ════════════════════════════════════════════════
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category')
    list_filter   = ('category',)
    search_fields = ('name',)


@admin.register(ChildCategory)
class ChildCategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'subcategory', 'get_category')
    list_filter   = ('subcategory__category', 'subcategory')
    search_fields = ('name',)

    def get_category(self, obj):
        return obj.subcategory.category
    get_category.short_description = 'Category'


@admin.register(Concern)
class ConcernAdmin(admin.ModelAdmin):
    list_display  = ('name',)
    search_fields = ('name',)


admin.site.register(Brand)
admin.site.register(Contact_us)
admin.site.register(Reel)


# ════════════════════════════════════════════════
#  PRODUCT  (with gallery images + variants inline)
# ════════════════════════════════════════════════
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model             = ProductVariant
    extra             = 0
    filter_horizontal = ('values',)
    fields            = ('values', 'sku', 'price', 'quantity', 'image')


class ProductAdminForm(forms.ModelForm):
    # Bullet points as a plain textarea: one point per line (stored as a list)
    bullet_points = forms.CharField(
        required=False,
        label='Bullet points',
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text='One bullet point per line.',
    )

    class Meta:
        model  = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        points = (self.instance.bullet_points or []) if self.instance.pk else []
        if points:
            self.initial['bullet_points'] = '\n'.join(points)

    def clean_bullet_points(self):
        text = self.cleaned_data.get('bullet_points') or ''
        return [line.strip() for line in text.splitlines() if line.strip()]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form          = ProductAdminForm
    list_display  = ('name', 'code', 'category', 'subcategory', 'child_category',
                     'brand', 'price', 'previous_price', 'discount_badge',
                     'quantity', 'Availability', 'is_popular', 'date')
    list_filter   = ('category', 'subcategory', 'brand', 'concern',
                     'Availability', 'is_popular')
    list_editable = ('previous_price', 'is_popular')
    search_fields = ('name', 'code', 'tags')
    readonly_fields     = ('date',)
    prepopulated_fields = {'slug': ('name',)}
    inlines       = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'code')
        }),
        ('Classification', {
            'fields': ('category', 'subcategory', 'child_category',
                       'brand', 'concern')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'previous_price', 'weight',
                       'stock_option', 'quantity', 'Availability')
        }),
        ('Media', {
            'fields': ('image', 'video_host', 'video_file', 'video_url')
        }),
        ('Content', {
            'fields': ('bullet_points', 'tags', 'description',
                       'ingredients', 'how_to_use')
        }),
        ('Flags', {
            'fields': ('is_popular', 'date')
        }),
    )

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
                       'total', 'coupon', 'coupon_discount', 'status', 'date')
    list_editable   = ('status',)
    list_filter     = ('status', 'date')
    search_fields   = ('product', 'user__username', 'phone')
    readonly_fields = ('date',)

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
#  ATTRIBUTE / ATTRIBUTE VALUE
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
#  PRODUCT VARIANT (standalone view)
# ════════════════════════════════════════════════
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display      = ('product', 'variant_values', 'sku', 'price', 'quantity')
    list_filter       = ('product__category',)
    search_fields     = ('product__name', 'sku')
    filter_horizontal = ('values',)

    def variant_values(self, obj):
        return ", ".join(str(v.value) for v in obj.values.all()) or '—'
    variant_values.short_description = 'Options'


# ════════════════════════════════════════════════
#  ADMIN SITE CUSTOMISATION
# ════════════════════════════════════════════════
admin.site.site_header  = 'Miyabi Admin'
admin.site.site_title   = 'Miyabi Admin Portal'
admin.site.index_title  = 'Welcome to Miyabi Dashboard'