"""
PharmaPOS NG - Payment Gateway Integration

This module handles interactions with external payment gateways (Paystack, Flutterwave).
"""

import abc
import json
import requests
from typing import Dict, Any, Optional
from decimal import Decimal

class PaymentGateway(abc.ABC):
    """Abstract base class for payment gateways."""

    @abc.abstractmethod
    def initialize_transaction(self, email: str, amount: Decimal, reference: str) -> Dict[str, Any]:
        """Initialize a transaction and return the authorization URL/details.
        
        Args:
            email: Customer email
            amount: Amount to charge
            reference: Unique transaction reference
            
        Returns:
            Dict containing 'authorization_url', 'access_code', etc.
        """
        pass

    @abc.abstractmethod
    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        """Verify the status of a transaction.
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            Dict containing 'status' (success/failed/pending), 'amount', 'gateway_response'
        """
        pass


class PaystackGateway(PaymentGateway):
    """Paystack implementation."""
    
    BASE_URL = "https://api.paystack.co"

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initialize_transaction(self, email: str, amount: Decimal, reference: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/transaction/initialize"
        # Paystack amount is in kobo
        amount_kobo = int(amount * 100)
        
        payload = {
            "email": email,
            "amount": amount_kobo,
            "reference": reference,
            "callback_url": "http://localhost:8000/callback", # Not used in desktop app but required
            "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"]
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data["status"]:
                return {
                    "authorization_url": data["data"]["authorization_url"],
                    "access_code": data["data"]["access_code"],
                    "reference": data["data"]["reference"]
                }
            else:
                raise Exception(f"Paystack Error: {data.get('message')}")
                
        except Exception as e:
            print(f"Paystack Init Error: {e}")
            raise

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/transaction/verify/{reference}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data["status"]:
                tx_data = data["data"]
                status = "success" if tx_data["status"] == "success" else "pending"
                if tx_data["status"] == "failed":
                    status = "failed"
                    
                return {
                    "status": status,
                    "amount": Decimal(tx_data["amount"]) / 100,
                    "gateway_response": json.dumps(tx_data)
                }
            else:
                raise Exception(f"Paystack Verify Error: {data.get('message')}")
                
        except Exception as e:
            print(f"Paystack Verify Error: {e}")
            # Return pending on network error to allow retry
            return {"status": "pending", "gateway_response": str(e)}


class FlutterwaveGateway(PaymentGateway):
    """Flutterwave implementation."""
    
    BASE_URL = "https://api.flutterwave.com/v3"

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initialize_transaction(self, email: str, amount: Decimal, reference: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/payments"
        
        payload = {
            "tx_ref": reference,
            "amount": str(amount),
            "currency": "NGN",
            "redirect_url": "http://localhost:8000/callback",
            "customer": {
                "email": email,
                "name": "PharmPos Customer"
            },
            "customizations": {
                "title": "PharmPos Payment",
                "description": "Payment for items"
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "success":
                return {
                    "authorization_url": data["data"]["link"],
                    "reference": reference
                }
            else:
                raise Exception(f"Flutterwave Error: {data.get('message')}")
                
        except Exception as e:
            print(f"Flutterwave Init Error: {e}")
            raise

    def verify_transaction(self, reference: str) -> Dict[str, Any]:
        # Flutterwave verify by transaction ID is preferred, but we use tx_ref query here
        # Note: In production, we might need to query by tx_ref specifically
        # For v3, we can verify by transaction ID. But we only have reference.
        # We'll use the transactions endpoint with tx_ref filter
        
        url = f"{self.BASE_URL}/transactions"
        params = {"tx_ref": reference}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "success" and data["data"]:
                # Get the first match
                tx = data["data"][0]
                status = "success" if tx["status"] == "successful" else "pending"
                if tx["status"] == "failed":
                    status = "failed"
                    
                return {
                    "status": status,
                    "amount": Decimal(tx["amount"]),
                    "gateway_response": json.dumps(tx)
                }
            else:
                # If not found, it might be pending or invalid
                return {"status": "pending", "gateway_response": "Transaction not found yet"}
                
        except Exception as e:
            print(f"Flutterwave Verify Error: {e}")
            return {"status": "pending", "gateway_response": str(e)}

def get_gateway(gateway_name: str, config: Dict[str, Any]) -> Optional[PaymentGateway]:
    """Factory to get gateway instance."""
    gateways_config = config.get("payment_gateways", {})
    
    if gateway_name == "paystack":
        secret = gateways_config.get("paystack", {}).get("secret_key")
        if secret:
            return PaystackGateway(secret)
            
    elif gateway_name == "flutterwave":
        secret = gateways_config.get("flutterwave", {}).get("secret_key")
        if secret:
            return FlutterwaveGateway(secret)
            
    return None
