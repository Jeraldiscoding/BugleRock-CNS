from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Allow React to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For hackathon only!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory "Database" for the demo
demo_state = {
    "kpis": {
        "total_aum": "$1.2B",
        "triage_volume": 842,
        "risk_flags": 3
    },
    "clients": {
        "Bruce Wayne": {
            "department": "Client & UHNW",
            "status": "AI Triage",
            "module_a_insight": "Waiting for email...",
            "module_c_insight": "Waiting for transcript..."
        }
    }
}

class UpdateRequest(BaseModel):
    client_name: str
    module: str # "A" or "C"
    new_status: str
    insight: str

# --- NEW: SLACK SLASH COMMAND ENDPOINT ---
@app.post("/slack/command")
async def handle_slack_command(
    command: str = Form(...),
    text: str = Form(...)
):
    # Extract the client name (e.g., text="Apex Corp - missing docs" -> "Apex Corp")
    client_name = text.split("-")[0].strip() if "-" in text else text.strip()

    # COMMAND 1: THE DASHBOARD MANIPULATOR
    if command == "/flag-compliance":
        # 1. Update the React Dashboard state!
        if client_name in demo_state["clients"]:
            demo_state["clients"][client_name]["status"] = "Compliance Hold"
            # we'll append to module_a_insight for visibility
            demo_state["clients"][client_name]["module_a_insight"] = f"Flagged via Slack: {text}"
            demo_state["kpis"]["risk_flags"] += 1

        # 2. Reply to Slack
        return {
            "response_type": "in_channel",
            "text": f"🚨 *{client_name}* has been locked. Escalated to Stefan Ho (Risk & Compliance)."
        }

    # COMMAND 2: THE SYNTHESIZER
    elif command == "/prep-meeting":
        # Hardcoded for the video demo speed!
        return {
            "response_type": "in_channel",
            "text": f"📝 *Meeting Prep: {client_name}*\n• *Last Touchpoint:* Emailed yesterday expressing anxiety over tech stock volatility.\n• *Past Context:* Discussed shifting 15% to Private Credit.\n• *AI Recommended Action:* Propose BugleRock Yield Fund."
        }

    # COMMAND 3: THE HEAVY LIFTER (CLAUDE AI)
    elif command == "/draft-rebalance":
        # Use Claude Haiku because Slack times out if it takes longer than 3 seconds!
        prompt = f"Write a short, professional wealth management email to {client_name} suggesting a 5% shift from equities to fixed income. Sign it from Jeremy Sim, Head of Investments."
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        draft = message.content[0].text if isinstance(message.content, list) else message.content.text

        return {
            "response_type": "in_channel",
            "text": f"✉️ *Draft Generated for {client_name}*\n\n```\n{draft}\n```\n\n_Review and send via Zoho CRM._"
        }

    return {"text": "Unknown command."}

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