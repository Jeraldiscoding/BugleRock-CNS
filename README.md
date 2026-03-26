# BugleRock Client Nervous System

AI-powered wealth management command center: Slack-first workflows, institutional-grade formatting (zero emojis), automated routing, meeting intelligence, and one-click Gmail dispatch.

---

## Architecture Overview
- **Frontend:** React (Vite) + Tailwind (`frontend-app/`).
- **Backend:** Python 3 + FastAPI + Slack Bolt (Socket Mode) in `api_bridge.py`.
- **AI:** Anthropic Claude 3 Haiku (`claude-haiku-4-5-20251001`).
- **Messaging & Actions:** Slack slash commands + Block Kit.
- **Email Dispatch:** Gmail SMTP (App Password) triggered from Slack buttons.
- **Data/Mock Entities:** LexCorp, Bruce Wayne, Stark Industries, Subiksha, Jeremy Sim, etc., stored in in-memory dictionaries inside `api_bridge.py`.
- **Modules:** Module A (drafts & email execution), Module B (lead routing & bandwidth scoring), Module C (meeting intelligence search). React dashboard mirrors Module B scoring/insights.

---

## Prerequisites
- **Python** 3.10+
- **Node.js** 18+ (for Vite frontend)
- **npm** (or yarn/pnpm; commands assume npm)
- **Slack Workspace** with a Socket Mode app (slash commands enabled)
- **Gmail** account with an **App Password** (not the main password)
- **Anthropic API key**
- **Ngrok** (optional; only if you want to expose FastAPI HTTP endpoints—Socket Mode itself doesn’t need it)

---

## Environment Variables (.env)
Create a `.env` at the repo root. Template:

```bash
# AI
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: transcription (Module C integrations)
FIREFLIES_API_KEY=your_fireflies_key

# Gmail
GMAIL_ADDRESS=your_gmail_address@example.com
GMAIL_APP_PASSWORD=your_gmail_app_password   # App Password, not main password
GMAIL_CREDENTIALS_PATH=./credentials.json    # if used elsewhere

# Slack (Socket Mode)
SLACK_APP_TOKEN=xapp-...
SLACK_BOT_TOKEN=xoxb-...

# Zoho (Module B auth/tests)
ZOHO_CLIENT_ID=...
ZOHO_CLIENT_SECRET=...
ZOHO_REFRESH_TOKEN=...
```

Security: `.env` is gitignored. Rotate any secrets that were ever hardcoded or shared.

---

## Setup & Run (three terminals)

### Terminal 1 — Backend (FastAPI + Slack Socket Mode)
```bash
cd /path/to/BugleRock-CNS
pip install -r requirements.txt
python api_bridge.py
```
- Starts FastAPI and Slack Bolt Socket Mode.
- Serves `/api/state` and `/api/trigger` for dashboard/ingest.

### Terminal 2 — Frontend (React Dashboard)
```bash
cd /path/to/BugleRock-CNS/frontend-app
npm install
npm run dev
```
- Vite dev server (default http://localhost:5173).
- Shows prospect scoring, BWS, and briefings for mock entities (LexCorp, Stark, etc.).

---

## Feature Guide / Slack Commands
All commands ack within 3 seconds and return Block Kit responses (no emojis, enterprise tone):

- `/buglerock-help` — Lists all available commands.
- `/route-prospect [Name - AUM]` — Module B routing: computes Bandwidth Score (BWS) and recommends advisor; Approve/Re-route buttons.
- `/flag-compliance [Client]` — Flags a client, updates status, increments risk flags.
- `/prep-meeting [Client]` — Quick status snapshot for an upcoming meeting.
- `/draft-rebalance [Client]` — Generates a short rebalance email draft.
- `/morning-briefing` — Executive briefing block with prospects/actions/inbox.
- `/draft-followup [Client]` — Follow-up draft generation (Module A).
- `/draft_prospects [Prospect]` — Prospect-focused draft using mock data.
- `/ask-bunglejungle [query]` — Meeting-knowledge AI Q&A (Module C tone).
- `/ask [query or greeting]` — General AI assistant; concise 1–2 sentence replies; greeting path asks one clarifying question.
- `/search-meetings [query]` — Meeting knowledge base search/summarize (Module C).

---

## Data Flow (high level)
- Frontend pulls from FastAPI (`/api/state`) for dashboard cards; data mirrors in-memory `demo_state` in `api_bridge.py`.
- Slack commands run via Bolt Socket Mode; longer tasks run in background threads and edit the original message.
- AI calls go to Anthropic Haiku for drafts, meeting search, and `/ask` responses.
- Email dispatch uses Gmail SMTP with env vars; if missing, send is aborted with a log.
- Mock entities (LexCorp, Bruce Wayne, Stark) and advisors (Subiksha, Jeremy Sim, Dheeraj Bharwani) provide deterministic demo output.

---

## Verification Notes
- Syntax: `python -m py_compile api_bridge.py` passes.
- Logic highlights:
  - Commands ack immediately to beat the Slack 3s window; heavy work in threads.
  - `/route-prospect` BWS = (active_clients*1 + pending_prospects*0.5 + meetings*0.2) / capacity.
  - `/ask` and `/ask-bunglejungle` enforce 1–2 sentence responses; greetings yield one clarifying question.
  - `/search-meetings` and drafting commands use model `claude-haiku-4-5-20251001`.
  - Email send now relies solely on env creds (hardcoded creds removed); missing creds log an error and skip send.

---

## Suggested Demo Flow (≈7 minutes)
1) Dashboard: show LexCorp score + BWS.
2) Slack `/buglerock-help` to reveal command directory.
3) `/route-prospect LexCorp Family Office - 120` and approve.
4) `/search-meetings Bruce Wayne last call summary`.
5) `/draft Bruce Wayne` (or `/draft-followup`) then click send.
6) Show Gmail Sent folder with the dispatched email.
7) Close: emphasize zero-emoji, enterprise-grade loop: route → context → draft → send.

---

## Troubleshooting
- No Slack response: verify `SLACK_APP_TOKEN` and `SLACK_BOT_TOKEN`, and ensure the app is installed in the channel.
- Email not sending: confirm `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` (App Password), and that SMTP access is allowed.
- AI failures: check `ANTHROPIC_API_KEY` and network egress.
- Frontend 404: ensure `npm run dev` is running in `frontend-app/`.
- If secrets were ever committed, rotate them immediately.
