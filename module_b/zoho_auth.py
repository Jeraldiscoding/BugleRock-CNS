import os
import requests
import json
import logging
import time
from dotenv import load_dotenv
from requests.exceptions import RequestException

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class ZohoAuthenticator:
    """Handles OAuth 2.0 Access Token generation using the stored Refresh Token."""
    
    # Class-level cache to share token across instances during app lifecycle
    _cached_token = None
    _token_expiry = 0

    def __init__(self):
        self.client_id = os.environ.get("ZOHO_CLIENT_ID")
        self.client_secret = os.environ.get("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.environ.get("ZOHO_REFRESH_TOKEN")
        self.domain = "https://accounts.zoho.com" # Defaults to US domain

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.error("Missing Zoho API credentials in .env file!")

    def get_access_token(self):
        """Exchange the refresh token for a fresh access token."""
        # Use cached token if valid (buffer of 60 seconds)
        if ZohoAuthenticator._cached_token and time.time() < ZohoAuthenticator._token_expiry - 60:
            return ZohoAuthenticator._cached_token

        url = f"{self.domain}/oauth/v2/token"
        
        payload = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "access_token" in data:
                logger.info("Successfully generated new Zoho Access Token.")
                ZohoAuthenticator._cached_token = data["access_token"]
                # Usually valid for 1 hour (3600 seconds)
                expires_in = data.get("expires_in", 3600)
                ZohoAuthenticator._token_expiry = time.time() + expires_in
                return ZohoAuthenticator._cached_token
            else:
                logger.error(f"Failed to get access token. Response: {data}")
                return None
                
        except RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            return None

if __name__ == "__main__":
    auth = ZohoAuthenticator()
    token = auth.get_access_token()
    if token:
        print(f"\nYour fresh Access Token is generated successfully! First 15 characters: {token[:15]}...")
