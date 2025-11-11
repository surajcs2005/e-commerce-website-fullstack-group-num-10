# AI Coding Agent Instructions for FashionStore Ecommerce

## Project Overview
A Django-based ecommerce platform for fashion retail with product catalog, shopping cart (session-based), user authentication, and checkout workflow. Single `shop` app handles all business logic.

## Architecture

### Tech Stack
- **Backend**: Django 4.x with SQLite3 database
- **Frontend**: Bootstrap 5.3 with Django templating
- **Authentication**: Django built-in `User` model and session middleware
- **Cart Management**: Session-based (no Cart model) - stored as `request.session['cart']` dict

### Key Components

**Data Layer** (`shop/models.py`)
- `Product` model: name, description, price, image, category (7 hardcoded choices)
- No Order/Cart models - cart persists only in session during browsing

**Views** (`shop/views.py`)
- **Product browsing**: `home()` supports category filtering via GET parameter
- **Cart flow**: `add_to_cart()` → `cart_view()` → `checkout()` → `payment_page()` → `payment_success()`
- **Auth**: `signup_view()`, `login_view()`, `logout_view()`
- Cart structure: `{'product_id_str': {'name', 'price', 'quantity'}, ...}`

**URL Routing** (`shop/urls.py`)
- All routes prefixed with empty string (mounted at root in `ecommerce/urls.py`)
- Cart state preserved via Django sessions (no AJAX cart sync)

**Templates** (`shop/templates/`)
- Base navbar in home.html and product_detail.html shows cart count
- Bootstrap 5.3 for responsive layout
- Media uploads go to `media/products/` directory

### Important Patterns

1. **Session Cart Structure**: Cart items use product ID as string key for session serialization:
   ```python
   cart[str(pk)] = {'name': product.name, 'price': float(product.price), 'quantity': 1}
   ```

2. **Product Admin Display**: ProductAdmin shows name, category, price in list view

3. **Media Handling**: Images stored in `MEDIA_ROOT = BASE_DIR / 'media'` with DEBUG mode serving (`urls.py` line 11-12)

4. **User Messages**: Django messages framework used for feedback (success/error alerts)

## Critical Developer Workflows

### Running the Project
```bash
# Install dependencies (Django, Pillow for images)
pip install django pillow

# Apply migrations
python manage.py migrate

# Run development server (port 8000)
python manage.py runserver

# Create superuser for admin panel
python manage.py createsuperuser
```

### Database Operations
- No custom migration patterns - use `python manage.py makemigrations shop` then `migrate`
- Existing migrations show category field added in 0002, then altered in 0003

### Testing
- No test infrastructure present (tests.py is empty) - add pytest/unittest as needed

## Known Limitations & Gotchas

1. **Session-Only Cart**: Cart data lost on server restart or session expiry. No persistence layer.
2. **No Order Tracking**: `payment_success()` just clears cart - no order record created
3. **Image Field**: Requires Pillow library; missing images show placeholder from external CDN
4. **Auth Gaps**: No email verification, password reset, or admin-only endpoints
5. **Template Duplication**: Navbar HTML duplicated in home.html and product_detail.html (refactor to `base.html` if expanding)
6. **BUG in models.py**: `__str__` method typo: `_str_` should be `__str__`

## Extension Points

When adding features:
- **New models**: Follow Product pattern in `models.py`, register in `admin.py`
- **New views**: Add to `views.py`, wire in `urls.py`, create template in `shop/templates/shop/`
- **New categories**: Update `CATEGORY_CHOICES` in Product model (static list, not a separate model)
- **Checkout integration**: Payment providers (Stripe, PayPal) would replace `payment_page()` mock
- **Cart persistence**: Add Order/OrderItem models before removing session dependency

## File Structure Reference
- **ecommerce/** - Project config (settings, URL root, WSGI)
- **shop/** - Core app (models, views, templates, URL routing)
- **shop/migrations/** - Schema version history
- **media/products/** - User-uploaded product images
- **db.sqlite3** - Development database

