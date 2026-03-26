# TASK: Implement Meeting Knowledge Base Search (Feature 4)

## 1. Context & Objectives
Implement Module C's searchable meeting knowledge base, allowing advisors to query transcripts via natural language. 
We are building a `/search-meetings` Slack command using a mock RAG (Retrieval-Augmented Generation) approach.

## 2. Strict Workflow Rules
1. **Safety First:** DO NOT modify, reformat, or delete the existing `/draft` command, the `smtplib` email dispatcher, or the interactivity handlers. 
2. **Timeout Prevention:** You MUST use the exact same `ack()` and `threading.Thread` pattern used in the `/draft` command to avoid Slack's 3-second timeout.
3. **Standardized Data:** Inject the hardcoded mock transcript database exactly as provided.
4. **Emoji Standard:** ZERO emojis in the output. Use `[SYSTEM]` and `[SEARCH]` bracket tags.

## 3. Implementation Details

Add this exact command listener to the bottom of `api_bridge.py`:

```python
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
            message = client.messages.create(
                model="claude-3-haiku-20240307", # Use standard model
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            ai_answer = message.content.text
            
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