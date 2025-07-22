from groq import Groq
import json
import os
import uuid
from typing import Dict, Any, List

try:
    # Try relative imports first (when imported as a package)
    from .base_service import BaseService, ServiceResult
except ImportError:
    # Fall back to absolute imports (when run as standalone)
    from base_service import BaseService, ServiceResult

class GroqLLMService(BaseService):
    """Enhanced service for Groq LLM integration to parse generalized natural language workflows"""
    
    def __init__(self, api_key: str = None, model: str = "compound-beta"):
        super().__init__("GroqLLMService", failure_rate=0.1)
        self.api_key = api_key or os.getenv("GROQ_API_KEY_PROD4")
        self.model = model or os.getenv("GROQ_MODEL", "compound-beta")
        
        if not self.api_key:
            raise ValueError("Groq API key is required")
            
        self.client = Groq(api_key=self.api_key)
        
    def execute(self, user_input: str, **kwargs) -> ServiceResult:
        """Parse natural language input into workflow configuration for any domain"""
        self._log_operation("PARSE_WORKFLOW", True, f"Input: {user_input[:100]}...")
        
        # Simulate failure
        if self._simulate_failure():
            return ServiceResult(
                success=False,
                error_message="Groq LLM service temporarily unavailable"
            )
        
        try:
            # Enhanced prompt for generalized input processing
            system_prompt = """
                You are an intelligent workflow orchestration system that can handle various types of business processes beyond just travel and booking. 

                Analyze the user input and determine:
                1. What type of business process/workflow this represents
                2. Whether it's a B2C (individual customer) or Corporate (business) transaction
                3. What items/services are being requested
                4. Payment method preferences
                5. Any special requirements
                6. What workflow steps are appropriate for this domain

                The system can handle various domains including:
                - Travel & Hospitality (flights, hotels, car rentals)
                - E-commerce (product orders, subscriptions)
                - Professional Services (consulting, legal, accounting)
                - Event Management (conferences, meetings, catering)
                - Software/SaaS (licenses, subscriptions, support)
                - Healthcare (appointments, treatments, consultations)
                - Education (courses, training, certifications)
                - Real Estate (property rentals, purchases, services)
                - Financial Services (loans, investments, insurance)
                - Entertainment (tickets, memberships, experiences)
                - Food & Dining (restaurant reservations, catering, delivery)
                - Automotive (car services, rentals, maintenance)
                - Home Services (cleaning, repairs, maintenance)
                - Fitness & Wellness (gym memberships, personal training, spa services)

                For ANY type of business process, create a workflow configuration with these fields:
                {
                    "workflow_type": "string (e.g., 'travel_booking', 'product_order', 'service_request', 'subscription', 'appointment')",
                    "domain": "string (e.g., 'travel', 'ecommerce', 'professional_services', 'healthcare', etc.)",
                    "workflow_steps": [
                        "Analyze Request",
                        "Process Order",
                        "Handle Payment", 
                        "Arrange Service",
                        "Send Confirmation"
                    ],
                    "customer_id": "string (generate if not provided)",
                    "customer_email": "string (use default if not provided)",
                    "customer_phone": "string (use default if not provided)", 
                    "customer_address": "string (use appropriate default based on channel)",
                    "channel": "B2C or Corporate (infer from context)",
                    "items": [
                        {
                            "name": "string (describe the product/service)",
                            "category": "string (e.g., 'flight', 'product', 'service', 'subscription')",
                            "price": number (estimate reasonable price),
                            "quantity": number,
                            "duration": "string (if applicable, e.g., '1 month', '2 hours')",
                            "specifications": "string (any special requirements)"
                        }
                    ],
                    "currency": "string (detect from context: USD, EUR, GBP, JPY, CAD, AUD, etc. Default USD)",
                    "target_currency": "string (same as currency unless conversion specified)",
                    "payment_method": "string (infer from context: 'credit_card', 'wallet', 'bank_transfer', 'subscription')",
                    "booking_type": "string (e.g., 'standard', 'premium', 'enterprise', 'basic')",
                    "service_level": "string (e.g., 'standard', 'priority', 'express')",
                    "shipping_method": "string (if applicable: 'standard', 'express', 'digital', 'pickup')",
                    "delivery_timeline": "string (e.g., 'immediate', '1-3 days', '1 week')",
                    "special_requirements": "string (any additional notes)"
                }

                IMPORTANT - Workflow Steps Guidelines:
                - Step 1: Always start with user-friendly terms like "Review Request", "Check Details", "Verify Information" (NEVER use "Analyze" or "Parse")
                - Step 2-5: Customize based on domain:
                * Travel: "Book Travel", "Process Payment", "Confirm Booking", "Send Confirmation"
                * E-commerce: "Create Order", "Process Payment", "Arrange Shipping", "Send Confirmation" 
                * Services: "Schedule Service", "Process Payment", "Confirm Appointment", "Send Details"
                * Healthcare: "Book Appointment", "Process Payment", "Confirm Booking", "Send Reminders"
                * Subscriptions: "Setup Account", "Process Payment", "Activate Service", "Send Welcome"
                * Events: "Reserve Venue", "Process Payment", "Arrange Catering", "Send Details"
                * Financial: "Review Application", "Process Payment", "Setup Account", "Send Documents"

                Always provide exactly 5 steps that make sense for the specific domain. Use simple, customer-friendly language that any user can understand.

                Important guidelines:
                - If the input is unclear or too vague, make reasonable assumptions
                - Detect currency from context: locations (NYC=USD, Paris=EUR, London=GBP, Tokyo=JPY), explicit mentions, or business context
                - For corporate requests, prefer wallet payment method
                - For individual requests, prefer credit_card payment method
                - Estimate reasonable prices based on the service/product type
                - Include relevant categories and specifications
                - If it's a subscription or recurring service, note that in the workflow_type
                - For digital services, use 'digital' shipping method
                - For appointments/consultations, use 'N/A' for shipping
                - Currency detection examples:
                * "flight to Paris" → EUR
                * "hotel in London" → GBP  
                * "purchase in Tokyo" → JPY
                * "order to Canada" → CAD
                * "business in Australia" → AUD
                * Default to USD if unclear

                Return ONLY valid JSON, no additional text.
            """

            user_prompt = f"User Input: \"{user_input}\"\n\nGenerate the workflow configuration JSON:"

            # Call Groq API with connection error handling
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1200
                )
            except Exception as api_error:
                # Handle connection/API errors specifically
                error_msg = str(api_error)
                if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    self._log_operation("PARSE_WORKFLOW", False, "Error: Connection error.")
                    return ServiceResult(
                        success=False,
                        error_message="Connection error."
                    )
                else:
                    raise  # Re-raise other API errors
            
            # Parse the response
            llm_response = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                workflow_config = json.loads(llm_response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from the response
                import re
                
                # First try to extract from markdown code blocks
                markdown_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
                if markdown_match:
                    try:
                        workflow_config = json.loads(markdown_match.group(1))
                    except json.JSONDecodeError:
                        # If markdown extraction fails, try general JSON pattern
                        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                        if json_match:
                            try:
                                workflow_config = json.loads(json_match.group())
                            except json.JSONDecodeError:
                                raise ValueError(f"Could not parse JSON from LLM response. Response was: {llm_response[:500]}...")
                        else:
                            raise ValueError(f"No JSON found in LLM response. Response was: {llm_response[:500]}...")
                else:
                    # Try general JSON pattern
                    json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
                    if json_match:
                        try:
                            workflow_config = json.loads(json_match.group())
                        except json.JSONDecodeError:
                            raise ValueError(f"Could not parse JSON from LLM response. Response was: {llm_response[:500]}...")
                    else:
                        raise ValueError(f"No JSON found in LLM response. Response was: {llm_response[:500]}...")
            
            # Validate and set defaults for required fields
            required_fields = {
                'workflow_type': 'general_workflow',
                'domain': 'general',
                'workflow_steps': [
                    'Review Request',
                    'Process Order',
                    'Handle Payment',
                    'Arrange Service',
                    'Send Confirmation'
                ],
                'customer_id': f'CUST-{uuid.uuid4().hex[:8].upper()}',
                'customer_email': 'customer@example.com',
                'customer_phone': '+1234567890',
                'customer_address': '123 Default St, City, State',
                'channel': 'B2C',
                'items': [{'name': 'General Service', 'category': 'service', 'price': 100.0, 'quantity': 1}],
                'currency': 'USD',
                'target_currency': 'USD',
                'payment_method': 'credit_card',
                'booking_type': 'standard',
                'service_level': 'standard',
                'shipping_method': 'standard',
                'delivery_timeline': '1-3 days',
                'special_requirements': 'None'
            }
            
            # Ensure all required fields are present
            for field, default_value in required_fields.items():
                if field not in workflow_config or not workflow_config[field]:
                    workflow_config[field] = default_value
            
            # Ensure items is a list
            if not isinstance(workflow_config['items'], list):
                workflow_config['items'] = [workflow_config['items']]
            
            # Validate each item has required fields
            for item in workflow_config['items']:
                if 'name' not in item:
                    item['name'] = 'General Service'
                if 'category' not in item:
                    item['category'] = 'service'
                if 'price' not in item:
                    item['price'] = 100.0
                if 'quantity' not in item:
                    item['quantity'] = 1
                if 'duration' not in item:
                    item['duration'] = 'N/A'
                if 'specifications' not in item:
                    item['specifications'] = 'Standard specifications'
            
            # Ensure workflow_steps is a list with exactly 5 steps
            if 'workflow_steps' not in workflow_config or not isinstance(workflow_config['workflow_steps'], list):
                workflow_config['workflow_steps'] = required_fields['workflow_steps']
            elif len(workflow_config['workflow_steps']) != 5:
                # Pad or trim to exactly 5 steps
                steps = workflow_config['workflow_steps']
                if len(steps) < 5:
                    steps.extend(required_fields['workflow_steps'][len(steps):])
                else:
                    steps = steps[:5]
                workflow_config['workflow_steps'] = steps
            
            # Adjust address based on channel
            if workflow_config['channel'] == 'Corporate':
                workflow_config['customer_address'] = '123 Corporate Drive, Business City, State'
                workflow_config['payment_method'] = 'wallet'
                workflow_config['customer_id'] = f'CORP-{uuid.uuid4().hex[:8].upper()}'
            
            self._log_operation("PARSE_WORKFLOW", True, "Workflow configuration generated successfully")
            
            return ServiceResult(
                success=True,
                data={
                    "workflow_config": workflow_config,
                    "llm_response": llm_response,
                    "domain_detected": workflow_config.get('domain', 'general'),
                    "workflow_type": workflow_config.get('workflow_type', 'general_workflow'),
                    "parsed_successfully": True
                }
            )
            
        except Exception as e:
            self._log_operation("PARSE_WORKFLOW", False, f"Error: {str(e)}")
            return ServiceResult(
                success=False,
                error_message=f"Failed to parse workflow: {str(e)}"
            )
    
    def generate_workflow_suggestions(self, partial_input: str, **kwargs) -> ServiceResult:
        """Generate workflow suggestions based on partial input across multiple domains"""
        self._log_operation("GENERATE_SUGGESTIONS", True, f"Partial input: {partial_input}")
        
        try:
            system_prompt = """Generate 4-6 diverse workflow suggestions based on the partial user input. 
Include suggestions from different business domains like:
- Travel & Hospitality
- E-commerce & Shopping
- Professional Services
- Healthcare & Wellness
- Entertainment & Events
- Software & Technology

Each suggestion should be a complete, actionable workflow description.
Return as a JSON array of strings."""
            
            user_prompt = f"Partial input: \"{partial_input}\"\n\nGenerate diverse workflow suggestions:"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            
            try:
                suggestions = json.loads(suggestions_text)
            except json.JSONDecodeError:
                # Fallback to diverse domain suggestions
                suggestions = [
                    "Book a premium flight for business travel to Europe",
                    "Order enterprise software licenses for the development team",
                    "Schedule a corporate wellness consultation for employees",
                    "Reserve conference room and catering for quarterly meeting",
                    "Purchase bulk office supplies for the marketing department",
                    "Book professional photography services for product launch"
                ]
            
            # Ensure we have a list
            if not isinstance(suggestions, list):
                suggestions = [suggestions] if suggestions else []
            
            return ServiceResult(
                success=True,
                data={"suggestions": suggestions}
            )
            
        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to generate suggestions: {str(e)}"
            )

    def analyze_domain(self, user_input: str) -> ServiceResult:
        """Analyze the domain/category of the user input"""
        try:
            system_prompt = """Analyze the user input and determine the business domain/category.
Return a JSON object with:
{
    "domain": "primary domain (e.g., travel, ecommerce, healthcare, etc.)",
    "confidence": "high/medium/low",
    "keywords": ["list", "of", "key", "terms"],
    "suggested_workflow_type": "recommended workflow type"
}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            analysis_text = response.choices[0].message.content.strip()
            analysis = json.loads(analysis_text)
            
            return ServiceResult(
                success=True,
                data=analysis
            )
            
        except Exception as e:
            return ServiceResult(
                success=False,
                error_message=f"Failed to analyze domain: {str(e)}"
            )

