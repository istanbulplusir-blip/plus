"""
Payment Gateway Integrations for Iranian Payment Providers
"""
import requests
import json
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class ZarinpalGateway:
    """
    Zarinpal Payment Gateway Integration
    """
    
    def __init__(self):
        self.merchant_id = getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
        self.sandbox = getattr(settings, 'ZARINPAL_SANDBOX', True)
        self.callback_url = getattr(settings, 'ZARINPAL_CALLBACK_URL', '')
        
        if self.sandbox:
            self.request_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'
            self.verify_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'
            self.start_pay_url = 'https://sandbox.zarinpal.com/pg/StartPay/'
        else:
            self.request_url = 'https://api.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'
            self.verify_url = 'https://api.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'
            self.start_pay_url = 'https://www.zarinpal.com/pg/StartPay/'
    
    def request_payment(self, amount, description, callback_url, mobile=None, email=None):
        """
        Request payment from Zarinpal
        
        Args:
            amount: Amount in Toman
            description: Payment description
            callback_url: Callback URL
            mobile: Customer mobile (optional)
            email: Customer email (optional)
            
        Returns:
            dict: Response with authority or error
        """
        try:
            data = {
                'MerchantID': self.merchant_id,
                'Amount': int(amount),
                'Description': description,
                'CallbackURL': callback_url,
            }
            
            if mobile:
                data['Mobile'] = mobile
            if email:
                data['Email'] = email
            
            response = requests.post(
                self.request_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            result = response.json()
            
            if result.get('Status') == 100:
                return {
                    'success': True,
                    'authority': result.get('Authority'),
                    'redirect_url': f"{self.start_pay_url}{result.get('Authority')}"
                }
            else:
                return {
                    'success': False,
                    'error': f"خطا در درخواست پرداخت: {result.get('Status')}"
                }
                
        except Exception as e:
            logger.error(f"Zarinpal payment request failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با درگاه پرداخت'
            }
    
    def verify_payment(self, authority, amount):
        """
        Verify payment with Zarinpal
        
        Args:
            authority: Payment authority from callback
            amount: Original amount in Toman
            
        Returns:
            dict: Verification result
        """
        try:
            data = {
                'MerchantID': self.merchant_id,
                'Amount': int(amount),
                'Authority': authority
            }
            
            response = requests.post(
                self.verify_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            result = response.json()
            
            if result.get('Status') == 100:
                return {
                    'success': True,
                    'ref_id': result.get('RefID'),
                    'card_pan': result.get('CardPan', ''),
                    'card_hash': result.get('CardHash', ''),
                    'fee_type': result.get('FeeType', ''),
                    'fee': result.get('Fee', 0)
                }
            else:
                return {
                    'success': False,
                    'error': f"پرداخت ناموفق: {result.get('Status')}"
                }
                
        except Exception as e:
            logger.error(f"Zarinpal payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در تایید پرداخت'
            }


class IDPayGateway:
    """
    IDPay Payment Gateway Integration
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'IDPAY_API_KEY', '')
        self.sandbox = getattr(settings, 'IDPAY_SANDBOX', True)
        self.callback_url = getattr(settings, 'IDPAY_CALLBACK_URL', '')
        
        if self.sandbox:
            self.base_url = 'https://api.sandbox.idpay.ir/v1.1'
        else:
            self.base_url = 'https://api.idpay.ir/v1.1'
    
    def request_payment(self, amount, order_id, description, callback_url, name=None, phone=None, mail=None):
        """
        Request payment from IDPay
        
        Args:
            amount: Amount in Rial
            order_id: Order ID
            description: Payment description
            callback_url: Callback URL
            name: Customer name (optional)
            phone: Customer phone (optional)
            mail: Customer email (optional)
            
        Returns:
            dict: Response with payment link or error
        """
        try:
            data = {
                'order_id': str(order_id),
                'amount': int(amount * 10),  # Convert Toman to Rial
                'name': name or '',
                'phone': phone or '',
                'mail': mail or '',
                'desc': description,
                'callback': callback_url
            }
            
            response = requests.post(
                f'{self.base_url}/payment',
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-KEY': self.api_key,
                    'X-SANDBOX': '1' if self.sandbox else '0'
                },
                timeout=30
            )
            
            result = response.json()
            
            if 'id' in result:
                return {
                    'success': True,
                    'payment_id': result.get('id'),
                    'redirect_url': result.get('link')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error_message', 'خطا در درخواست پرداخت')
                }
                
        except Exception as e:
            logger.error(f"IDPay payment request failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با درگاه پرداخت'
            }
    
    def verify_payment(self, payment_id, order_id, amount):
        """
        Verify payment with IDPay
        
        Args:
            payment_id: Payment ID from callback
            order_id: Order ID
            amount: Original amount in Toman
            
        Returns:
            dict: Verification result
        """
        try:
            data = {
                'id': payment_id,
                'order_id': str(order_id)
            }
            
            response = requests.post(
                f'{self.base_url}/payment/verify',
                json=data,
                headers={
                    'Content-Type': 'application/json',
                    'X-API-KEY': self.api_key,
                    'X-SANDBOX': '1' if self.sandbox else '0'
                },
                timeout=30
            )
            
            result = response.json()
            
            if result.get('status') == 100:
                return {
                    'success': True,
                    'track_id': result.get('track_id'),
                    'id': result.get('id'),
                    'order_id': result.get('order_id'),
                    'amount': result.get('amount'),
                    'date': result.get('date'),
                    'payment': result.get('payment'),
                    'verify': result.get('verify')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error_message', 'پرداخت ناموفق')
                }
                
        except Exception as e:
            logger.error(f"IDPay payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در تایید پرداخت'
            }


class NextPayGateway:
    """
    NextPay Payment Gateway Integration
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'NEXTPAY_API_KEY', '')
        self.sandbox = getattr(settings, 'NEXTPAY_SANDBOX', True)
        self.callback_url = getattr(settings, 'NEXTPAY_CALLBACK_URL', '')
        
        if self.sandbox:
            self.base_url = 'https://api.nextpay.org'
        else:
            self.base_url = 'https://api.nextpay.org'
    
    def request_payment(self, amount, order_id, description, callback_url, customer_phone=None):
        """
        Request payment from NextPay
        
        Args:
            amount: Amount in Rial
            order_id: Order ID
            description: Payment description
            callback_url: Callback URL
            customer_phone: Customer phone (optional)
            
        Returns:
            dict: Response with trans_id or error
        """
        try:
            data = {
                'api_key': self.api_key,
                'order_id': str(order_id),
                'amount': int(amount * 10),  # Convert Toman to Rial
                'callback_uri': callback_url,
                'customer_phone': customer_phone or '',
                'custom_json_fields': json.dumps({'description': description})
            }
            
            response = requests.post(
                f'{self.base_url}/v1/payment',
                data=data,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('code') == -1:
                return {
                    'success': True,
                    'trans_id': result.get('trans_id'),
                    'redirect_url': f"https://nextpay.org/nx/gateway/payment/{result.get('trans_id')}"
                }
            else:
                return {
                    'success': False,
                    'error': f"خطا در درخواست پرداخت: {result.get('code')}"
                }
                
        except Exception as e:
            logger.error(f"NextPay payment request failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در ارتباط با درگاه پرداخت'
            }
    
    def verify_payment(self, trans_id, amount, order_id):
        """
        Verify payment with NextPay
        
        Args:
            trans_id: Transaction ID from callback
            amount: Original amount in Toman
            order_id: Order ID
            
        Returns:
            dict: Verification result
        """
        try:
            data = {
                'api_key': self.api_key,
                'trans_id': trans_id,
                'amount': int(amount * 10),  # Convert Toman to Rial
                'order_id': str(order_id)
            }
            
            response = requests.post(
                f'{self.base_url}/v1/payment/verify',
                data=data,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('code') == 0:
                return {
                    'success': True,
                    'trans_id': result.get('trans_id'),
                    'amount': result.get('amount'),
                    'order_id': result.get('order_id'),
                    'card_holder': result.get('card_holder', ''),
                    'card_number': result.get('card_number', ''),
                    'shaparak_ref_id': result.get('shaparak_ref_id', '')
                }
            else:
                return {
                    'success': False,
                    'error': f"پرداخت ناموفق: {result.get('code')}"
                }
                
        except Exception as e:
            logger.error(f"NextPay payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در تایید پرداخت'
            }


class PaymentGatewayFactory:
    """
    Factory class for creating payment gateway instances
    """
    
    @staticmethod
    def get_gateway(gateway_name):
        """
        Get payment gateway instance
        
        Args:
            gateway_name: Name of the gateway ('zarinpal', 'idpay', 'nextpay')
            
        Returns:
            Gateway instance or None
        """
        gateways = {
            'zarinpal': ZarinpalGateway,
            'idpay': IDPayGateway,
            'nextpay': NextPayGateway,
        }
        
        gateway_class = gateways.get(gateway_name.lower())
        if gateway_class:
            return gateway_class()
        
        return None
