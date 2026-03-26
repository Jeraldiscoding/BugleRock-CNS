import requests
import json

# ==============================================================
# INSTRUCTIONS:
# Paste your Client ID, Client Secret, and Grant Token below.
# If your Zoho account is in a different region, change the domain:
# .com (US), .eu (Europe), .in (India), .com.au (Australia), etc.
# ==============================================================

ZOHO_DOMAIN = "https://accounts.zoho.com" # Change if in .eu, .in, etc.
TOKEN_URL = f"{ZOHO_DOMAIN}/oauth/v2/token"

# PASTE YOUR CREDENTIALS HERE:
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
GRANT_TOKEN = "YOUR_GRANT_TOKEN"

# Note: If your Zoho developer console app requires a Redirect URI, 
# you might need to add '"redirect_uri": "YOUR_REDIRECT_URI"' below.
payload = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": GRANT_TOKEN
}

def get_refresh_token():
    print(f"Sending POST request to {TOKEN_URL}...")
    
    # We use 'data=' instead of 'json=' as Zoho requires form-encoded payload
    response = requests.post(TOKEN_URL, data=payload)
    
    print("\n--- ZOHO API RESPONSE ---")
    print(f"Status Code: {response.status_code}")
    
    try:
        response_json = response.json()
        print(json.dumps(response_json, indent=4))
        
        if "refresh_token" in response_json:
            print("\n✅ SUCCESS! Save your 'refresh_token' securely!")
        else:
            print("\n❌ Didn't find refresh_token. "
                  "Grant tokens expire quickly (usually 1-2 mins) and can only be used once. "
                  "You might need to generate a new grant token in the Zoho Console!")
            
    except Exception as e:
        print("Failed to parse JSON response. Raw text was:")
        print(response.text)

if __name__ == "__main__":
    get_refresh_token()
