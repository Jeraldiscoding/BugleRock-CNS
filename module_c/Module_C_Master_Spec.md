# 🧠 BugleRock Meeting Intelligence (Module C) - Agent Master Specification

## 🎯 Role & Objective
You are an expert backend AI engineer building "Module C: Meeting Intelligence" for the BugleRock Rockathon. 
[cite_start]Your objective is to analyze meeting transcripts, auto-generate follow-up drafts, build a searchable Vector Knowledge Base (RAG), and push updates to the CRM and Event Bus[cite: 69, 72, 73, 85].

## 🛠️ Tech Stack & Constraints
* **APIs:** Fireflies.ai API, Claude API (use `claude-haiku-4-5-20251001` or standard Sonnet depending on key access), Zoho CRM API, Slack Bolt SDK (Python).
* [cite_start]**Databases:** ChromaDB (local Vector DB for RAG) and SQLite (for the Event Bus)[cite: 75, 76, 88].
* [cite_start]**Timezone:** STRICTLY SGT (UTC+8)[cite: 113].
* **Constraints:** Must use Structured JSON Outputs (Pydantic) for Claude extraction.

---

## 🏗️ Step-by-Step Implementation Guide

### Phase 1: Deep Analysis & Follow-Up Generation
Take the Fireflies transcript (passed from Module A or queried directly) and process it.
1.  **Pydantic Schema (`MeetingInsights`):** Define a schema for Claude to extract:
    * [cite_start]`decisions_made`: List of strings[cite: 71].
    * [cite_start]`commitments_given`: List of strings[cite: 71].
    * [cite_start]`risk_flags`: List of strings (e.g., churn risk, compliance issues)[cite: 71].
    * [cite_start]`sentiment_shift`: String description[cite: 71].
    * [cite_start]`follow_up_email_draft`: A fully written, professional email draft[cite: 72, 79].
2.  [cite_start]**Chunking:** If the transcript is >4000 tokens, process it in chunks and map-reduce the insights[cite: 112].

### Phase 2: The Vector Knowledge Base (RAG)
Build the searchable memory bank.
1.  **ChromaDB Setup:** Initialize a local ChromaDB collection named `meeting_transcripts`.
2.  **Embedding:** Break the meeting transcript into smaller semantic chunks (e.g., 500 words each). Add metadata to each chunk: `client_name`, `meeting_date`, `zoho_contact_id`.
3.  **Storage:** Embed these chunks and store them in ChromaDB.

### Phase 3: The Slack Bot Interface 
Create the user interface for the advisors using the Slack Bolt SDK.
1.  **Slash Command (`/ask-buglerock`):** Register a command listener. When an advisor types `/ask-buglerock What did we discuss with Wayne Enterprises?`, the bot must:
    * [cite_start]Query ChromaDB for the top 3 most relevant transcript chunks[cite: 72].
    * Pass those chunks to Claude with the prompt: "Answer the user's question using ONLY this context."
    * [cite_start]Reply privately to the advisor in Slack[cite: 80].
2.  **Interactive Follow-up Prompt:** Once Phase 1 finishes drafting the email, push a Slack Block Kit message to the advisor containing the `follow_up_email_draft` and an interactive button to "Approve & Send".

### Phase 4: CRM Sync & Event Publishing
1.  [cite_start]**Zoho CRM Updates:** Take the `decisions_made` and `commitments_given` and automatically log them as Notes and Tasks under the respective Contact/Deal in Zoho[cite: 73, 81].
2.  **Universal Router Publish:** Connect to `universal_router.db`. Insert a new row with `event_type = "meeting_analysed"` and the payload containing the risk flags and basic metadata. This will trigger the firm-wide React dashboard.

---

## 🚨 Error Handling & Logic Checks

* [cite_start]*IF* ChromaDB fails to initialize -> *THEN* fallback to standard SQLite Full-Text Search (FTS)[cite: 75, 76].
* *IF* Claude fails to generate a follow-up draft due to prompt blocking -> *THEN* return a standardized fallback template with placeholders.
* *IF* Slack Bolt receives a command but the RAG query returns 0 results -> *THEN* reply in Slack: "I couldn't find any meeting records discussing that topic."