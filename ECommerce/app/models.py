from django.db import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django import forms
import datetime


class Category(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name     = models.CharField(max_length=150)
    Category = models.ForeignKey(Category, on_delete=models.CASCADE)
    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name


class Product(models.Model):
    AVAILABILITY_CHOICES = (('In Stock', 'In Stock'), ('Out of Stock', 'Out of Stock'))
    category     = models.ForeignKey(Category, on_delete=models.CASCADE, null=False, default='')
    subcategory  = models.ForeignKey(Subcategory, on_delete=models.CASCADE, null=False, default='')
    brand        = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True)
    image        = models.ImageField(upload_to='ecoming')
    name         = models.CharField(max_length=100)
    price        = models.IntegerField()
    # ── NEW: offer price field ──
    offer_price  = models.IntegerField(null=True, blank=True,
                   help_text='Leave blank if no offer. Set lower than price.')
    Availability = models.CharField(choices=AVAILABILITY_CHOICES, null=True, max_length=100)
    date         = models.DateField(auto_now_add=True)
    is_popular   = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    # Helper: discount percentage
    @property
    def discount_percent(self):
        if self.offer_price and self.offer_price < self.price:
            return round(((self.price - self.offer_price) / self.price) * 100)
        return None

    # Helper: active selling price
    @property
    def active_price(self):
        if self.offer_price and self.offer_price < self.price:
            return self.offer_price
        return self.price


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


class Contact_us(models.Model):
    name    = models.CharField(max_length=100)
    email   = models.EmailField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return self.email


# ── NEW: Coupon model ──
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
    usage_limit     = models.PositiveIntegerField(default=0,
                      help_text='0 = unlimited')
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

    # ── NEW: status + coupon fields ──
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    coupon          = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.product


class Reel(models.Model):
    title   = models.CharField(max_length=100)
    video   = models.FileField(upload_to='reels/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date    = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title


# ── Policy Pages ──
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


# ── Social Media Links ──
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


# ── Reviews ──
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    rating  = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


# ── NEW: Supplier model ──
class Supplier(models.Model):
    name    = models.CharField(max_length=200)
    phone   = models.CharField(max_length=20)
    email   = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    note    = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ── NEW: SMS Promotion model ──
class SMSPromotion(models.Model):
    title   = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# ── NEW: Landing Page model ──
class LandingPage(models.Model):
    title      = models.CharField(max_length=200)
    slug       = models.SlugField(unique=True)
    content    = models.TextField()
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ── NEW: Product Attribute models ──
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


# ── User Profile ──
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