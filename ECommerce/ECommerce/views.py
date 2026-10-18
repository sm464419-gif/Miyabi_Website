from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from cart.cart import Cart
from django.contrib.admin.views.decorators import staff_member_required
from app.models import (
    Category, Product, UserCreateForm, Contact_us,
    Order, Brand, Reel, PolicyPage, Review,
    UserProfile, SocialLink, Coupon
)
from django import forms


# ════════════════════════════════════════════════
#  BASE
# ════════════════════════════════════════════════
def Base(request):
    return render(request, 'base.html')


# ════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════
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


# ════════════════════════════════════════════════
#  SIGNUP
# ════════════════════════════════════════════════
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


# ════════════════════════════════════════════════
#  CART
# ════════════════════════════════════════════════
@login_required(login_url="/accounts/login/")
def cart_add(request, id):
    cart    = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("index")

@login_required(login_url="/accounts/login/")
def item_clear(request, id):
    cart    = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect("cart:cart_detail")

@login_required(login_url="/accounts/login/")
def item_increment(request, id):
    cart    = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("cart:cart_detail")

@login_required(login_url="/accounts/login/")
def item_decrement(request, id):
    cart    = Cart(request)
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


# ════════════════════════════════════════════════
#  COUPON — apply & remove
# ════════════════════════════════════════════════
@login_required(login_url="/accounts/login/")
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            messages.error(request, 'This coupon code does not exist.')
            return redirect('cart:cart_detail')

        # Check validity
        if not coupon.is_valid():
            messages.error(request, 'This coupon is expired or inactive.')
            return redirect('cart:cart_detail')

        # Check minimum cart amount
        cart        = Cart(request)
        cart_total  = sum(
            int(item['price']) * int(item['quantity'])
            for item in cart
        )
        if cart_total < coupon.minimum_amount:
            messages.error(
                request,
                f'Minimum order amount for this coupon is ৳{coupon.minimum_amount}.'
            )
            return redirect('cart:cart_detail')

        # Save coupon to session
        request.session['coupon_code']     = coupon.code
        request.session['coupon_discount'] = str(
            coupon.get_discount_amount(cart_total)
        )
        request.session['coupon_type']     = coupon.discount_type
        request.session['coupon_pct']      = str(coupon.discount)

        messages.success(
            request,
            f'Coupon "{coupon.code}" applied! You save ৳{coupon.get_discount_amount(cart_total)}.'
        )

    return redirect('cart:cart_detail')


@login_required(login_url="/accounts/login/")
def remove_coupon(request):
    for key in ('coupon_code', 'coupon_discount', 'coupon_type', 'coupon_pct'):
        request.session.pop(key, None)
    messages.info(request, 'Coupon removed.')
    return redirect('cart:cart_detail')


# ════════════════════════════════════════════════
#  CONTACT
# ════════════════════════════════════════════════
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


# ════════════════════════════════════════════════
#  CHECKOUT
# ════════════════════════════════════════════════
@login_required(login_url="/accounts/login/")
def Checkout(request):
    if request.method == "POST":
        address = request.POST.get('address')
        phone   = request.POST.get('phone')
        pincode = request.POST.get('pincode')

        cart = request.session.get('cart')
        uid  = request.session.get('_auth_user_id')
        user = User.objects.get(pk=uid)

        # Resolve coupon if applied
        coupon          = None
        coupon_discount = 0
        coupon_code     = request.session.get('coupon_code')
        if coupon_code:
            try:
                coupon          = Coupon.objects.get(code=coupon_code, is_active=True)
                coupon_discount = float(request.session.get('coupon_discount', 0))
                # Increment usage count
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                coupon = None

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
                coupon=coupon,
                coupon_discount=coupon_discount,
            )
            order.save()

        # Clear cart and coupon from session
        request.session['cart'] = {}
        for key in ('coupon_code', 'coupon_discount', 'coupon_type', 'coupon_pct'):
            request.session.pop(key, None)

        return redirect('index')

    return HttpResponse("this is checkout page")


# ════════════════════════════════════════════════
#  ORDERS
# ════════════════════════════════════════════════
@login_required(login_url="/accounts/login/")
def Your_Order(request):
    uid   = request.session.get('_auth_user_id')
    user  = User.objects.get(pk=uid)
    order = Order.objects.filter(user=user).order_by('-date')
    return render(request, 'order.html', {'order': order})


# ════════════════════════════════════════════════
#  PRODUCTS
# ════════════════════════════════════════════════
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
        'products': Product.objects.filter(
            category=product.category
        ).exclude(id=id)[:6],
    }
    return render(request, 'product_detail.html', context)


# ════════════════════════════════════════════════
#  POLICY PAGES
# ════════════════════════════════════════════════
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


# ════════════════════════════════════════════════
#  ACCOUNT VIEWS
# ════════════════════════════════════════════════
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


# ════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ════════════════════════════════════════════════
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
import json

@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()

    # ── Order status counts ──
    status_counts = {
        'ordered':          Order.objects.filter(status='ordered').count(),
        'processing':       Order.objects.filter(status='processing').count(),
        'shipped':          Order.objects.filter(status='shipped').count(),
        'on_delivery':      Order.objects.filter(status='on_delivery').count(),
        'partial_delivery': Order.objects.filter(status='partial_delivery').count(),
        'delivered':        Order.objects.filter(status='delivered').count(),
        'cancelled':        Order.objects.filter(status='cancelled').count(),
        'returned':         Order.objects.filter(status='returned').count(),
    }

    # ── Top stats ──
    total_orders    = Order.objects.count()
    total_revenue   = Order.objects.aggregate(
                          s=Sum('price'))['s'] or 0
    total_customers = User.objects.filter(is_staff=False).count()
    total_products  = Product.objects.count()

    # ── Sales overview last 30 days ──
    thirty_days_ago = today - timezone.timedelta(days=30)
    sales_qs = (
        Order.objects
        .filter(date__gte=thirty_days_ago)
        .values('date')
        .annotate(
            total_orders=Count('id'),
            total_amount=Sum('price')
        )
        .order_by('date')
    )

    sales_labels  = json.dumps([str(s['date']) for s in sales_qs])
    sales_orders  = json.dumps([s['total_orders']           for s in sales_qs])
    sales_amounts = json.dumps([float(s['total_amount'] or 0) for s in sales_qs])

    # ── Recent orders ──
    recent_orders = Order.objects.select_related(
        'user', 'coupon'
    ).order_by('-date', '-id')[:10]

    # ── Popular products ──
    popular_products = Product.objects.filter(is_popular=True)[:8]

    # ── Active coupons ──
    from app.models import Coupon
    active_coupons = Coupon.objects.filter(is_active=True).order_by('-id')[:6]

    return render(request, 'admin_dashboard.html', {
        'status_counts':    status_counts,
        'total_orders':     total_orders,
        'total_revenue':    total_revenue,
        'total_customers':  total_customers,
        'total_products':   total_products,
        'sales_labels':     sales_labels,
        'sales_orders':     sales_orders,
        'sales_amounts':    sales_amounts,
        'recent_orders':    recent_orders,
        'popular_products': popular_products,
        'active_coupons':   active_coupons,
        'today':            today,
    })


# ════════════════════════════════════════════════
#  ADMIN ORDER MANAGEMENT
# ════════════════════════════════════════════════
@staff_member_required
def admin_orders(request):
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('q', '').strip()

    orders = Order.objects.select_related('user', 'coupon').order_by('-date', '-id')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search:
        orders = orders.filter(
            models.Q(product__icontains=search) |
            models.Q(user__username__icontains=search) |
            models.Q(phone__icontains=search)
        )

    # Handle status update via POST
    if request.method == 'POST':
        order_id   = request.POST.get('order_id')
        new_status = request.POST.get('status')
        if order_id and new_status:
            Order.objects.filter(id=order_id).update(status=new_status)
            messages.success(request, f'Order #{order_id} status updated.')
        return redirect(request.path + (
            f'?status={status_filter}' if status_filter else ''
        ))

    status_choices = Order.STATUS_CHOICES
    return render(request, 'admin_orders.html', {
        'orders':         orders,
        'status_filter':  status_filter,
        'status_choices': status_choices,
        'search':         search,
    })