from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from cart.cart import Cart
from app.models import (
    Category, Product, UserCreateForm, Contact_us,
    Order, Brand, Reel, PolicyPage, Review, UserProfile, SocialLink
)
from django import forms


# ── Base ──
def Base(request):
    return render(request, 'base.html')


# ── Home ──
def Index(request):
    category   = Category.objects.all()
    brand      = Brand.objects.all()
    brandID    = request.GET.get('brand')
    categoryID = request.GET.get('category')

    if categoryID:
        product = Product.objects.filter(Subcategory=categoryID).order_by('-id')
    elif brandID:
        product = Product.objects.filter(brand=brandID).order_by('-id')
    else:
        product = Product.objects.filter(is_popular=False)

    context = {
        'category':         category,
        'product':          product,
        'brand':            brand,
        'popular_products': Product.objects.filter(is_popular=True),
        'reels':            Reel.objects.all().order_by('-date'),
    }
    return render(request, 'index.html', context)


# ── Signup ──
def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request, new_user)
            return redirect('index')
    else:
        form = UserCreateForm()

    return render(request, 'registration/signup.html', {'form': form})


# ── Cart ──
@login_required(login_url="/accounts/login/")
def cart_add(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("index")

@login_required(login_url="/accounts/login/")
def item_clear(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect("cart:cart_detail")

@login_required(login_url="/accounts/login/")
def item_increment(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("cart:cart_detail")

@login_required(login_url="/accounts/login/")
def item_decrement(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.decrement(product=product)
    return redirect("cart:cart_detail")

@login_required(login_url="/accounts/login/")
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect("cart:cart_detail")

@login_required(login_url="/accounts/login/")
def cart_detail(request):
    return render(request, 'cart/cart_detail.html')


# ── Contact ──
def Contact_Page(request):
    if request.method == "POST":
        contact = Contact_us(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message'),
        )
        contact.save()
    return render(request, 'contact.html')


# ── Checkout ──
@login_required(login_url="/accounts/login/")
def Checkout(request):
    if request.method == "POST":
        address = request.POST.get('address')
        phone   = request.POST.get('phone')
        pincode = request.POST.get('pincode')

        cart = request.session.get('cart')
        uid  = request.session.get('_auth_user_id')
        user = User.objects.get(pk=uid)

        for i in cart:
            a     = int(cart[i]['price'])
            b     = cart[i]['quantity']
            total = a * b

            order = Order(
                user=user,
                product=cart[i]['name'],
                price=cart[i]['price'],
                quantity=cart[i]['quantity'],
                image=cart[i]['image'],
                address=address,
                phone=phone,
                pincode=pincode,
                total=total,
            )
            order.save()

        request.session['cart'] = {}
        return redirect('index')

    return HttpResponse("this is checkout page")


# ── Orders ──
@login_required(login_url="/accounts/login/")
def Your_Order(request):
    uid   = request.session.get('_auth_user_id')
    user  = User.objects.get(pk=uid)
    order = Order.objects.filter(user=user)
    return render(request, 'order.html', {'order': order})


# ── Products ──
def Product_page(request):
    category   = Category.objects.all()
    brand      = Brand.objects.all()
    brandID    = request.GET.get('brand')
    categoryID = request.GET.get('category')
    query      = request.GET.get('q', '').strip()

    if query:
        product = Product.objects.filter(name__icontains=query).order_by('-id')
    elif categoryID:
        product = Product.objects.filter(Subcategory=categoryID).order_by('-id')
    elif brandID:
        product = Product.objects.filter(brand=brandID).order_by('-id')
    else:
        product = Product.objects.all()

    context = {
        'category': category,
        'brand':    brand,
        'product':  product,
        'query':    query,
    }
    return render(request, 'product.html', context)


@login_required(login_url="/accounts/login/")
def Product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.all().order_by('-created')

    if request.method == 'POST':
        rating  = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if rating and comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=int(rating),
                comment=comment,
            )
        return redirect('product_detail', id=id)

    context = {
        'product':  product,
        'reviews':  reviews,
        'products': Product.objects.filter(category=product.category).exclude(id=id)[:6],
    }
    return render(request, 'product_detail.html', context)


# ── Policy Pages ──
def about(request):
    page = get_object_or_404(PolicyPage, slug='about')
    return render(request, 'policy_page.html', {'page': page})

def privacy_policy(request):
    page = get_object_or_404(PolicyPage, slug='privacy_policy')
    return render(request, 'policy_page.html', {'page': page})

def terms(request):
    page = get_object_or_404(PolicyPage, slug='terms')
    return render(request, 'policy_page.html', {'page': page})

def shipping_delivery(request):
    page = get_object_or_404(PolicyPage, slug='shipping_delivery')
    return render(request, 'policy_page.html', {'page': page})

def refund_returns(request):
    page = get_object_or_404(PolicyPage, slug='refund_returns')
    return render(request, 'policy_page.html', {'page': page})


# ══════════════════════════════════════════
# ACCOUNT VIEWS
# ══════════════════════════════════════════

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=False, label='First Name')
    last_name  = forms.CharField(max_length=50, required=False, label='Last Name')

    class Meta:
        model  = UserProfile
        fields = ('phone', 'picture')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial  = user.last_name


class EmailChangeForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ('email',)


@login_required(login_url='login')
def account(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders     = Order.objects.filter(user=request.user).order_by('-date')
    return render(request, 'account.html', {
        'profile': profile,
        'orders':  orders,
    })


@login_required(login_url='login')
def account_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(
            request.POST, request.FILES,
            instance=profile, user=request.user
        )
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.save()
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('account')
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)
    return render(request, 'account_edit.html', {'form': form})


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('account')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})


@login_required(login_url='login')
def change_email(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Email updated successfully.')
            return redirect('account')
    else:
        form = EmailChangeForm(instance=request.user)
    return render(request, 'change_email.html', {'form': form})