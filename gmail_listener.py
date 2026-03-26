import os
import time
import email
import imaplib
import logging
import requests
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
WEBHOOK_URL = "http://localhost:8000/api/gmail-webhook"

def clean_header(header_text):
    """Decodes email headers (like subject and sender) correctly."""
    if not header_text:
        return ""
    
    decoded_parts = decode_header(header_text)
    result = ""
    for content, charset in decoded_parts:
        if isinstance(content, bytes):
            result += content.decode(charset or 'utf-8', errors='ignore')
        else:
            result += content
    return result

def get_email_body(msg):
    """Extracts the plain text body from the email."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Look for plain text parts that aren't attachments
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    return part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    continue
    else:
        # Not multipart, just extract the payload
        try:
            return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
            
    return "No plain text body found."

def listen_to_inbox():
    """Connects to Gmail and polls the INBOX for UNSEEN messages."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logger.error("Starting aborted: GMAIL_ADDRESS or GMAIL_APP_PASSWORD is not set in your .env file!")
        return

    logger.info(f"Connecting to imap.gmail.com as {GMAIL_ADDRESS}...")
    
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        logger.info("Successfully connected and authenticated to Gmail!")
    except Exception as e:
        logger.error(f"Failed to connect or login: {e}")
        return

    logger.info("Listening for new emails every 10 seconds. Press Ctrl+C to stop.")

    while True:
        try:
            # Select INBOX (You need to select every time to refresh the mailbox state)
            imap.select("INBOX")
            
            # Search for UNSEEN emails
            status, response = imap.search(None, "UNSEEN")
            if status != "OK":
                logger.error("Failed to search INBOX.")
                time.sleep(10)
                continue
                
            unread_msg_nums = response[0].split()
            
            for msg_num in unread_msg_nums:
                logger.info(f"Found new unseen email! Message ID: {msg_num.decode('utf-8')}")
                
                # Fetch the email using BODY.PEEK[] so it doesn't get marked as read
                res, msg_data = imap.fetch(msg_num, "(BODY.PEEK[])")
                if res != "OK":
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject = clean_header(msg.get("Subject"))
                        sender = clean_header(msg.get("From"))
                        body = get_email_body(msg)
                        
                        logger.info(f"Processing Email -> From: {sender} | Subject: {subject}")
                        
                        # Pack into exact schema expected by Module A
                        payload = {
                            "sender": sender,
                            "subject": subject,
                            "body": body,
                            "attachments": []
                        }
                        
                        # Send to local FastAPI webhook
                        try:
                            wh_resp = requests.post(WEBHOOK_URL, json=payload, timeout=60)
                            if wh_resp.status_code == 200:
                                data = wh_resp.json()
                                extractions = data.get("extractions", [])
                                
                                dest_folder = "AI_Processed" # Default destination
                                
                                if extractions:
                                    ext_type = extractions[0].get("type", "").lower()
                                    ext_urgency = extractions[0].get("urgency", "").lower()
                                    
                                    logger.info(f"AI Classification -> Type: {ext_type} | Urgency: {ext_urgency}")
                                    
                                    # Route based on classification
                                    if ext_urgency == "high":
                                        dest_folder = "Urgent"
                                    elif "prospect" in ext_type:
                                        dest_folder = "Prospects"
                                    elif "internal" in ext_type:
                                        dest_folder = "Internal"
                                    elif "client" in ext_type:
                                        dest_folder = "Clients"
                                
                                logger.info(f"Routing email to folder: {dest_folder}")
                                
                                # Attempt to create the folder if it doesn't exist gently
                                imap.create(dest_folder)
                                
                                # Move email to the destination folder
                                copy_res, _ = imap.copy(msg_num, dest_folder)
                                if copy_res == "OK":
                                    # Store "\Deleted" flag to delete the original from INBOX
                                    imap.store(msg_num, '+FLAGS', '\\Deleted')
                                    imap.expunge() # Physically remove it so it's formally completely moved
                                    logger.info(f"Successfully moved to '{dest_folder}' keeping Unread status!")
                                else:
                                    logger.error(f"Failed to copy email to folder {dest_folder}")
                            else:
                                logger.error(f"Webhook failed with status {wh_resp.status_code}: {wh_resp.text}")
                        except Exception as e:
                            logger.error(f"Could not connect to FastAPI server. Is it running? {e}")

            time.sleep(10)

        except Exception as e:
            logger.error(f"Lost connection or error occurred: {e}")
            logger.info("Attempting to reconnect in 10 seconds...")
            time.sleep(10)
            try:
                imap = imaplib.IMAP4_SSL("imap.gmail.com")
                imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            except:
                pass


if __name__ == "__main__":
    listen_to_inbox()
