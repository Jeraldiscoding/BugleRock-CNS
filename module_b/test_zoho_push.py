import logging
from .zoho_client_live import ZohoClientLive

logging.basicConfig(level=logging.INFO)

def test_zoho_connection():
    print("Initializing Zoho Live Client...")
    client = ZohoClientLive()
    
    print("\n--- Testing Contact Creation ---")
    contact_data = {
        "First_Name": "Jerald",
        "Last_Name": "Lim",
        "Email": "jeraldlim123444@buglerock.com",
        "Description": "Test Contact Auto-Generated from API Pipeline"
    }
    
    contact_id = client.upsert_contact(contact_data)
    
    if contact_id:
        print(f"[SUCCESS] Contact fully created in Zoho Cloud! CRM ID: {contact_id}")
        
        print("\n--- Testing Deal Creation linked to Contact ---")
        deal_data = {
            "Deal_Name": "Project Phoenix - Enterprise Deal",
            "Stage": "Value Proposition",
            "Contact_Name": contact_id
        }
        deal_id = client.create_deal(deal_data)
        if deal_id:
            print(f"[SUCCESS] Deal created and linked! Deal ID: {deal_id}")
            
    else:
        print("❌ Failed to create contact, check logs above.")

if __name__ == "__main__":
    test_zoho_connection()
