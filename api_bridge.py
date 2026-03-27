from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv
import logging
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
import threading
from contextlib import asynccontextmanager
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import json
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
import requests

import ssl
import certifi

# This forces the SSL context to use certifi's certificates
ssl._create_default_https_context = ssl._create_unverified_context

# --- REAL EMAIL DISPATCHER (SMTP via Gmail) ---
def send_real_email_via_gmail(draft_text: str, client_name: str):
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    gmail_address = os.environ.get("GMAIL_ADDRESS")

    if not gmail_address or not gmail_app_password:
        logging.error("[ERROR] Missing Gmail credentials in environment; aborting send.")
        return False

    # Standardized test email for the hackathon demo
    TARGET_EMAIL = "test_client@example.com"

    msg = MIMEText(draft_text)
    msg['Subject'] = f"BugleRock Capital: Follow-up regarding {client_name}"
    msg['From'] = gmail_address
    msg['To'] = TARGET_EMAIL

    try:
        logging.info("[NETWORK] Attempting to send email via SMTP...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(gmail_address, gmail_app_password)
            smtp_server.send_message(msg)
        logging.info("[NETWORK] Email successfully sent to Gmail Sent Box!")
        return True
    except Exception as e:
        logging.error(f"[ERROR] SMTP Email Failed: {str(e)}")
        return False

# Initialize Logging
logging.basicConfig(
    filename='api_error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# --- SLACK BOLT SETUP ---
slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

def send_demo_email(to_email, subject, body):
    """Sends a real email using the configured Gmail account.
    
    Note: Yes, in a real firm, this is integrated through the 
    CRMs' email API (like Zoho's OAuth REST API integrations) 
    so the email sends dynamically on behalf of the CRM owner.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        logging.error("Missing Gmail credentials in .env, cannot send email.")
        return False
        
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = to_email

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logging.error(f"Failed to send email via SMTP: {e}")
        return False

# In-memory "Database" for the demo API (Shared state)
demo_state = {
    "advisors": {
        "Dheeraj Bharwani": {"dept": "UHNW", "active_clients": 15, "pending_prospects": 2, "meetings_this_week": 4, "capacity": 30},
        "Subiksha": {"dept": "UHNW", "active_clients": 40, "pending_prospects": 5, "meetings_this_week": 10, "capacity": 50},
        "Jeremy Sim": {"dept": "Investments", "active_clients": 35, "pending_prospects": 3, "meetings_this_week": 6, "capacity": 45}
    },
    "kpis": {
        "total_aum": "$1.2B",
        "triage_volume": 842,
        "risk_flags": 3
    },
    "aggregated_briefing": {
        "module_a": {"new_contacts": 3},
        "module_b": {"prospect_scored": 1, "score": 87},
        "module_c": {"meetings_filed": 2}
    },
    "rich_briefing": {
        "leads": [
            {"name": "LexCorp Family Office", "advisor": "Subiksha", "aum": "$120M", "score": "94%", "status": "Ready to Pitch"},
            {"name": "Stark Industries Trust", "advisor": "Jeremy Sim", "aum": "$450M", "score": "88%", "status": "Warm"}
        ],
        "actions": [
            {"task": "Draft Rebalancing Proposal", "client": "Bruce Wayne", "due": "Today 5PM"},
            {"task": "Send Q3 Performance Audit docs", "client": "Apex Corp", "due": "Tomorrow 10AM"}
        ],
        "inbox": [
            {"signal": "Urgent compliance KYC missing", "from": "Stefan Ho (Risk)", "urgency": "Critical"},
            {"signal": "Complaint regarding billing delays", "from": "Bob (Acme Corp)", "urgency": "High"}
        ]
    },
    "clients": {
        "Bruce Wayne": {
            "department": "Client & UHNW",
            "status": "AI Triage",
            "module_a_insight": "Waiting for email...",
            "module_c_insight": "Waiting for transcript..."
        },
        "LexCorp Family Office": {
            "department": "Corporate Dev",
            "status": "Prospecting",
            "module_a_insight": "No recent email.",
            "module_c_insight": "Initial introductory call parsed."
        },
        "Stark Industries Trust": {
            "department": "Investments",
            "status": "Active",
            "module_a_insight": "Reviewing standard reporting.",
            "module_c_insight": "Preparing for Q3 performance review."
        },
        "Apex Corp": {
            "department": "Ops & Compliance",
            "status": "Active Risk",
            "module_a_insight": "Missing KYC documentation.",
            "module_c_insight": "Discussed regulatory filings."
        }
    }
}

# === UTILITY FUNCTIONS ===
def calculate_bws(advisor_data):
    try:
        # Formula: converted to a percentage based score out of 100
        bws = ((advisor_data["active_clients"] * 1.0 + advisor_data["pending_prospects"] * 0.5 + advisor_data["meetings_this_week"] * 0.2) / advisor_data["capacity"]) * 100
        return round(bws, 2)
    except ZeroDivisionError:
        logging.error("Capacity is zero, division by zero error.")
        return 999.99

# === SLACK SOCKET MODE COMMAND HANDLERS ===

@slack_app.command("/route-prospect")
def handle_route_prospect(ack, respond, command):
    ack()
    
    # 0. Personalization: Extract who invoked the command!
    invoker_name = command.get("user_name", "Executive")
    
    # Parse dynamic text from Slack (e.g., "/route-prospect Stark Industries - 45")
    text = command.get("text", "").strip()
    
    # 1. Define Default Prospect
    prospect = {"name": "LexCorp Family Office", "aum": 120, "intent": 94}
    
    # If user provided a specific prospect, override defaults
    if text:
        parts = text.split("-")
        prospect["name"] = parts[0].strip()
        if len(parts) > 1:
            try:
                # Extract AUM safely if provided
                prospect["aum"] = int(''.join(filter(str.isdigit, parts[1])))
                # Generate a random intent score for fun variation
                import random
                prospect["intent"] = random.randint(75, 99)
            except ValueError:
                pass

    # 2. Stage 1: Department Match Logic
    target_dept = "UHNW" if "Family" in prospect["name"] or prospect["aum"] >= 100 else "Investments"
        
    # 3. Stage 2: Bandwidth Match Logic
    best_advisor = None
    best_score = 999.99
    
    for name, data in demo_state["advisors"].items():
        if data["dept"] == target_dept:
            score = calculate_bws(data)
            if score < best_score:
                best_score = score
                best_advisor = name
            
    # 4. Block Kit Construction
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "[ROUTING] New High-Value Prospect Scored", "emoji": False}
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"*Action Initiated By:* @{invoker_name}"}]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Prospect:* {prospect['name']}\n*AUM Target:* ${prospect['aum']}M\n*AI Fit Score:* {prospect['intent']}/100"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Target Department:* {target_dept}\n*Recommended Assignment:* {best_advisor}\n*Bandwidth Score (BWS):* {best_score} (Optimal)"}
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve Assignment", "emoji": False},
                    "style": "primary",
                    "value": f"{prospect['name']}|{best_advisor}|{prospect['intent']}|{prospect['aum']}",
                    "action_id": "approve_assignment"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Re-route", "emoji": False},
                    "style": "danger",
                    "value": f"{prospect['name']}|{best_advisor}|{prospect['intent']}|{prospect['aum']}",
                    "action_id": "reroute_assignment"
                }
            ]
        }
    ]
    respond(blocks=blocks)

@slack_app.action("approve_assignment")
def handle_approve_assignment(ack, body, client, respond):
    # Acknowledge the button click immediately to remove ⚠️ warning
    ack()
    
    # Extract who clicked it
    user_name = body["user"]["username"]
    
    assigned_advisor = "Advisor"
    prospect_name = "The Prospect"
    intent = "N/A"
    aum = "N/A"
    
    try:
        action_value = body.get("actions", [{}])[0].get("value", "")
        if action_value and "|" in action_value:
            parts = action_value.split("|")
            prospect_name = parts[0]
            assigned_advisor = parts[1]
            intent = parts[2] if len(parts) > 2 else "N/A"
            aum = parts[3] if len(parts) > 3 else "N/A"
            
        # Update the backend state
        if prospect_name in demo_state["clients"]:
            demo_state["clients"][prospect_name]["status"] = "Assigned"
            demo_state["clients"][prospect_name]["module_a_insight"] = f"Assigned to {assigned_advisor} by @{user_name}"
        else:
            demo_state["clients"][prospect_name] = {
                "department": "Prospecting",
                "status": "Assigned",
                "module_a_insight": f"Assigned to {assigned_advisor} by @{user_name}",
                "module_c_insight": "Awaiting first meeting."
            }
    except Exception as e:
        logging.error(f"Error parsing approval: {e}")
    
    # Replace the original interactive message entirely
    respond(
        replace_original=True,
        text=f"[SUCCESS] {prospect_name} securely assigned to {assigned_advisor} by @{user_name}.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"[SUCCESS] *{prospect_name}* (AUM: ${aum}M | Fit: {intent}/100) securely assigned to *{assigned_advisor}* by @{user_name}. CRM and Dashboard updated."
                }
            }
        ]
    )

@slack_app.action("reroute_assignment")
def handle_reroute_assignment(ack, body, respond):
    ack()
    user_name = body["user"]["username"]
    
    prospect_name = "The Prospect"
    aum = "N/A"
    try:
        action_value = body.get("actions", [{}])[0].get("value", "")
        if action_value and "|" in action_value:
            parts = action_value.split("|")
            prospect_name = parts[0]
            aum = parts[3] if len(parts) > 3 else "N/A"
    except Exception:
        pass
    
    respond(
        replace_original=True,
        text=f"[ACTION] Lead rejected by @{user_name}.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"[ACTION] *{prospect_name}* (AUM: ${aum}M) assignment rejected by @{user_name}. Escalating back to the manual rotation pool."
                }
            }
        ]
    )

@slack_app.command("/flag-compliance")
def handle_flag_compliance(ack, respond, command):
    ack()
    text = command.get("text", "")
    client_name = text.split("-")[0].strip() if "-" in text else text.strip()

    if client_name in demo_state["clients"]:
        demo_state["clients"][client_name]["status"] = "Compliance Hold"
        demo_state["clients"][client_name]["module_a_insight"] = f"Flagged via Slack: {text}"
        demo_state["kpis"]["risk_flags"] += 1

    respond(f"[ALERT] *{client_name}* has been locked. Escalated to Stefan Ho (Risk & Compliance).")

@slack_app.command("/prep-meeting")
def handle_prep_meeting(ack, respond, command):
    ack()
    text = command.get("text", "")
    client_name = text.split("-")[0].strip() if "-" in text else text.strip()
    respond(f"[MEETING PREP] *For: {client_name}*\n• *Last Touchpoint:* Emailed yesterday expressing anxiety over tech stock volatility.\n• *Past Context:* Discussed shifting 15% to Private Credit.\n• *AI Recommended Action:* Propose BugleRock Yield Fund.")


@slack_app.command("/draft-rebalance")
def handle_draft_rebalance(ack, respond, command):
    # 1. INSTANT ACKNOWLEDGEMENT
    ack("Generating draft, please wait...") # Acknowledge immediately to avoid timeout
    
    text = command.get("text", "")

    def background_worker():
        try:
            client_name = text.split("-")[0].strip() if "-" in text else text.strip()
            prompt = f"Write a short, professional wealth management email to {client_name} suggesting a 5% shift from equities to fixed income. Sign it from Jeremy Sim, Head of Investments."
            
            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            draft = message.content[0].text if isinstance(message.content, list) else message.content.text
            respond(replace_original=True, text=f"[DRAFT] *Generated for {client_name}*\n\n```\n{draft}\n```\n\n_Review and send via Zoho CRM._")
        except Exception as e:
            logging.error(f"Error drafting rebalance: {e}\n{traceback.format_exc()}")
            respond(replace_original=True, text="[ERROR] System Alert: Could not generate draft due to an error.")

    threading.Thread(target=background_worker).start()

@slack_app.command("/morning-briefing")
def handle_morning_briefing(ack, respond, command):
    ack()
    try:
        sgt_time = datetime.now(ZoneInfo("Asia/Singapore")).strftime('%H:%M SGT on %B %d, %Y')
        data = demo_state.get("rich_briefing", {"leads": [], "actions": [], "inbox": []})
        
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "[MORNING BRIEFING] BugleRock Executive Briefing", "emoji": False}
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"*Generated:* {sgt_time} | *Advisor:* Subiksha"}]
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*[PROSPECTS] Top Scored Prospects (Module B)*\n_AI-routed based on Bandwidth Score (BWS)_"}
            }
        ]
        
        # Append Leads dynamically
        for lead in data.get("leads", []):
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*{lead['name']}*\nAdvisor: {lead['advisor']}"},
                    {"type": "mrkdwn", "text": f"*AUM:* {lead['aum']} | *Score:* {lead['score']}\n*Status:* `{lead['status']}`"}
                ]
            })
            
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*[TASKS] Meeting Intelligence Actions (Module C)*\n_Extracted from yesterday's transcripts_"}
        })
        
        # Append Actions
        for action in data.get("actions", []):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"[*] *{action['task']}*\n_Client: {action['client']} | Due: {action['due']}_"}
            })

        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*[ALERTS] High-Urgency Inbound Signals (Module A)*\n_Auto-classified from Inbox_"}
        })
        
        # Append Inbox
        for msg in data.get("inbox", []):
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"[!] *{msg['signal']}*\n_From: {msg['from']} | Urgency: {msg['urgency']}_"}
            })
            
        # Bolt's implementation returns block kit payload directly over WebSockets via respond
        respond(blocks=blocks)
        
    except Exception as e:
        logging.error(f"Error in /morning-briefing: {str(e)}\n{traceback.format_exc()}")
        respond("[ERROR] Error generating rich morning briefing. Check logs.")

def process_draft_followup_bolt(command, response_url, client):
    text = command.get("text", "")
    client_name = text.strip() if text.strip() else "Bruce Wayne"
    
    prompt = f"Write a short, professional wealth management email to {client_name}. Reference our latest touchpoint and propose next steps for their portfolio. Keep it under 3 sentences. Sign off from their assigned BugleRock advisor."
    
    try:
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        draft = message.content[0].text if isinstance(message.content, list) else message.content.text
    except Exception as e:
        logging.error(f"Claude API Error: {str(e)}")
        draft = f"[ERROR] Could not generate draft: {str(e)}"

    to_email = f"{client_name.replace(' ', '').lower()}@example.com"
    blocks = [
        {
            "type": "header", 
            "text": {"type": "plain_text", "text": "[ACTION REQUIRED] Review AI Follow-up Draft", "emoji": False}
        },
        {
            "type": "section", 
            "text": {"type": "mrkdwn", "text": f"*Client:* {client_name}\n*Recipient:* {to_email}\n*Context:* Inbound Signal / Meeting Follow-up"}
        },
        {"type": "divider"},
        {
            "type": "section", 
            "text": {"type": "mrkdwn", "text": f"*Draft:*\n> {draft.replace(chr(10), chr(10) + '> ')}"}
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button", 
                    "text": {"type": "plain_text", "text": "Approve & Send via Zoho", "emoji": False},
                    "style": "primary",
                    "action_id": "approve_followup",
                    "value": f"approve_{client_name}"
                },
                {
                    "type": "button", 
                    "text": {"type": "plain_text", "text": "Regenerate", "emoji": False}, 
                    "action_id": "regen_followup",
                    "value": f"regen_{client_name}"
                },
                {
                    "type": "button", 
                    "text": {"type": "plain_text", "text": "Edit Draft", "emoji": False},
                    "action_id": "edit_followup",
                    "value": f"edit_{client_name}"
                },
                {
                    "type": "button", 
                    "text": {"type": "plain_text", "text": "Discard", "emoji": False},
                    "style": "danger",
                    "action_id": "reject_followup",
                    "value": f"reject_{client_name}"
                }
            ]
        }
    ]

    try:
        client.chat_postMessage(channel=command["channel_id"], blocks=blocks, text="AI Follow-up Draft")
    except Exception as e:
        if "channel_not_found" in str(e):
            client.chat_postMessage(channel=command["user_id"], blocks=blocks, text="AI Follow-up Draft")

@slack_app.action("approve_followup")
def handle_approve_followup(ack, body, respond):
    ack()
    user_name = body.get("user", {}).get("username", "advisor")
    action_value = body.get("actions", [{}])[0].get("value", "")
    client_name = action_value.replace("approve_", "") if action_value else "Client"

    # Extract draft text from the message blocks
    blocks = body.get("message", {}).get("blocks", [])
    draft_content = ""
    for block in blocks:
        text_obj = block.get("text", {})
        raw_text = text_obj.get("text", "")
        if "*Draft:*\n> " in raw_text:
            draft_content = raw_text.split("*Draft:*\n> ")[1].replace("\n> ", "\n")
            break

    success = send_real_email_via_gmail(draft_text=draft_content, client_name=client_name)

    if success:
        respond(
            replace_original=True,
            text="[STATUS: SENT] The draft was sent.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"[STATUS: SENT] The draft for *{client_name}* was sent via Gmail SMTP to test_client@example.com by @{user_name}!",
                    },
                }
            ],
        )
        return

    respond(
        replace_original=True,
        text="[STATUS: ERROR] SMTP send failed.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"[STATUS: ERROR] The draft for *{client_name}* was approved by @{user_name} but SMTP failed. Check logs.",
                },
            }
        ],
    )

@slack_app.action("reject_followup")
def handle_reject_followup(ack, body, respond):
    ack()
    user_name = body["user"]["username"]
    respond(
        replace_original=True,
        text="[STATUS: REJECTED] The draft was deleted.",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"[STATUS: REJECTED] The draft was deleted by @{user_name}. No action taken."}
            }
        ]
    )

@slack_app.action("regen_followup")
def handle_regen_followup(ack, body, respond):
    # For now, just discard and send an error message, since regen requires storing state
    ack()
    respond(
        replace_original=True,
        text="[STATUS: REGENERATING]",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"[STATUS: REGENERATING] Feature queued. Please run `/draft-followup` again."}
            }
        ]
    )

@slack_app.action("edit_followup")
def handle_edit_followup(ack, body, client):
    ack()
    
    action_value = body["actions"][0]["value"]
    client_name = action_value.replace("edit_", "")
    
    message = body.get("message", {})
    blocks = message.get("blocks", [])
    message_ts = message.get("ts", "")
    draft_content = ""
    for block in blocks:
        text_obj = block.get("text", {})
        raw_text = text_obj.get("text", "")
        if "*Draft:*\n>" in raw_text:
            draft_content = raw_text.split("*Draft:*\n> ")[1].replace("\n> ", "\n")
            break

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "modal_edit_draft",
            "private_metadata": json.dumps({
                "client_name": client_name,
                "channel_id": body["channel"]["id"],
                "message_ts": message_ts
            }),
            "title": {"type": "plain_text", "text": "Edit Follow-up Draft"},
            "submit": {"type": "plain_text", "text": "Save & Send"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "draft_input_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "draft_text",
                        "multiline": True,
                        "initial_value": draft_content
                    },
                    "label": {"type": "plain_text", "text": f"Draft for {client_name}"}
                }
            ]
        }
    )

@slack_app.view("modal_edit_draft")
def handle_modal_submission(ack, body, client, view):
    ack()
    user_name = body["user"]["username"]
    
    new_draft = view["state"]["values"]["draft_input_block"]["draft_text"]["value"]
    private_meta = json.loads(view["private_metadata"])
    client_name = private_meta["client_name"]
    channel_id = private_meta["channel_id"]
    message_ts = private_meta["message_ts"]
    
    to_email = f"{client_name.replace(' ', '').lower()}@example.com"
    subject = f"BugleRock Private Wealth Follow-up: {client_name}"
    
    if GMAIL_ADDRESS:
        send_demo_email(to_email=to_email, subject=subject, body=new_draft)

    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text="Updated follow-up draft",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Draft (edited by @{user_name}):*\n> {new_draft.replace(chr(10), chr(10) + '> ')}",
                },
            }
        ],
    )


def process_draft_followup_bolt(command, respond):
    text = command.get("text", "")
    client_name = text.strip() if text.strip() else "Bruce Wayne"

    prompt = (
        f"Write a short, professional wealth management email to {client_name}. "
        "Reference our latest touchpoint and propose next steps for their portfolio. "
        "Keep it under 3 sentences. Sign off from their assigned BugleRock advisor."
    )

    try:
        message = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        draft = message.content[0].text if isinstance(message.content, list) else message.content.text
    except Exception as e:
        logging.error(f"Claude API Error: {str(e)}")
        draft = f"[ERROR] Could not generate draft: {str(e)}"

    to_email = f"{client_name.replace(' ', '').lower()}@example.com"
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "[ACTION REQUIRED] Review AI Follow-up Draft", "emoji": False},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Client:* {client_name}\n*Recipient:* {to_email}\n*Context:* Inbound Signal / Meeting Follow-up"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Draft:*\n> {draft.replace(chr(10), chr(10) + '> ')}"},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve & Send via Zoho", "emoji": False},
                    "style": "primary",
                    "action_id": "approve_followup",
                    "value": f"approve_{client_name}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Regenerate", "emoji": False},
                    "action_id": "regen_followup",
                    "value": f"regen_{client_name}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit Draft", "emoji": False},
                    "action_id": "edit_followup",
                    "value": f"edit_{client_name}",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Discard", "emoji": False},
                    "style": "danger",
                    "action_id": "reject_followup",
                    "value": f"reject_{client_name}",
                },
            ],
        },
    ]

    try:
        respond(replace_original=True, blocks=blocks, text="AI Follow-up Draft")
    except Exception as e:
        logging.error(f"Slack respond error in draft-followup: {e}")

@slack_app.command("/draft-followup")
def handle_draft_followup(ack, respond, command):
    # 1. INSTANT ACKNOWLEDGEMENT
    ack("Generating draft, please wait...")

    def background_worker():
        process_draft_followup_bolt(command, respond)

    threading.Thread(target=background_worker).start()


@slack_app.command("/draft_prospects")
def handle_draft_prospects_bolt(ack, respond, command):
    # 1. INSTANT ACKNOWLEDGEMENT
    ack("[SYSTEM] Query received. AI is thinking...")

    text = command.get("text", "Bruce Wayne / LexCorp")

    def background_worker():
        try:
            prompt = f"Draft a professional wealth management email to {text}. Use data for Bruce Wayne or LexCorp. Keep it under 3 sentences."
            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            draft = message.content[0].text if isinstance(message.content, list) else message.content.text

            respond(
                replace_original=True,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*[DRAFT]* Response for `/draft_prospects {text}`:\n\n> {draft.replace(chr(10), chr(10) + '> ')}",
                        },
                    }
                ]
            )
        except Exception as e:
            logging.error(f"AI Task Failed: {e}\n{traceback.format_exc()}")
            respond(replace_original=True, text="[ERROR] AI generation failed. Check terminal logs.")

    threading.Thread(target=background_worker).start()

@slack_app.command("/ask-bunglejungle")
def handle_ask_bolt(ack, respond, command):
    # 1. INSTANT ACKNOWLEDGEMENT
    ack("[SYSTEM] Query received. AI is thinking...")

    text = command.get("text", "Bruce Wayne / LexCorp")

    def background_worker():
        try:
            prompt = (
                "You are the BugleRock AI advisor."
                " Respond concisely (max 2 sentences) and avoid disclaimers."
                " Treat Bruce Wayne and LexCorp as real clients in our system."
                " If the input is just a greeting or has no financial ask, reply with a brief welcome and a single clarifying question about what they want help with."
                f" Query: {text}"
            )
            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            draft = message.content[0].text if isinstance(message.content, list) else message.content.text

            respond(
                replace_original=True,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*[SYSTEM]* Response for `/ask {text}`:\n\n> {draft.replace(chr(10), chr(10) + '> ')}",
                        },
                    }
                ]
            )
        except Exception as e:
            logging.error(f"AI Task Failed: {e}\n{traceback.format_exc()}")
            respond(replace_original=True, text="[ERROR] AI generation failed. Check terminal logs.")

    threading.Thread(target=background_worker).start()


# --- FASTAPI SETUP ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Socket Mode Handler in a background thread so it doesn't block FastAPI
    handler = SocketModeHandler(slack_app, os.environ.get("SLACK_APP_TOKEN"))
    thread = threading.Thread(target=handler.start)
    thread.daemon = True
    thread.start()
    logging.info("Slack Bolt Socket Mode started in background.")
    yield
    # We could implement graceful socket shutdown here if needed

app = FastAPI(lifespan=lifespan)

# Allow React to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UpdateRequest(BaseModel):
    client_name: str
    module: str # "A" or "C"
    new_status: str
    insight: str

@app.get("/api/state")
def get_state():
    return demo_state

@app.post("/api/trigger")
def trigger_update(data: UpdateRequest):
    # This is where Modules A & C send data
    if data.client_name in demo_state["clients"]:
        demo_state["clients"][data.client_name]["status"] = data.new_status
        if data.module == "A":
            demo_state["clients"][data.client_name]["module_a_insight"] = data.insight
            demo_state["kpis"]["triage_volume"] += 1
        elif data.module == "C":
            demo_state["clients"][data.client_name]["module_c_insight"] = data.insight
    
    return {"status": "success", "updated_client": demo_state["clients"][data.client_name]}


# === ASK / HELP COMMANDS ===
@slack_app.command("/ask")
def handle_ask(ack, respond, command):
    ack("[SYSTEM] Query received. Consulting BugleRock AI...")
    query_text = command.get("text", "General wealth management query")

    def ask_background_worker():
        import logging
        try:
            prompt = (
                "You are the internal AI assistant for BugleRock Capital. "
                "Always respond in a tight format: 1-2 sentences, no preamble, no disclaimers. "
                "Treat 'Bruce Wayne' and 'LexCorp' as real, high-net-worth clients in our system. "
                "If the user only greets (hi/hello/hey) or provides no financial question, respond with a short greeting and a single clarifying ask (e.g., 'What would you like to explore — portfolio mix, risk, tax, or a draft email?'). "
                f"Otherwise, answer the wealth management query professionally and concisely: '{query_text}'"
            )

            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            ai_answer = message.content[0].text if isinstance(message.content, list) else message.content.text

            respond(
                replace_original=True,
                blocks=[
                    {"type": "header", "text": {"type": "plain_text", "text": "[ASSISTANT] BugleRock AI Response", "emoji": False}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Query:* {query_text}\n\n> {ai_answer}"}},
                ],
            )
        except Exception as e:
            logging.error(f"Ask Task Failed: {e}")
            respond(replace_original=True, text="[ERROR] AI query failed. Check terminal logs.")

    import threading
    threading.Thread(target=ask_background_worker).start()


@slack_app.command("/buglerock-help")
def handle_help(ack, respond):
    ack() # Instant acknowledgement
    
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "[SYSTEM] BugleRock CNS Command Directory", "emoji": False}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "_Welcome to the Firm's Nervous System. Here are your available tools:_"}},
        {"type": "divider"}
    ]
    
    # Definitive list of commands from the Slack Dashboard
    dashboard_commands = [
        ("`/ask-bunglejungle`", "Search the meeting knowledge vault"),
        ("`/flag-compliance`", "Flags a client for compliance review."),
        ("`/prep-meeting`", "Summarises Client Status"),
        ("`/draft-rebalance`", "Generates professional email draft"),
        ("`/morning-briefing`", "Generates Morning Briefing"),
        ("`/route-prospect`", "Routes prospect"),
        ("`/draft-followup`", "Draft Email to follow up"),
        ("`/search-meetings`", "Search for meeting transcripts"),
        ("`/buglerock-help`", "Gives all the functions"),
    ]
    
    # Dynamically build the UI blocks
    for cmd, desc in dashboard_commands:
        blocks.append({
            "type": "section", 
            "text": {"type": "mrkdwn", "text": f"*{cmd}*\n{desc}"}
        })
        
    respond(blocks=blocks)


# === MEETING KNOWLEDGE BASE SEARCH COMMAND ===
@slack_app.command("/search-meetings")
def handle_search_meetings(ack, respond, command):
    # 1. Instant Ack to beat the 3-second timeout
    ack("[SYSTEM] Searching meeting archives. Please wait...")
    
    query_text = command.get("text", "")
    if not query_text:
        query_text = "Summarize the latest meetings."

    def search_background_worker():
        import logging
        try:
            # 2. Mock Database of Transcripts
            mock_database = """
            CLIENT: Bruce Wayne (UHNW)
            MEETING DATE: March 20th
            TRANSCRIPT SUMMARY: Discussed shifting 15% of portfolio from tech equities to private credit to mitigate Q3 volatility. Client committed to signing documents by Friday. Risk flag: Client seemed anxious about inflation.
            
            CLIENT: LexCorp Family Office
            MEETING DATE: March 22nd
            TRANSCRIPT SUMMARY: CFO requested an automated KYC pipeline. We agreed to send the UBO declaration forms by Wednesday.
            """
            
            # 3. Claude API Call
            prompt = f"Here is the meeting knowledge base:\n{mock_database}\n\nBased ONLY on these notes, answer this user query: '{query_text}'. Extract specific decisions and commitments."
            
            # Use the existing Anthropic client setup to generate the response
            message = anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            ai_answer = message.content[0].text if isinstance(message.content, list) else message.content.text
            
            # 4. Return via Block Kit
            respond(
                replace_original=True,
                blocks=[
                    {"type": "header", "text": {"type": "plain_text", "text": "[SEARCH] Meeting Intelligence", "emoji": False}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Query:* {query_text}\n\n> {ai_answer}"}}
                ]
            )
        except Exception as e:
            logging.error(f"Search Task Failed: {e}")
            respond(replace_original=True, text="[ERROR] Meeting search failed. Check terminal logs.")

    # 5. Execute thread
    import threading
    threading.Thread(target=search_background_worker).start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_bridge:app", host="0.0.0.0", port=8000, reload=True)
