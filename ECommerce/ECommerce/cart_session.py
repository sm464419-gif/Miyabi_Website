class Cart:
    """
    Simple session cart. Same methods and session layout as the
    `django-shopping-cart` package, so Checkout, apply_coupon and the
    templates (request.session.cart) keep working.
    """

    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.cart = self.session.get('cart') or {}

    def _save(self):
        self.session['cart'] = self.cart
        self.session.modified = True

    def add(self, product, quantity=1):
        key = str(product.id)
        if key in self.cart:
            self.cart[key]['quantity'] += quantity
        else:
            self.cart[key] = {
                'userid': self.request.user.id,
                'product_id': product.id,
                'name': product.name,
                'quantity': quantity,
                'price': str(product.price),
                'image': product.image.url if product.image else '',
            }
        self._save()

    def decrement(self, product):
        key = str(product.id)
        if key in self.cart:
            self.cart[key]['quantity'] -= 1
            if self.cart[key]['quantity'] <= 0:
                del self.cart[key]
            self._save()

    def remove(self, product):
        self.cart.pop(str(product.id), None)
        self._save()

    def clear(self):
        self.cart = {}
        self._save()

    def __iter__(self):
        return iter(self.cart.values())

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())