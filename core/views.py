from django.shortcuts import redirect, render, get_object_or_404
from .models import Product, Category, Order, OrderItem
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
    products = Product.objects.all().order_by('-created_at')[:8]  # Fetch all products ordered by creation date
    return render(request, 'home.html', {'products': products})

def category_filter(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()
    return render(request, 'home.html', {
        'products': products,
        'categories': categories,
        'selected_category': category
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def view_cart(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

def update_cart_quantity(request, product_id, action):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        if action == 'add':
            cart[product_id_str] += 1
        elif action == 'subtract':
            cart[product_id_str] -= 1
            if cart[product_id_str] <= 0:
                del cart[product_id_str]

    request.session['cart'] = cart
    return HttpResponseRedirect(reverse('view_cart'))

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return HttpResponseRedirect(reverse('view_cart'))

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('view_cart')

    products = Product.objects.filter(id__in=cart.keys())
    total = 0
    order = Order.objects.create(user=request.user, total_amount=0)

    for product in products:
        qty = cart[str(product.id)]
        subtotal = qty * product.price
        total += subtotal
        OrderItem.objects.create(order=order, product=product, quantity=qty)

    order.total_amount = total
    order.save()

    request.session['cart'] = {}  # Clear cart after order
    return redirect('my_orders')

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})


