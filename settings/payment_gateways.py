"""
Payment Gateway Settings for Iranian Payment Providers
"""

# Default payment gateway
DEFAULT_PAYMENT_GATEWAY = 'zarinpal'  # Options: 'zarinpal', 'idpay', 'nextpay'

# Use real gateway in development (set to True for testing with real gateways)
USE_REAL_GATEWAY = False

# Payment callback URL
PAYMENT_CALLBACK_URL = 'http://localhost:8000/payments/callback/'

# Zarinpal Gateway Settings
ZARINPAL_MERCHANT_ID = 'your_zarinpal_merchant_id_here'
ZARINPAL_SANDBOX = True  # Set to False for production
ZARINPAL_CALLBACK_URL = PAYMENT_CALLBACK_URL

# IDPay Gateway Settings
IDPAY_API_KEY = 'your_idpay_api_key_here'
IDPAY_SANDBOX = True  # Set to False for production
IDPAY_CALLBACK_URL = PAYMENT_CALLBACK_URL

# NextPay Gateway Settings
NEXTPAY_API_KEY = 'your_nextpay_api_key_here'
NEXTPAY_SANDBOX = True  # Set to False for production
NEXTPAY_CALLBACK_URL = PAYMENT_CALLBACK_URL

# Email settings for notifications
DEFAULT_FROM_EMAIL = 'noreply@istanbulplus.ir'
SITE_URL = 'http://localhost:8000'

# SMS settings (for future implementation)
SMS_API_KEY = 'your_sms_api_key_here'
SMS_SENDER_NUMBER = '10008663'
