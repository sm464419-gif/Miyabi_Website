import datetime
import random

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify


# ═════════════════════════════════════════════
#  Catalog structure
# ═════════════════════════════════════════════
class Category(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name     = models.CharField(max_length=150)
    # NOTE: renamed from "Category" -> "category" (update views/templates accordingly)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


# ── NEW: Child Category ──
class ChildCategory(models.Model):
    name        = models.CharField(max_length=150)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE,
                                    related_name='child_categories')

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


# ── NEW: Concern (skin concern dropdown) ──
class Concern(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


# ═════════════════════════════════════════════
#  Product Attributes (Color, Size, Weight ...)
# ═════════════════════════════════════════════
class Attribute(models.Model):
    name = models.CharField(max_length=100)  # e.g. Color, Size

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE,
                                  related_name='values')
    value     = models.CharField(max_length=100)  # e.g. Red, XL

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ═════════════════════════════════════════════
#  Product
# ═════════════════════════════════════════════
def generate_product_code():
    """Random unique 6-digit product code (like 759690)."""
    while True:
        code = str(random.randint(100000, 999999))
        if not Product.objects.filter(code=code).exists():
            return code


class Product(models.Model):
    AVAILABILITY_CHOICES = (('In Stock', 'In Stock'), ('Out of Stock', 'Out of Stock'))
    STOCK_OPTION_CHOICES = (
        ('manual', 'Manual'),
        ('auto',   'Auto (sum of variants)'),
    )
    VIDEO_HOST_CHOICES = (
        ('local',   'Local Upload'),
        ('youtube', 'YouTube'),
        ('vimeo',   'Vimeo'),
    )

    # ── Basic info ──
    name           = models.CharField(max_length=100)
    slug           = models.SlugField(max_length=150, unique=True, blank=True, null=True)
    code           = models.CharField(max_length=30, unique=True, blank=True, null=True,
                                      help_text='Leave blank to auto-generate')

    # ── Classification ──
    category       = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    subcategory    = models.ForeignKey(Subcategory, on_delete=models.CASCADE,
                                       null=True, blank=True)
    child_category = models.ForeignKey(ChildCategory, on_delete=models.SET_NULL,
                                       null=True, blank=True)
    brand          = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)
    concern        = models.ForeignKey(Concern, on_delete=models.SET_NULL,
                                       null=True, blank=True)

    # ── Pricing & stock ──
    price          = models.IntegerField(help_text='Selling price')
    previous_price = models.IntegerField(null=True, blank=True,
                                         help_text='Old price (shown crossed out)')
    weight         = models.PositiveIntegerField(null=True, blank=True,
                                                 help_text='Weight in grams')
    stock_option   = models.CharField(max_length=10, choices=STOCK_OPTION_CHOICES,
                                      default='manual')
    quantity       = models.PositiveIntegerField(default=0)
    Availability   = models.CharField(choices=AVAILABILITY_CHOICES, null=True, blank=True,
                                      max_length=100)

    # ── Media ──
    image          = models.ImageField(upload_to='ecoming')          # Featured image
    video_host     = models.CharField(max_length=10, choices=VIDEO_HOST_CHOICES,
                                      default='local')
    video_file     = models.FileField(upload_to='products/videos/', blank=True, null=True)
    video_url      = models.URLField(blank=True, help_text='YouTube / Vimeo link')

    # ── Content ──
    bullet_points  = models.JSONField(default=list, blank=True,
                                      help_text='List of bullet point strings')
    tags           = models.CharField(max_length=300, blank=True,
                                      help_text='Separate tags with commas, e.g. shirt, blue, cotton')
    description    = models.TextField(blank=True)    # rich text (HTML)
    ingredients    = models.TextField(blank=True)    # rich text (HTML)
    how_to_use     = models.TextField(blank=True)    # rich text (HTML)

    # ── Flags / meta ──
    date           = models.DateField(auto_now_add=True)
    is_popular     = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # forms send None for an empty JSONField; keep it a list
        if self.bullet_points is None:
            self.bullet_points = []
        # auto slug
        if not self.slug:
            base = slugify(self.name) or 'product'
            slug, n = base, 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        # auto product code
        if not self.code:
            self.code = generate_product_code()
        super().save(*args, **kwargs)

    # ── Helpers ──
    @property
    def discount_percent(self):
        if self.previous_price and self.previous_price > self.price:
            return round(((self.previous_price - self.price) / self.previous_price) * 100)
        return None

    @property
    def active_price(self):
        return self.price

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def total_stock(self):
        if self.stock_option == 'auto':
            return sum(v.quantity for v in self.variants.all())
        return self.quantity


# ── NEW: Gallery images (multiple per product) ──
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image   = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return f"{self.product.name} image #{self.pk}"


# ── NEW: Variants (Single / Combinations) ──
class ProductVariant(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    # Single mode -> 1 value (Red). Combination mode -> several values (Red + XL).
    values   = models.ManyToManyField(AttributeValue, related_name='variants')
    sku      = models.CharField(max_length=50, blank=True)
    price    = models.IntegerField(null=True, blank=True,
                                   help_text='Leave blank to use the product price')
    quantity = models.PositiveIntegerField(default=0)
    image    = models.ImageField(upload_to='products/variants/', blank=True, null=True)

    def __str__(self):
        names = ", ".join(v.value for v in self.values.all())
        return f"{self.product.name} - {names}" if names else self.product.name

    @property
    def final_price(self):
        return self.price if self.price is not None else self.product.price


# ═════════════════════════════════════════════
#  Auth form
# ═════════════════════════════════════════════
class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email',
                             error_messages={'exists': 'This already exists'})

    class Meta:
        model  = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder']  = 'Username'
        self.fields['email'].widget.attrs['placeholder']     = 'Email'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'

    def save(self, commit=True):
        user       = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError(self.fields['email'].error_messages['exists'])
        return self.cleaned_data['email']


# ═════════════════════════════════════════════
#  Contact
# ═════════════════════════════════════════════
class Contact_us(models.Model):
    name    = models.CharField(max_length=100)
    email   = models.EmailField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return self.email


# ═════════════════════════════════════════════
#  Coupon
# ═════════════════════════════════════════════
class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('fixed',      'Fixed Amount (৳)'),
    ]
    code            = models.CharField(max_length=50, unique=True)
    discount_type   = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES,
                                       default='percentage')
    discount        = models.DecimalField(max_digits=10, decimal_places=2,
                      help_text='e.g. 10 = 10% off or ৳10 off depending on type')
    is_active       = models.BooleanField(default=True)
    valid_from      = models.DateTimeField()
    valid_to        = models.DateTimeField()
    minimum_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                      help_text='Minimum cart total required to use this coupon')
    usage_limit     = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    used_count      = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.usage_limit > 0 and self.used_count >= self.usage_limit:
            return False
        return True

    def get_discount_amount(self, cart_total):
        if self.discount_type == 'percentage':
            return round((cart_total * self.discount) / 100, 2)
        return min(self.discount, cart_total)


# ═════════════════════════════════════════════
#  Order
# ═════════════════════════════════════════════
class Order(models.Model):
    STATUS_CHOICES = [
        ('ordered',          'Ordered'),
        ('processing',       'Processing'),
        ('shipped',          'Shipped'),
        ('on_delivery',      'On Delivery'),
        ('partial_delivery', 'Partial Delivery'),
        ('delivered',        'Delivered'),
        ('cancelled',        'Cancelled'),
        ('returned',         'Returned'),
    ]

    image    = models.ImageField(upload_to='ecommerce/order/image')
    product  = models.CharField(max_length=1000, default=' ')
    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    price    = models.IntegerField()
    quantity = models.CharField(max_length=5)
    total    = models.CharField(max_length=1000, default=' ')
    address  = models.TextField()
    phone    = models.CharField(max_length=10)
    pincode  = models.CharField(max_length=10)
    date     = models.DateField(default=datetime.datetime.today)

    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    coupon          = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.product


# ═════════════════════════════════════════════
#  Reels
# ═════════════════════════════════════════════
class Reel(models.Model):
    title   = models.CharField(max_length=100)
    video   = models.FileField(upload_to='reels/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date    = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title


# ═════════════════════════════════════════════
#  Policy Pages
# ═════════════════════════════════════════════
class PolicyPage(models.Model):
    PAGE_CHOICES = [
        ('about',             'About Us'),
        ('privacy_policy',    'Privacy Policy'),
        ('terms',             'Terms & Conditions'),
        ('shipping_delivery', 'Shipping & Delivery'),
        ('refund_returns',    'Refund and Returns'),
    ]
    slug    = models.SlugField(unique=True, choices=PAGE_CHOICES, max_length=50)
    title   = models.CharField(max_length=200)
    content = models.TextField(help_text='Write the full page content here.')
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# ═════════════════════════════════════════════
#  Social Media Links
# ═════════════════════════════════════════════
PLATFORM_CHOICES = [
    ('whatsapp',  'WhatsApp'),
    ('messenger', 'Messenger'),
    ('instagram', 'Instagram'),
    ('telegram',  'Telegram'),
    ('facebook',  'Facebook'),
    ('twitter',   'Twitter'),
    ('youtube',   'YouTube'),
    ('linkedin',  'LinkedIn'),
]


class SocialLink(models.Model):
    platform     = models.CharField(max_length=30, choices=PLATFORM_CHOICES)
    url          = models.URLField(help_text="Full profile URL (e.g. https://facebook.com/yourpage)")
    chat_handle  = models.CharField(
        max_length=100, blank=True,
        help_text="For WhatsApp: number with country code (e.g. 8801XXXXXXXXX). "
                  "For Messenger: your Facebook page username."
    )
    show_in_chat = models.BooleanField(default=False,
                   help_text="Show this platform in the chat widget?")
    order        = models.PositiveIntegerField(default=0,
                   help_text="Display order (lower = first)")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_platform_display()


# ═════════════════════════════════════════════
#  Reviews
# ═════════════════════════════════════════════
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    rating  = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


# ═════════════════════════════════════════════
#  Supplier / SMS / Landing page
# ═════════════════════════════════════════════
class Supplier(models.Model):
    name    = models.CharField(max_length=200)
    phone   = models.CharField(max_length=20)
    email   = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    note    = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SMSPromotion(models.Model):
    title   = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class LandingPage(models.Model):
    title      = models.CharField(max_length=200)
    slug       = models.SlugField(unique=True)
    content    = models.TextField()
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ═════════════════════════════════════════════
#  User Profile
# ═════════════════════════════════════════════
class UserProfile(models.Model):
    user    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone   = models.CharField(max_length=20, blank=True)
    picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# ── Auto-create / auto-save profile when User is created ──
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)