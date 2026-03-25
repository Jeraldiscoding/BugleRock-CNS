# 🧠 BugleRock Smart Inbox (Module A) - Agent Master Specification

## 🎯 Role & Objective
[cite_start]You are an expert backend engineer building "Module A: Smart Inbox" for the BugleRock Rockathon[cite: 1, 19]. 
[cite_start]Your objective is to build an email & meeting intelligence capture engine[cite: 20]. [cite_start]This system must capture incoming signals, classify them using an LLM, update a CRM, and publish an event to a central router[cite: 4, 24, 25, 68].

## 🛠️ Tech Stack & Constraints
* [cite_start]**APIs:** Gmail API, Fireflies.ai API, Claude API, Zoho CRM API[cite: 26].
* [cite_start]**Databases:** SQLite (for deduplication cache and event bus)[cite: 27, 68].
* **Timezone:** STRICTLY SGT (UTC+8). [cite_start]Do not mix time zones under any circumstances[cite: 96, 97].
* **Zoho Rate Limit:** 100 API calls/min on the free tier. [cite_start]You MUST batch writes and cache reads[cite: 94, 95].
* [cite_start]**Token Limit:** Meeting transcripts can be 5000+ words; you MUST chunk before sending to Claude (max 4000 tokens per chunk)[cite: 95].

---

## 🏗️ Step-by-Step Implementation Guide

### Phase 1: Ingestion & Gateway
Build endpoints/listeners to capture incoming data.
1.  **Fireflies Webhook:** Create a `POST /api/fireflies-webhook` endpoint to accept transcript data. 
    * [cite_start]*Data to extract:* Attendees, topics, action items, full transcript[cite: 23].
2.  [cite_start]**Gmail Integration (Pub/Sub vs. Polling):** * *Primary attempt:* Implement Gmail API via Google Cloud Pub/Sub[cite: 22]. Catch payloads at `POST /api/gmail-webhook`.
    * [cite_start]*Fallback Logic:* If GCP setup fails or takes too long, implement a `while` loop that polls via IMAP every 2 minutes[cite: 22, 94].
    * [cite_start]*Data to extract:* Sender, subject, body, attachments[cite: 22].

### Phase 2: AI Processing (Claude API)
[cite_start]Send the captured text to Claude for structured extraction[cite: 24].
1.  **Prompt Engineering:** Force Claude to return strict JSON.
2.  **Classification Fields Required:**
    * [cite_start]`type`: Must be one of [client email, prospect inquiry, internal, marketing, vendor][cite: 24].
    * [cite_start]`urgency`: Must be one of [high, medium, low][cite: 24].
    * [cite_start]`entities`: Extract company name, person, deal reference, action items[cite: 24].
    * `sentiment`: Extract sentiment (Positive, Neutral, Frustrated) *[Custom Feature]*.
3.  [cite_start]**Chunking Logic:** If `transcript.length > 4000_tokens`, split the text into sequential chunks and process them iteratively[cite: 95].

### Phase 3: Deduplication Cache & Zoho CRM
Do NOT write to Zoho without checking the cache first.
1.  [cite_start]**SQLite Dedup Cache:** Create a table with a composite key of `email_address + company_name`[cite: 100]. 
    * *Edge Case Handling:* If the sender uses a personal email (e.g., @gmail.com), rely on the `company_name` extracted by Claude from the email body/signature to verify identity.
2.  [cite_start]**Zoho Operations:** * Auto-create or update records for Contacts, Deals, Notes, Tasks[cite: 25].
    * [cite_start]Map extracted meeting action items specifically to Zoho CRM Tasks[cite: 32].

### Phase 4: Event Publishing
1.  [cite_start]**The Event Bus:** Connect to the shared SQLite event table[cite: 71].
2.  [cite_start]**Publish:** Once Zoho is updated, publish an event with the payload: `{"event": "new_signal_classified", "data": {...}}`[cite: 68].

---

## 🚨 Error Handling & Logic Checks (The "If/Then" Matrix)

**Ingestion Errors:**
* *IF* the Fireflies payload is missing the `transcript` field -> *THEN* log a warning, return a 400 status, and abort processing.
* *IF* GCP Pub/Sub authentication throws an error -> *THEN* immediately fallback to the IMAP polling function running every 2 minutes.

**Claude API Errors:**
* *IF* Claude returns a 429 (Rate Limit) -> *THEN* implement an exponential backoff retry (wait 2s, 4s, 8s).
* *IF* Claude outputs invalid JSON -> *THEN* catch the parsing error and send a follow-up prompt to Claude: "Your previous response was not valid JSON. Return ONLY valid JSON."
* *IF* the text exceeds token limits despite chunking -> *THEN* truncate the oldest parts of the transcript and prioritize the final 30 minutes of the meeting.

**Zoho CRM & Database Errors:**
* [cite_start]*IF* the SQLite dedup check finds a matching `email + company` -> *THEN* pull the `zoho_contact_id` from SQLite and execute a Zoho UPDATE request[cite: 25].
* [cite_start]*IF* the SQLite dedup check finds NO match -> *THEN* execute a Zoho CREATE request and save the new ID to SQLite[cite: 25].
* [cite_start]*IF* the Zoho API approaches 100 calls/min -> *THEN* push the remaining payloads to an in-memory queue, wait 60 seconds, and execute them as a batch[cite: 95].

**Logic Checks Before Final Publish:**
* *CHECK:* Are all timestamps attached to the data strictly in SGT (UTC+8)? [cite_start]If no, convert them before saving[cite: 96].
* *CHECK:* Was an action item extracted? [cite_start]If yes, verify a Zoho Task was mapped and created[cite: 32].