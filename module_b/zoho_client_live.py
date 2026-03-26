import logging
import json
from typing import Dict
from .zoho_auth import ZohoAuthenticator
import requests

logger = logging.getLogger(__name__)

class ZohoClientLive:
    """Live implementation of the Zoho CRM API client."""

    def __init__(self):
        self.auth = ZohoAuthenticator()
        # By default API URL sits on crm.zoho.com for US region
        self.api_base_url = "https://www.zohoapis.com/crm/v6"

    def _get_headers(self) -> dict:
        access_token = self.auth.get_access_token()
        if not access_token:
            raise ValueError("Could not obtain a Zoho API Access Token")
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }

    def _call(self, module_name: str, payload: Dict):
        """Generic method to push data to any Zoho CRM Module (Contacts, Deals, etc.)"""
        url = f"{self.api_base_url}/{module_name}"
        
        # Zoho expects a list of dictionaries nested under the "data" key
        zoho_payload = {"data": [payload]}

        logger.info(f"Pushing to Zoho Module: {module_name}")
        response = requests.post(url, headers=self._get_headers(), json=zoho_payload)

        try:
            response_data = response.json()
            if response.status_code in [200, 201]:
                # Zoho usually returns status inside data list element
                if response_data.get("data") and response_data["data"][0].get("code") == "SUCCESS":
                    logger.info(f"Success! Zoho {module_name} ID: {response_data['data'][0]['details']['id']}")
                    return response_data['data'][0]['details']['id']
            logger.error(f"Zoho API Error ({response.status_code}): {json.dumps(response_data, indent=2)}")
        except Exception as e:
            logger.error(f"Failed to parse Zoho API Response: {e}")
        
        return None

    def upsert_contact(self, contact_data: Dict) -> str:
        """Create or update a contact in Zoho"""
        payload = {
            "Email": contact_data.get("Email"),
            "Last_Name": contact_data.get("Last_Name", "Unknown"), 
            "First_Name": contact_data.get("First_Name", ""),
            "Description": contact_data.get("Description", "")
        }
        # Zoho required Last_Name basically at all times for standard configurations.
        zoho_id = self._call("Contacts", payload)
        return zoho_id
        
    def create_deal(self, deal_data: Dict) -> str:
        """Create a new Deal/Opportunity"""
        payload = {
            "Deal_Name": deal_data.get("Deal_Name", "New Deal"),
            "Stage": deal_data.get("Stage", "Needs Analysis"),
            "Closing_Date": deal_data.get("Closing_Date", "2026-12-31"),
            "Description": deal_data.get("Description", "")
        }
        
        if "Contact_Name" in deal_data:
            payload["Contact_Name"] = deal_data["Contact_Name"] # Reference to standard Contact ID
            
        return self._call("Deals", payload)
        
    def create_task(self, task_data: Dict) -> str:
        """Create an Action Item / Task"""
        payload = {
            "Subject": task_data.get("Subject", "New Task"),
            "Status": "Not Started",
            "Description": task_data.get("Description", "")
        }
        if "Who_Id" in task_data:
            payload["Who_Id"] = task_data["Who_Id"] # Associate to standard contact
            
        return self._call("Tasks", payload)

