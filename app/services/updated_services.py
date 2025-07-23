#!/usr/bin/env python3
"""
Updated Services to Match New Specification
7 total services: 6 dummy + 1 real (Currency Conversion)
"""

import uuid
import random
import requests
import os
from typing import Dict, Any, Optional

try:
    # Try relative imports first (when imported as a package)
    from .base_service import BaseService, ServiceResult
except ImportError:
    # Fall back to absolute imports (when run as standalone)
    from base_service import BaseService, ServiceResult

# =============================================================================
# 1. ORDER CREATION SERVICE (Dummy)
# =============================================================================
class OrderCreationService(BaseService):
    """🛒 Order Creation - Simulates receiving an order"""
    
    def __init__(self):
        super().__init__("OrderCreationService", failure_rate=0.1)
        self.orders = {}  # In-memory order storage
        
    def execute(self, customer_id: str, items: list, channel: str = "B2C", **kwargs) -> ServiceResult:
        """Create a new order"""
        self._log_operation("CREATE_ORDER", True, f"Customer: {customer_id}, Channel: {channel}")
        
        # Simulate failure
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="Order creation failed - system temporarily unavailable"
            )
        
        # Create order
        order_id = str(uuid.uuid4())
        total_amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
        
        order_data = {
            'order_id': order_id,
            'customer_id': customer_id,
            'channel': channel,
            'items': items,
            'total_amount': total_amount,
            'status': 'created',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        self.orders[order_id] = order_data
        
        self._log_operation("CREATE_ORDER", True, f"Order {order_id} created successfully")
        
        return ServiceResult(
            success=True,
            data=order_data
        )

# =============================================================================
# 2. PAYMENT PROCESSING SERVICE (Dummy with specific failure logic)
# =============================================================================
class PaymentProcessingService(BaseService):
    """💳 Payment Processing - Simulates payment, can randomly fail"""
    
    def __init__(self):
        super().__init__("PaymentProcessingService", failure_rate=0.0)  # Custom failure logic
        self.successful_payments = 0  # Track successful payments
        
    def execute(self, amount: float, customer_id: str, payment_method: str = "credit_card", currency: str = "USD", **kwargs) -> ServiceResult:
        """Process payment with specific failure pattern and currency display"""
        self._log_operation("PROCESS_PAYMENT", True, f"Amount: ${amount}, Customer: {customer_id}, Currency: {currency}")
        
        # Specific failure logic: fail after 3-4 successful payments
        if self.successful_payments >= 3:
            self._log_operation("PROCESS_PAYMENT", False, f"Payment failed after {self.successful_payments} successful payments")
            return ServiceResult(
                success=False,
                error_message=f"Payment processing failed - card declined after {self.successful_payments} successful transactions"
            )
        
        # Process payment successfully
        payment_id = str(uuid.uuid4())
        self.successful_payments += 1
        
        # Currency conversion for display (if not USD)
        usd_amount = amount
        local_amount = amount
        exchange_rate = 1.0
        
        if currency != "USD":
            # Simulate currency conversion rates
            conversion_rates = {
                'EUR': 0.85, 'GBP': 0.73, 'JPY': 110.0, 'CAD': 1.25, 
                'AUD': 1.35, 'CHF': 0.92, 'CNY': 6.45, 'INR': 74.5
            }
            if currency in conversion_rates:
                exchange_rate = conversion_rates[currency]
                local_amount = round(amount * exchange_rate, 2)
        
        payment_data = {
            'payment_id': payment_id,
            'amount': amount,
            'local_amount': local_amount,
            'currency': currency,
            'usd_amount': usd_amount,
            'exchange_rate': exchange_rate,
            'currency_display': f"${usd_amount:.2f} USD" + (f" ({currency} {local_amount:.2f})" if currency != "USD" else ""),
            'customer_id': customer_id,
            'payment_method': payment_method,
            'status': 'completed',
            'transaction_fee': round(amount * 0.029, 2),
            'successful_payment_count': self.successful_payments
        }
        
        self._log_operation("PROCESS_PAYMENT", True, f"Payment {payment_data['currency_display']} processed successfully (#{self.successful_payments})")
        
        return ServiceResult(
            success=True,
            data=payment_data
        )
    
    def reset_counter(self):
        """Reset payment counter for testing"""
        old_count = self.successful_payments
        self.successful_payments = 0
        self._log_operation("RESET_COUNTER", True, f"Payment counter reset from {old_count} to 0")

# =============================================================================
# 3. CURRENCY CONVERSION SERVICE (Real API)
# =============================================================================
class CurrencyConversionService(BaseService):
    """💱 Currency Conversion - Calls live exchange rate API"""
    
    def __init__(self):
        super().__init__("CurrencyConversionService", failure_rate=0.1)
        self.api_base_url = "https://v1.apiplugin.io/v1/currency"
        self.api_key = os.getenv("CURRENCY_API_KEY", "SJOX87Ur")
        
        # Fallback rates for when API is unavailable
        self.fallback_rates = {
            'USD': {'EUR': 0.85, 'GBP': 0.73, 'JPY': 110.0, 'CAD': 1.25},
            'EUR': {'USD': 1.18, 'GBP': 0.86, 'JPY': 129.0, 'CAD': 1.47},
            'GBP': {'USD': 1.37, 'EUR': 1.16, 'JPY': 150.0, 'CAD': 1.71}
        }
        
    def execute(self, amount: float, from_currency: str = "USD", to_currency: str = "USD", **kwargs) -> ServiceResult:
        """Convert currency using real API with fallback"""
        self._log_operation("CONVERT_CURRENCY", True, f"${amount} {from_currency} to {to_currency}")
        
        # If same currency, no conversion needed
        if from_currency == to_currency:
            return ServiceResult(
                success=True,
                data={
                    'original_amount': amount,
                    'converted_amount': amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'exchange_rate': 1.0,
                    'source': 'no_conversion_needed'
                }
            )
        
        # Try real API first
        try:
            if not self._simulate_failure():
                # Make actual API call to currency plugin
                rate = self._get_exchange_rate_from_api(from_currency, to_currency)
                converted_amount = round(amount * rate, 2)
                
                conversion_data = {
                    'original_amount': amount,
                    'converted_amount': converted_amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'exchange_rate': rate,
                    'source': 'live_api'
                }
                
                self._log_operation("CONVERT_CURRENCY", True, f"API call successful: Converted ${amount} {from_currency} to ${converted_amount} {to_currency}")
                
                return ServiceResult(
                    success=True,
                    data=conversion_data
                )
            else:
                raise Exception("API temporarily unavailable")
                
        except Exception as e:
            # Fallback to cached rates
            self._log_operation("CONVERT_CURRENCY", False, f"API failed, using fallback rates: {str(e)}")
            
            try:
                rate = self.fallback_rates.get(from_currency, {}).get(to_currency, 1.0)
                converted_amount = round(amount * rate, 2)
                
                conversion_data = {
                    'original_amount': amount,
                    'converted_amount': converted_amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'exchange_rate': rate,
                    'source': 'fallback_rates'
                }
                
                self._log_operation("CONVERT_CURRENCY", True, f"Fallback conversion: ${amount} {from_currency} to ${converted_amount} {to_currency}")
                
                return ServiceResult(
                    success=True,
                    data=conversion_data
                )
                
            except Exception as fallback_error:
                return ServiceResult(
                    success=False,
                    error_message=f"Currency conversion failed: {str(fallback_error)}"
                )
    
    def _get_exchange_rate_from_api(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate from real API using correct format from API documentation"""
        try:
            # Correct API format from their website documentation
            url = f"{self.api_base_url}/{self.api_key}/convert"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'ProDT-Currency-Service/1.0'
            }
            
            params = {
                "amount": "1",
                "from": from_currency,
                "to": to_currency
            }
            
            self._log_operation("API_CALL", True, f"Making API request to: {url} with params: {params}")
            
            # Make the actual HTTP request using the format from their documentation
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            self._log_operation("API_RESPONSE", True, f"API Response: {data}")
            
            # Extract rate from the known API response format
            # Response format should be similar to: {"query":{"from":"USD","to":"EUR","amount":"1"},"info":{"rate":...},"result":...}
            if 'result' in data:
                rate = float(data['result'])
            elif 'info' in data and 'rate' in data['info']:
                rate = float(data['info']['rate'])
            elif 'rate' in data:
                rate = float(data['rate'])
            elif 'conversion_rate' in data:
                rate = float(data['conversion_rate'])
            elif 'exchange_rate' in data:
                rate = float(data['exchange_rate'])
            else:
                # If response format is unexpected, log it and fall back
                self._log_operation("API_PARSE_ERROR", False, f"Unexpected API response format: {data}")
                raise Exception(f"Unexpected API response format: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            self._log_operation("API_SUCCESS", True, f"Retrieved live rate {rate} for {from_currency} to {to_currency}")
            return rate
            
        except requests.exceptions.RequestException as e:
            self._log_operation("API_ERROR", False, f"HTTP request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            self._log_operation("API_PARSE_ERROR", False, f"Failed to parse API response: {str(e)}")
            raise Exception(f"Failed to parse API response: {str(e)}")
        except Exception as e:
            self._log_operation("API_UNKNOWN_ERROR", False, f"Unknown API error: {str(e)}")
            raise Exception(f"Unknown API error: {str(e)}")
    
    def _get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate from fallback rates (for backward compatibility)"""
        return self.fallback_rates.get(from_currency, {}).get(to_currency, 1.0)

# =============================================================================
# 4. EMAIL NOTIFICATION SERVICE (Dummy)
# =============================================================================
class EmailNotificationService(BaseService):
    """✉️ Email Notification - Simulates sending a confirmation email"""
    
    def __init__(self):
        super().__init__("EmailNotificationService", failure_rate=0.15)
        
    def execute(self, recipient: str, subject: str = "Order Confirmation", message: str = "", **kwargs) -> ServiceResult:
        """Send email notification"""
        self._log_operation("SEND_EMAIL", True, f"To: {recipient}, Subject: {subject}")
        
        # Simulate failure
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="Email delivery failed - SMTP server unavailable"
            )
        
        # Simulate email sending
        email_id = str(uuid.uuid4())
        
        email_data = {
            'email_id': email_id,
            'recipient': recipient,
            'subject': subject,
            'message': message,
            'status': 'sent',
            'sent_at': '2024-01-01T00:00:00Z'
        }
        
        self._log_operation("SEND_EMAIL", True, f"Email sent successfully to {recipient}")
        
        return ServiceResult(
            success=True,
            data=email_data
        )

# =============================================================================
# 5. SHIPPING CONFIRMATION SERVICE (Dummy)
# =============================================================================
class ShippingConfirmationService(BaseService):
    """📦 Shipping Confirmation - Marks the order as shipped"""
    
    def __init__(self):
        super().__init__("ShippingConfirmationService", failure_rate=0.1)
        
    def execute(self, order_id: str, shipping_method: str = "standard", **kwargs) -> ServiceResult:
        """Confirm shipping for an order"""
        self._log_operation("CONFIRM_SHIPPING", True, f"Order: {order_id}, Method: {shipping_method}")
        
        # Simulate failure
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="Shipping confirmation failed - warehouse system unavailable"
            )
        
        # Generate tracking number
        tracking_number = f"TRK{random.randint(100000, 999999)}"
        
        shipping_data = {
            'order_id': order_id,
            'tracking_number': tracking_number,
            'shipping_method': shipping_method,
            'status': 'shipped',
            'estimated_delivery': '3-5 business days',
            'shipped_at': '2024-01-01T00:00:00Z'
        }
        
        self._log_operation("CONFIRM_SHIPPING", True, f"Shipping confirmed with tracking {tracking_number}")
        
        return ServiceResult(
            success=True,
            data=shipping_data
        )

# =============================================================================
# 6. CALL CENTER TRIGGER SERVICE (Dummy)
# =============================================================================
class CallCenterTriggerService(BaseService):
    """📞 Call Center Trigger - Simulates calling customer if payment or email fails"""
    
    def __init__(self):
        super().__init__("CallCenterTriggerService", failure_rate=0.05)
        
    def execute(self, customer_id: str, phone_number: str, reason: str = "payment_failure", **kwargs) -> ServiceResult:
        """Trigger call center to contact customer"""
        self._log_operation("TRIGGER_CALL", True, f"Customer: {customer_id}, Reason: {reason}")
        
        # Simulate failure (very low rate for call center)
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="Call center trigger failed - system unavailable"
            )
        
        # Generate call ticket
        ticket_id = f"CALL{random.randint(10000, 99999)}"
        
        call_data = {
            'ticket_id': ticket_id,
            'customer_id': customer_id,
            'phone_number': phone_number,
            'reason': reason,
            'priority': 'high' if reason == 'payment_failure' else 'medium',
            'status': 'queued',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        self._log_operation("TRIGGER_CALL", True, f"Call center ticket {ticket_id} created")
        
        return ServiceResult(
            success=True,
            data=call_data
        )

# =============================================================================
# 8. ORDER SUMMARY SERVICE (LLM-powered)
# =============================================================================
class OrderSummaryService(BaseService):
    """📋 Order Summary - Generates intelligent summary using LLM"""
    
    def __init__(self):
        super().__init__("OrderSummaryService", failure_rate=0.02)  # Very low failure rate
        
    def execute(self, config: dict, results: dict, **kwargs) -> ServiceResult:
        """Generate order summary using LLM"""
        self._log_operation("GENERATE_SUMMARY", True, f"Creating summary for workflow")
        
        # Simulate very rare failure
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="Summary generation temporarily unavailable"
            )
        
        # Calculate totals and gather information
        items = config.get('items', [])
        original_amount = config.get('original_amount', sum(item.get('price', 0) * item.get('quantity', 1) for item in items))
        converted_amount = config.get('converted_amount', original_amount)
        currency = config.get('currency', 'USD')
        target_currency = config.get('target_currency', currency)
        is_cross_border = config.get('cross_border_transaction', False)
        payment_country = config.get('payment_country', 'US')
        workflow_type = config.get('workflow_type', 'service_request')
        domain = config.get('domain', 'general')
        
        # Get payment details if available
        payment_data = results.get('payment', {}).get('data', {})
        
        # Get currency conversion details from the currency conversion service
        currency_data = results.get('currency_conversion', {}).get('data', {})
        exchange_rate = currency_data.get('exchange_rate', 1.0)
        conversion_source = currency_data.get('source', 'no_conversion')
        
        # Use the amounts from currency conversion service if available
        if currency_data:
            original_amount = currency_data.get('original_amount', original_amount)
            converted_amount = currency_data.get('converted_amount', converted_amount)
        
        # Create currency display with cross-border info
        if is_cross_border and currency != target_currency:
            currency_display = f"""**{original_amount:.2f} {currency}** → **{converted_amount:.2f} {target_currency}**
💱 *Exchange Rate: 1 {currency} = {exchange_rate:.4f} {target_currency}*  
🌍 *Cross-border transaction (Payment Country: {payment_country})*  
📡 *Conversion Source: {conversion_source}*"""
        else:
            currency_display = f"**{original_amount:.2f} {currency}**"
        
        # Count successful vs failed services
        successful_services = sum(1 for result in results.values() if result.get('success', False))
        total_services = len(results)
        
        # Generate intelligent summary based on workflow type
        if domain == 'travel':
            summary_text = f"""# 🧳 Travel Booking Summary

## ✅ **Service Details**
- **Service Type**: {workflow_type.replace('_', ' ').title()}
- **Total Cost**: **{currency_display}**
- **Processing Status**: {successful_services}/{total_services} services completed successfully

## 📋 **Items Booked**
"""
            for item in items:
                summary_text += f"- **{item.get('quantity', 1)}x {item.get('name', 'Service')}** - *{currency} {item.get('price', 0):.2f}*\n"
            
            summary_text += f"""
## 👤 **Customer Information**
- **Customer ID**: `{config.get('customer_id', 'N/A')}`
- **Contact Email**: {config.get('customer_email', 'N/A')}
- **Service Level**: {config.get('service_level', 'Standard')}
- **Processing Time**: ⚡ Completed in real-time
"""

        elif domain == 'ecommerce':
            summary_text = f"""# 🛒 Order Summary

## ✅ **Order Details**
- **Order Type**: {workflow_type.replace('_', ' ').title()}
- **Total Amount**: **{currency_display}**
- **Processing Status**: {successful_services}/{total_services} processes completed

## 📦 **Items Ordered**
"""
            for item in items:
                summary_text += f"- **{item.get('quantity', 1)}x {item.get('name', 'Product')}** - *{currency} {item.get('price', 0):.2f}*\n"
            
            summary_text += f"""
## 🚚 **Delivery & Payment**
- **Delivery Timeline**: {config.get('delivery_timeline', 'Standard shipping')}
- **Payment Method**: {config.get('payment_method', 'Credit Card')}
- **Customer ID**: `{config.get('customer_id', 'N/A')}`
- **Email**: {config.get('customer_email', 'N/A')}
"""

        else:
            # Generic summary for other domains
            summary_text = f"""# 📋 Service Summary

## ✅ **Service Details**
- **Service Type**: {workflow_type.replace('_', ' ').title()}
- **Domain**: {domain.title()}
- **Total Cost**: **{currency_display}**
- **Processing Status**: {successful_services}/{total_services} services completed

## 📋 **Services Requested**
"""
            for item in items:
                summary_text += f"- **{item.get('quantity', 1)}x {item.get('name', 'Service')}** - *{currency} {item.get('price', 0):.2f}*\n"
            
            summary_text += f"""
## 👤 **Customer Information**
- **Customer ID**: `{config.get('customer_id', 'N/A')}`
- **Contact**: {config.get('customer_email', 'N/A')}
- **Service Level**: {config.get('service_level', 'Standard')}
"""

        # Add service status details
        if successful_services < total_services:
            failed_services = []
            for service_name, result in results.items():
                if not result.get('success', False):
                    failed_services.append(service_name.replace('_', ' ').title())
            
            summary_text += f"""
## ⚠️ **Important Notice**
**{len(failed_services)} service(s) encountered issues:**
"""
            for service in failed_services:
                summary_text += f"- ❌ {service}\n"
            
            summary_text += f"""
🔄 **Retry options are available** for failed services using the retry buttons below.
"""

        # Add completion status
        if successful_services == total_services:
            summary_text += f"""
## 🎉 **Completion Status**
> ✅ **All services completed successfully!**  
> Your {workflow_type.replace('_', ' ')} is fully processed and ready.
"""

        summary_data = {
            'summary_id': str(uuid.uuid4()),
            'summary_text': summary_text,
            'workflow_type': workflow_type,
            'domain': domain,
            'total_amount': original_amount,
            'currency': currency,
            'currency_display': currency_display,
            'services_completed': successful_services,
            'services_total': total_services,
            'completion_rate': round((successful_services / total_services) * 100, 1) if total_services > 0 else 100,
            'customer_id': config.get('customer_id'),
            'generated_at': '2024-01-01T00:00:00Z'
        }
        
        self._log_operation("GENERATE_SUMMARY", True, f"Summary generated successfully - {successful_services}/{total_services} services completed")
        
        return ServiceResult(
            success=True,
            data=summary_data
        )
class SMSNotificationService(BaseService):
    """💬 SMS Notification - Sends SMS alert (simulated, can be replaced by Slack/real API optionally)"""
    
    def __init__(self):
        super().__init__("SMSNotificationService", failure_rate=0.12)
        
    def execute(self, phone_number: str, message: str, **kwargs) -> ServiceResult:
        """Send SMS notification"""
        self._log_operation("SEND_SMS", True, f"To: {phone_number}, Message: {message[:50]}...")
        
        # Simulate failure
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="SMS delivery failed - carrier network unavailable"
            )
        
        # Simulate SMS sending
        sms_id = str(uuid.uuid4())
        
        sms_data = {
            'sms_id': sms_id,
            'phone_number': phone_number,
            'message': message,
            'status': 'delivered',
            'sent_at': '2024-01-01T00:00:00Z',
            'cost': 0.05  # Cost per SMS
        }
        
        self._log_operation("SEND_SMS", True, f"SMS sent successfully to {phone_number}")
        
        return ServiceResult(
            success=True,
            data=sms_data
        )

# =============================================================================
# SERVICE REGISTRY
# =============================================================================
class ServiceRegistry:
    """Registry for all services"""
    
    def __init__(self):
        self.services = {
            'order_creation': OrderCreationService(),
            'payment_processing': PaymentProcessingService(),
            'currency_conversion': CurrencyConversionService(),
            'email_notification': EmailNotificationService(),
            'shipping_confirmation': ShippingConfirmationService(),
            'call_center_trigger': CallCenterTriggerService(),
            'sms_notification': SMSNotificationService(),
            'order_summary': OrderSummaryService()
        }
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """Get service by name"""
        return self.services.get(service_name)
    
    def list_services(self) -> Dict[str, str]:
        """List all available services"""
        return {
            name: service.__class__.__doc__ or service.__class__.__name__
            for name, service in self.services.items()
        }
    
    def reset_all_counters(self):
        """Reset all service counters for testing"""
        for service in self.services.values():
            if hasattr(service, 'reset_counter'):
                service.reset_counter()

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
def get_service_registry() -> ServiceRegistry:
    """Get the global service registry"""
    return ServiceRegistry()

def test_all_services():
    """Test all services to ensure they work"""
    registry = ServiceRegistry()
    
    print("Testing all services...")
    
    # Test Order Creation
    order_service = registry.get_service('order_creation')
    result = order_service.execute(
        customer_id="TEST001",
        items=[{"name": "Test Product", "price": 100.0, "quantity": 1}],
        channel="B2C"
    )
    print(f"Order Creation: {'✅' if result.success else '❌'}")
    
    # Test Payment Processing
    payment_service = registry.get_service('payment_processing')
    result = payment_service.execute(amount=100.0, customer_id="TEST001")
    print(f"Payment Processing: {'✅' if result.success else '❌'}")
    
    # Test Currency Conversion
    currency_service = registry.get_service('currency_conversion')
    result = currency_service.execute(amount=100.0, from_currency="USD", to_currency="EUR")
    print(f"Currency Conversion: {'✅' if result.success else '❌'}")
    
    # Test Email Notification
    email_service = registry.get_service('email_notification')
    result = email_service.execute(recipient="test@example.com", subject="Test")
    print(f"Email Notification: {'✅' if result.success else '❌'}")
    
    # Test Shipping Confirmation
    shipping_service = registry.get_service('shipping_confirmation')
    result = shipping_service.execute(order_id="TEST001")
    print(f"Shipping Confirmation: {'✅' if result.success else '❌'}")
    
    # Test Call Center Trigger
    call_service = registry.get_service('call_center_trigger')
    result = call_service.execute(customer_id="TEST001", phone_number="+1234567890")
    print(f"Call Center Trigger: {'✅' if result.success else '❌'}")
    
    # Test SMS Notification
    sms_service = registry.get_service('sms_notification')
    result = sms_service.execute(phone_number="+1234567890", message="Test SMS")
    print(f"SMS Notification: {'✅' if result.success else '❌'}")
    
    print("Service testing completed!")

if __name__ == "__main__":
    test_all_services()

