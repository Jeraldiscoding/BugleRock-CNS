import os
import time
import requests
import logging
import threading
from datetime import datetime

# Import components from Module C
from meeting_intelligence import analyze_meeting_transcript
from vector_store import store_transcript
from meeting_sync import sync_to_zoho, publish_meeting_event
from slack_interface import app, SLACK_BOT_TOKEN, SLACK_APP_TOKEN, send_draft_for_approval
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# Tie Everything Together
# ==========================================
def process_new_meeting(transcript: str, metadata: dict):
    """
    The orchestrator for Module C.
    1. Phase 1: Extract insights via Claude
    2. Phase 2: Embed chunks in ChromaDB
    3. Phase 3: Send follow-up draft to Slack
    4. Phase 4: Sync to CRM and publish exactly to the Event Bus
    """
    logger.info(f"--- Starting Processing for New Meeting: {metadata.get('company_name')} ---")
    
    # --- PHASE 1: Extraction ---
    try:
        insights = analyze_meeting_transcript(transcript)
        logger.info("Successfully extracted meeting insights via Claude.")
    except Exception as e:
        logger.error(f"Failed to analyze transcript: {e}")
        return

    # --- PHASE 2: ChromaDB Embeddings ---
    try:
        # Pass exactly what store_transcript expects natively
        # The underlying store_transcript will generate random IDs and handle mapping
        store_transcript(transcript, metadata)
        logger.info("Successfully embedded meeting context into Vector Store.")
    except Exception as e:
        logger.error(f"Failed to store transcript in ChromaDB: {e}")

    # --- PHASE 3: Slack Bot Interactivity ---
    # In a real app we'd map this to the specific reps channel, here we just check for an env var or dump it broadly
    try:
        # Warning: For testing, you must define TEST_SLACK_CHANNEL_ID in your .env or replace it below
        slack_channel = os.environ.get("TEST_SLACK_CHANNEL_ID", "C00000000") 
        if slack_channel != "C00000000":
            send_draft_for_approval(channel_id=slack_channel, draft_text=insights.follow_up_email_draft)
            logger.info("Fired Draft Email Blocks to Slack via Block Kit.")
        else:
            logger.warning("No TEST_SLACK_CHANNEL_ID found. Skipping Slack Draft notification.")
    except Exception as e:
        logger.error(f"Failed to send Slack follow up draft: {e}")

    # --- PHASE 4: Sync & Publish ---
    zoho_id = metadata.get("zoho_contact_id", "Z-UNKNOWN")
    sync_to_zoho(insights, contact_id=zoho_id)
    publish_meeting_event(insights, metadata)
    
    # --- PHASE 5: Tell the Dashboard! ---
    try:
        requests.post("http://localhost:8005/api/trigger", json={
            "client_name": "Bruce Wayne", # Hardcoded for dashboard demo visualization
            "module": "C",
            "new_status": "Advisor Action", # Moves the card on the Kanban board!
            "insight": insights.key_takeaways[0] if insights.key_takeaways else "Meeting analyzed successfully."
        })
        logger.info("Successfully sent update to the Dashboard!")
    except Exception as e:
        logger.error(f"Could not reach dashboard: {e}")
        
    logger.info("--- Meeting Pipeline Execution Complete ---")

# ==========================================
# Background Services (SocketMode)
# ==========================================
def start_slack_bot():
    """Runs the Slack bot in an isolated thread."""
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        logger.error("Missing Slack Tokens, cannot start SocketMode in background.")
        return
        
    logger.info("⚡️ Starting Slack Bolt App in Background Thread...")
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

# ==========================================
# Test Execution
# ==========================================
if __name__ == "__main__":
    # 1. Spin up the Background Slack Bot Thread (Allows /ask-bunglejungle to work globally while running this module)
    slack_thread = threading.Thread(target=start_slack_bot, daemon=True)
    slack_thread.start()
    
    # Give the bot 2 seconds to reliably connect to Slack WebSocket before dropping heavy stdout printing
    time.sleep(2)
    
    # 2. Mock exactly what the webhook in Phase 1 receives from Fireflies
    mock_payload = {
        "transcript": "Meeting with Acme about renewal. We discussed the Q3 performance. Client was happy but frustrated with recent billing delays. Action items: send proposal, schedule pricing call, and review the billing audit. We promised a 10% discount for next quarter to make up for the delays. Bob from Acme said they will renew if we fix it.",
        "company_name": "Acme Corp",
        "zoho_contact_id": "Z-456",
        "date": datetime.today().strftime('%Y-%m-%d')
    }
    
    logger.info("\n[SIMULATION STARTing in 3 Seconds] Kicking off a full test of the Phase 1 to 4 Pipeline...")
    time.sleep(3)
    
    process_new_meeting(transcript=mock_payload["transcript"], metadata=mock_payload)
    
    # Keep the main thread alive indefinitely so the Slack bot remains awake
    try:
        logger.info("\nSystem active. You can now test your Slack Slash commands in the workspace!")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Module C orchestrator.")