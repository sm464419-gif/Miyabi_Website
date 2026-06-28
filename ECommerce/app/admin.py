from django.contrib import admin
from .models import (
    Category, Subcategory, Brand, Product,
    Contact_us, Order, Reel, PolicyPage, SocialLink, Review
)

admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Brand)
admin.site.register(Contact_us)
admin.site.register(Reel)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'subcategory', 'brand', 'price', 'Availability', 'is_popular', 'date')
    list_filter   = ('category', 'brand', 'Availability', 'is_popular')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ('product', 'user', 'price', 'quantity', 'total', 'status', 'date')
    list_editable   = ('status',)
    list_filter     = ('status', 'date')
    search_fields   = ('product', 'user__username', 'phone')
    readonly_fields = ('date',)


@admin.register(PolicyPage)
class PolicyPageAdmin(admin.ModelAdmin):
    list_display    = ('title', 'slug', 'updated')
    readonly_fields = ('updated',)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display  = ('platform', 'url', 'chat_handle', 'show_in_chat', 'order')
    list_editable = ('show_in_chat', 'order')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('product', 'user', 'rating', 'created')
    list_filter   = ('rating',)
    search_fields = ('user__username', 'product__name')