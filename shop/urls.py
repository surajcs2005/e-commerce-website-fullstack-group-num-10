from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment_page, name='payment_page'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
]