import json
from datetime import timedelta

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from cart.cart import Cart
from app.models import (
    Category, Subcategory, ChildCategory, Concern, Brand,
    Product, ProductImage, ProductVariant, Attribute, AttributeValue,
    UserCreateForm, Contact_us, Order, Reel, PolicyPage, Review,
    UserProfile, SocialLink, Coupon
)


# ════════════════════════════════════════════════
#  SMALL HELPERS
# ════════════════════════════════════════════════
def _to_int(value, default=None):
    """Safe int() for form values. Returns default when empty/invalid."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _variants_json(product):
    """Variants of a product as JSON (used by edit form + detail page JS)."""
    data = []
    for v in product.variants.prefetch_related('values__attribute'):
        data.append({
            'id':       v.id,
            'values':   [{'id': x.id, 'attribute': x.attribute.name, 'value': x.value}
                         for x in v.values.all()],
            'sku':      v.sku,
            'price':    v.price if v.price is not None else product.price,
            'quantity': v.quantity,
            'image':    v.image.url if v.image else '',
        })
    return json.dumps(data)


def _variant_groups(product):
    """Group variant options by attribute, e.g. [{'name': 'Color', 'values': [...]}]."""
    groups = {}
    for v in product.variants.prefetch_related('values__attribute'):
        for val in v.values.all():
            groups.setdefault(val.attribute.name, {})[val.id] = val.value
    return [
        {'name': name, 'values': [{'id': i, 'value': n} for i, n in vals.items()]}
        for name, vals in groups.items()
    ]


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
    categoryID = request.GET.get('category')      # subcategory id (kept param name)
    childID    = request.GET.get('child')         # NEW: child category id

    if childID:
        product = Product.objects.filter(child_category=childID).order_by('-id')
    elif categoryID:
        product = Product.objects.filter(subcategory=categoryID).order_by('-id')
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
#  PRODUCTS (storefront)
# ════════════════════════════════════════════════
def Product_page(request):
    category   = Category.objects.all()
    brand      = Brand.objects.all()
    brandID    = request.GET.get('brand')
    categoryID = request.GET.get('category')      # subcategory id (kept param name)
    childID    = request.GET.get('child')         # NEW: child category id
    query      = request.GET.get('q', '').strip()

    if query:
        product = Product.objects.filter(
            Q(name__icontains=query) | Q(tags__icontains=query)
        ).order_by('-id')
    elif childID:
        product = Product.objects.filter(child_category=childID).order_by('-id')
    elif categoryID:
        product = Product.objects.filter(subcategory=categoryID).order_by('-id')
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
def Product_detail(request, slug=None, id=None):
    # Works with both URL styles: /product/<slug>/ and the old /product/<id>
    if slug:
        product = Product.objects.filter(slug=slug).first()
        # /product/3/ also matches the slug pattern, so fall back to the id
        if product is None and slug.isdigit():
            product = Product.objects.filter(id=int(slug)).first()
        if product is None:
            raise Http404('No Product matches the given query.')
    else:
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
        return redirect(request.path)

    context = {
        'product':        product,
        'reviews':        reviews,
        'gallery':        product.gallery.all(),
        'variants':       product.variants.prefetch_related('values__attribute'),
        'variant_groups': _variant_groups(product),
        'variants_json':  _variants_json(product),
        'category':       Category.objects.prefetch_related(
                              'subcategory_set__child_categories'
                          ),
        'brands':         Brand.objects.all(),
        'bullet_points':  product.bullet_points,
        'tag_list':       product.tag_list,
        'products':       Product.objects.filter(
                              category=product.category
                          ).exclude(pk=product.pk)[:6],
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
    thirty_days_ago = today - timedelta(days=30)
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
            Q(product__icontains=search) |
            Q(user__username__icontains=search) |
            Q(phone__icontains=search)
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


# ════════════════════════════════════════════════
#  ADMIN: AJAX (chained dropdowns)
# ════════════════════════════════════════════════
@staff_member_required
def load_subcategories(request):
    """GET ?category=<id>  ->  [{'id':1,'name':'...'}, ...]"""
    category_id = _to_int(request.GET.get('category'))
    data = []
    if category_id:
        data = list(
            Subcategory.objects.filter(category_id=category_id)
            .order_by('name').values('id', 'name')
        )
    return JsonResponse(data, safe=False)


@staff_member_required
def load_child_categories(request):
    """GET ?subcategory=<id>  ->  [{'id':1,'name':'...'}, ...]"""
    sub_id = _to_int(request.GET.get('subcategory'))
    data = []
    if sub_id:
        data = list(
            ChildCategory.objects.filter(subcategory_id=sub_id)
            .order_by('name').values('id', 'name')
        )
    return JsonResponse(data, safe=False)


# ════════════════════════════════════════════════
#  ADMIN: PRODUCT  (insert / edit / list / delete)
# ════════════════════════════════════════════════
def _save_product(request, product=None):
    """
    Create or update a Product from the Insert/Edit Product form.
    Returns (product, error_message). error_message is None on success.

    Form field names expected:
      name, slug, code, category, subcategory, child_category, brand, concern,
      price, previous_price, weight, stock_option, quantity,
      image (file), gallery (multiple files), delete_gallery (ids, edit only),
      video_host, video_file (file), video_url,
      bullet_points (repeated text inputs), tags, description, ingredients,
      how_to_use, is_popular (checkbox)

      Variants - one block per row, where <n> comes from the hidden
      repeated input "variant_rows":
        variant_rows, variant_id_<n> (edit only), variant_values_<n> (comma
        separated AttributeValue ids, e.g. "3,7"), variant_sku_<n>,
        variant_price_<n>, variant_quantity_<n>, variant_image_<n> (file)
    """
    p, f   = request.POST, request.FILES
    is_new = product is None

    # ── Validation ──
    name        = p.get('name', '').strip()
    price       = _to_int(p.get('price'))
    category_id = _to_int(p.get('category'))

    if not name:
        return None, 'Product name is required.'
    if price is None:
        return None, 'Price is required.'
    if not category_id:
        return None, 'Category is required.'
    if is_new and not f.get('image'):
        return None, 'Featured image is required.'

    code = p.get('code', '').strip() or None
    if code:
        dup = Product.objects.filter(code=code)
        if product:
            dup = dup.exclude(pk=product.pk)
        if dup.exists():
            return None, f'Product code "{code}" already exists.'

    slug = slugify(p.get('slug', '').strip()) or None
    if slug:
        dup = Product.objects.filter(slug=slug)
        if product:
            dup = dup.exclude(pk=product.pk)
        if dup.exists():
            return None, f'Slug "{slug}" is already used by another product.'

    stock_option = p.get('stock_option', 'manual')
    if stock_option not in dict(Product.STOCK_OPTION_CHOICES):
        stock_option = 'manual'
    video_host = p.get('video_host', 'local')
    if video_host not in dict(Product.VIDEO_HOST_CHOICES):
        video_host = 'local'

    try:
        with transaction.atomic():
            if is_new:
                product = Product()

            # ── Basic info ──
            product.name = name
            product.slug = slug or product.slug
            product.code = code or product.code

            # ── Classification ──
            product.category_id       = category_id
            product.subcategory_id    = _to_int(p.get('subcategory'))
            product.child_category_id = _to_int(p.get('child_category'))
            product.brand_id          = _to_int(p.get('brand'))
            product.concern_id        = _to_int(p.get('concern'))

            # ── Pricing & stock ──
            product.price          = price
            product.previous_price = _to_int(p.get('previous_price'))
            product.weight         = _to_int(p.get('weight'))
            product.stock_option   = stock_option
            product.quantity       = max(_to_int(p.get('quantity'), 0), 0)

            # ── Media ──
            if f.get('image'):
                product.image = f['image']
            product.video_host = video_host
            if f.get('video_file'):
                product.video_file = f['video_file']
            product.video_url = p.get('video_url', '').strip()

            # ── Content ──
            product.bullet_points = [
                b.strip() for b in p.getlist('bullet_points') if b.strip()
            ]
            product.tags = ', '.join(
                t.strip() for t in p.get('tags', '').split(',') if t.strip()
            )
            product.description = p.get('description', '')
            product.ingredients = p.get('ingredients', '')
            product.how_to_use  = p.get('how_to_use', '')
            product.is_popular  = 'is_popular' in p

            product.save()

            # ── Gallery images ──
            delete_ids = [i for i in map(_to_int, p.getlist('delete_gallery')) if i]
            if delete_ids:
                ProductImage.objects.filter(product=product, id__in=delete_ids).delete()
            for img in f.getlist('gallery'):
                ProductImage.objects.create(product=product, image=img)

            # ── Variants ──
            kept_ids = []
            for row in p.getlist('variant_rows'):
                value_ids = [
                    v for v in map(_to_int, p.get(f'variant_values_{row}', '').split(','))
                    if v
                ]
                if not value_ids:
                    continue

                variant = None
                variant_id = _to_int(p.get(f'variant_id_{row}'))
                if variant_id:
                    variant = ProductVariant.objects.filter(
                        id=variant_id, product=product
                    ).first()
                if variant is None:
                    variant = ProductVariant(product=product)

                variant.sku      = p.get(f'variant_sku_{row}', '').strip()
                variant.price    = _to_int(p.get(f'variant_price_{row}'))
                variant.quantity = max(_to_int(p.get(f'variant_quantity_{row}'), 0), 0)
                v_img = f.get(f'variant_image_{row}')
                if v_img:
                    variant.image = v_img
                variant.save()
                variant.values.set(AttributeValue.objects.filter(id__in=value_ids))
                kept_ids.append(variant.id)

            # remove variants that were deleted in the form
            product.variants.exclude(id__in=kept_ids).delete()

            # ── Availability follows stock ──
            product.Availability = 'In Stock' if product.total_stock > 0 else 'Out of Stock'
            product.save(update_fields=['Availability'])

    except IntegrityError:
        return None, 'Could not save: slug or product code already exists.'

    return product, None


def _product_form_context(request, product=None):
    ctx = {
        'product':          product,
        'form_data':        request.POST if request.method == 'POST' else None,
        'categories':       Category.objects.all(),
        'brands':           Brand.objects.all(),
        'concerns':         Concern.objects.all(),
        'attributes':       Attribute.objects.prefetch_related('values'),
        'stock_options':    Product.STOCK_OPTION_CHOICES,
        'video_hosts':      Product.VIDEO_HOST_CHOICES,
        'subcategories':    Subcategory.objects.none(),
        'child_categories': ChildCategory.objects.none(),
        'gallery':          [],
        'variants_json':    '[]',
    }
    if product:
        if product.category_id:
            ctx['subcategories'] = Subcategory.objects.filter(category_id=product.category_id)
        if product.subcategory_id:
            ctx['child_categories'] = ChildCategory.objects.filter(
                subcategory_id=product.subcategory_id
            )
        ctx['gallery']       = product.gallery.all()
        ctx['variants_json'] = _variants_json(product)
    return ctx


@staff_member_required
def admin_product_add(request):
    if request.method == 'POST':
        product, error = _save_product(request)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, f'Product "{product.name}" added.')
            return redirect('admin_product_list')
    return render(request, 'admin_product_form.html', _product_form_context(request))


@staff_member_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        saved, error = _save_product(request, product)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, f'Product "{saved.name}" updated.')
            return redirect('admin_product_list')
    return render(request, 'admin_product_form.html', _product_form_context(request, product))


@staff_member_required
def admin_product_list(request):
    query    = request.GET.get('q', '').strip()
    products = Product.objects.select_related(
        'category', 'subcategory', 'child_category', 'brand'
    ).order_by('-id')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )
    return render(request, 'admin_product_list.html', {
        'products': products,
        'query':    query,
    })


@staff_member_required
def admin_product_delete(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
    return redirect('admin_product_list')