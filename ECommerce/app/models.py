from django.db import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    Availability = models.CharField(choices=AVAILABILITY_CHOICES, null=True, max_length=100)
    date         = models.DateField(auto_now_add=True)
    is_popular   = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email', error_messages={'exists': 'This already exists'})

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


class Order(models.Model):
    STATUS_CHOICES = [
        ('ordered',    'Ordered'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
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
    status   = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ordered'
    )

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
    show_in_chat = models.BooleanField(default=False, help_text="Show this platform in the chat widget?")
    order        = models.PositiveIntegerField(default=0, help_text="Display order (lower = first)")

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