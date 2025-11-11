# Razorpay Payment Gateway Setup

## Steps to Configure Razorpay

1. **Create a Razorpay Account**
   - Go to https://razorpay.com/
   - Sign up for an account
   - Complete the KYC verification process

2. **Get Your API Keys**
   - Log in to your Razorpay Dashboard
   - Go to Settings > API Keys
   - Generate Test/Live keys
   - Copy your Key ID and Key Secret

3. **Update Settings**
   - Open `ecommerce/settings.py`
   - Replace the placeholder values:
     ```python
     RAZORPAY_KEY_ID = 'your_razorpay_key_id_here'
     RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret_here'
     ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Test the Payment**
   - Use Razorpay test cards for testing
   - Test Card: 4111 1111 1111 1111
   - CVV: Any 3 digits
   - Expiry: Any future date

## Payment Flow

1. User adds items to cart
2. User proceeds to checkout
3. User clicks "Proceed to Payment"
4. Razorpay payment gateway opens
5. User completes payment
6. Payment is verified on the server
7. Cart is cleared and success page is shown

## Security Notes

- Never commit your Razorpay keys to version control
- Use environment variables for production
- Always verify payment signatures on the server side
- Use HTTPS in production

## Environment Variables (Recommended for Production)

```python
import os

RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
```


