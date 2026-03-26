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

# Initialize Logging
logging.basicConfig(
    filename='api_error.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# --- SLACK BOLT SETUP ---
slack_app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# In-memory "Database" for the demo API (Shared state)
demo_state = {
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

# === SLACK SOCKET MODE COMMAND HANDLERS ===

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
    ack("Generating draft, please wait...") # Acknowledge immediately to avoid timeout
    try:
        text = command.get("text", "")
        client_name = text.split("-")[0].strip() if "-" in text else text.strip()
        prompt = f"Write a short, professional wealth management email to {client_name} suggesting a 5% shift from equities to fixed income. Sign it from Jeremy Sim, Head of Investments."
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        draft = message.content[0].text if isinstance(message.content, list) else message.content.text
        respond(f"[DRAFT] *Generated for {client_name}*\n\n```\n{draft}\n```\n\n_Review and send via Zoho CRM._")
    except Exception as e:
        logging.error(f"Error drafting rebalance: {e}\n{traceback.format_exc()}")
        respond("[ERROR] System Alert: Could not generate draft due to an error.")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
