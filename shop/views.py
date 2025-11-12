from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json
import urllib.parse
from .models import Product

# Try to import Razorpay, but make it optional
try:
    import razorpay
    from razorpay.errors import SignatureVerificationError
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    razorpay = None
    SignatureVerificationError = Exception

# Try to import QR code generator
try:
    import qrcode
    from io import BytesIO
    import base64
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    qrcode = None


# 🏠 Homepage
def home(request):
    category = request.GET.get('category')
    if category:
        products = Product.objects.filter(category=category)
    else:
        products = Product.objects.all()
    return render(request, 'shop/home.html', {'products': products, 'selected_category': category})


# 🧾 Product details page
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})


# 🛒 Add to Cart
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    cart = request.session.get('cart', {})

    # Get quantity from form, default to 1
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1
    if quantity > 10:
        quantity = 10

    if str(pk) in cart:
        cart[str(pk)]['quantity'] += quantity
    else:
        cart[str(pk)] = {'name': product.name, 'price': float(product.price), 'quantity': quantity}

    request.session['cart'] = cart
    if quantity > 1:
        messages.success(request, f"{quantity} x {product.name} added to your cart!")
    else:
        messages.success(request, f"{product.name} added to your cart!")
    return redirect('cart')


# 🧺 View Cart
def cart_view(request):
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render(request, 'shop/cart.html', {'cart': cart, 'total': total})


# ❌ Remove from Cart
def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    if str(pk) in cart:
        del cart[str(pk)]
        request.session['cart'] = cart
    return redirect('cart')


# 💳 Checkout Page
def checkout(request):
    cart = request.session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render(request, 'shop/checkout.html', {'cart': cart, 'total': total})


# 👤 User Signup
def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm = request.POST['confirm']

        if password == confirm:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken")
            else:
                User.objects.create_user(username=username, password=password)
                messages.success(request, "Account created! Please log in.")
                return redirect('login_view')
        else:
            messages.error(request, "Passwords do not match")
    return render(request, 'shop/signup.html')


# 🔑 User Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'shop/login.html')


# 🚪 Logout
def logout_view(request):
    logout(request)
    return redirect('home')


# 💳 Payment Page
def payment_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty!")
        return redirect('cart')
    
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    
    # Generate UPI QR code (even if Razorpay is not available)
    upi_qr_code = None
    upi_payment_url = None
    upi_id_display = None
    if QRCODE_AVAILABLE:
        try:
            upi_id = getattr(settings, 'UPI_ID', None)
            merchant_name = getattr(settings, 'MERCHANT_NAME', 'Ecommerce')
            
            if upi_id and upi_id != 'your-upi-id@paytm':
                upi_id_display = upi_id
                # Create UPI payment URL
                upi_payment_url = f"upi://pay?pa={upi_id}&pn={urllib.parse.quote(merchant_name)}&am={total:.2f}&cu=INR&tn=Order Payment"
                
                # Generate QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(upi_payment_url)
                qr.make(fit=True)
                
                # Create QR code image
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                upi_qr_code = f"data:image/png;base64,{image_base64}"
        except Exception as e:
            # If QR code generation fails, continue without it
            upi_qr_code = None
            upi_payment_url = None
            upi_id_display = None
    
    # Check if Razorpay is available and configured
    if not RAZORPAY_AVAILABLE:
        # Fallback to simple payment without Razorpay, but show QR code if available
        context = {
            'total': total,
            'amount': int(total * 100),
            'order_id': None,
            'razorpay_key': None,
            'razorpay_enabled': False,
            'upi_qr_code': upi_qr_code,
            'upi_payment_url': upi_payment_url,
            'upi_id': upi_id_display or getattr(settings, 'UPI_ID', 'your-upi@paytm'),
        }
        return render(request, 'shop/payment.html', context)
    
    # Check if Razorpay keys are configured
    razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
    razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
    
    if not razorpay_key_id or not razorpay_key_secret:
        # Fallback to simple payment, but show QR code if available
        context = {
            'total': total,
            'amount': int(total * 100),
            'order_id': None,
            'razorpay_key': None,
            'razorpay_enabled': False,
            'upi_qr_code': upi_qr_code,
            'upi_payment_url': upi_payment_url,
            'upi_id': upi_id_display or getattr(settings, 'UPI_ID', 'your-upi@paytm'),
        }
        return render(request, 'shop/payment.html', context)
    
    if razorpay_key_id == 'your_razorpay_key_id_here' or razorpay_key_secret == 'your_razorpay_key_secret_here':
        # Fallback to simple payment, but show QR code if available
        context = {
            'total': total,
            'amount': int(total * 100),
            'order_id': None,
            'razorpay_key': None,
            'razorpay_enabled': False,
            'upi_qr_code': upi_qr_code,
            'upi_payment_url': upi_payment_url,
            'upi_id': upi_id_display or getattr(settings, 'UPI_ID', 'your-upi@paytm'),
        }
        return render(request, 'shop/payment.html', context)
    
    # Initialize Razorpay client
    try:
        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
        
        # Create order
        amount = int(total * 100)  # Convert to paise
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'receipt': f'order_{request.user.id if request.user.is_authenticated else "guest"}_{total}',
            'payment_capture': '1'
        }
        
        order = client.order.create(data=order_data)
        order_id = order['id']
        
        context = {
            'total': total,
            'amount': amount,
            'order_id': order_id,
            'razorpay_key': razorpay_key_id,
            'razorpay_enabled': True,
            'upi_qr_code': upi_qr_code,
            'upi_payment_url': upi_payment_url,
            'upi_id': upi_id_display or getattr(settings, 'UPI_ID', 'your-upi@paytm'),
        }
        return render(request, 'shop/payment.html', context)
    except Exception as e:
        # Fallback to simple payment if Razorpay fails, but show QR code if available
        messages.warning(request, f"Razorpay error: {str(e)}. Using simple payment method.")
        context = {
            'total': total,
            'amount': int(total * 100),
            'order_id': None,
            'razorpay_key': None,
            'razorpay_enabled': False,
            'upi_qr_code': upi_qr_code,
            'upi_payment_url': upi_payment_url,
            'upi_id': upi_id_display or getattr(settings, 'UPI_ID', 'your-upi@paytm'),
        }
        return render(request, 'shop/payment.html', context)


def payment_success(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'cod')
        
        # Handle Cash on Delivery
        if payment_method == 'cod':
            # Clear cart and show success message
            request.session['cart'] = {}
            messages.success(request, "Order placed successfully! You will pay cash on delivery.")
            return render(request, 'shop/payment_success.html', {'payment_method': 'cod'})
        
        # Handle UPI/Online Payment (Razorpay)
        elif payment_method == 'upi':
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            # Verify Razorpay payment
            if razorpay_payment_id and razorpay_order_id and razorpay_signature and RAZORPAY_AVAILABLE:
                razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
                razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)
                
                if razorpay_key_id and razorpay_key_secret and razorpay_key_id != 'your_razorpay_key_id_here':
                    try:
                        # Verify payment signature
                        client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
                        
                        # Verify the payment signature
                        params_dict = {
                            'razorpay_order_id': razorpay_order_id,
                            'razorpay_payment_id': razorpay_payment_id,
                            'razorpay_signature': razorpay_signature
                        }
                        
                        # Verify signature
                        client.utility.verify_payment_signature(params_dict)
                        
                        # Payment successful - clear cart
                        request.session['cart'] = {}
                        messages.success(request, "Payment successful! Your order has been placed.")
                        return render(request, 'shop/payment_success.html', {'payment_method': 'upi'})
                        
                    except SignatureVerificationError:
                        messages.error(request, "Payment verification failed! Please try again.")
                        return redirect('payment_page')
                    except Exception as e:
                        messages.error(request, f"Error verifying payment: {str(e)}")
                        return redirect('payment_page')
                else:
                    messages.error(request, "Payment gateway not configured. Please use Cash on Delivery.")
                    return redirect('payment_page')
            else:
                messages.error(request, "Payment details missing. Please try again.")
                return redirect('payment_page')
        else:
            # Default to COD if payment method is not specified
            request.session['cart'] = {}
            messages.success(request, "Order placed successfully! You will pay cash on delivery.")
            return render(request, 'shop/payment_success.html', {'payment_method': 'cod'})
    else:
        # If accessed via GET, redirect to payment page
        return redirect('payment_page')