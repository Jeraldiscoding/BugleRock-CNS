# TASK: Fix Slack 3-Second Timeout on Slash Commands

## 1. Context & Objectives
The `/ask-bunglejungle` and `/draft` commands are failing intermittently with Slack's "did not respond" error. This occurs because synchronous Claude API calls are blocking the `ack()` function, causing Slack's 3-second timeout to trip.

## 2. Strict Workflow Rules
1. **Instant Ack:** The `ack()` function MUST be the very first line executed in the command handler.
2. **Threading:** All Claude API calls MUST be pushed into a `threading.Thread` so the main function can return immediately.
3. **Delayed Response:** Use the `respond()` function (provided by Bolt) inside the thread to send the final AI draft.

## 3. Implementation Details

### Update the Command Handlers (`api_bridge.py`)
Rewrite the command handlers to strictly follow this threaded pattern:

```python
import threading
import logging

@slack_app.command("/ask-bunglejungle")
def handle_ask_bunglejungle(ack, respond, command):
    # 1. INSTANT ACKNOWLEDGEMENT (Stops the Slack timeout)
    ack("[SYSTEM] Query received. AI is thinking...")

    # 2. Extract the text
    text = command.get("text", "Bruce Wayne")

    # 3. Define the background worker
    def background_worker():
        try:
            # Call Claude API here
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": f"Answer this professionally: {text}"}]
            )
            ai_content = message.content.text
            
            # Send the final result back to Slack
            respond(
                replace_original=True,
                blocks=[
                    {"type": "header", "text": {"type": "plain_text", "text": "[DRAFT] AI Response", "emoji": False}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"> {ai_content}"}}
                ]
            )
        except Exception as e:
            logging.error(f"AI Task Failed: {e}")
            respond(replace_original=True, text="[ERROR] AI generation failed. Check terminal logs.")

    # 4. Start the thread and exit the main function immediately!
    threading.Thread(target=background_worker).start()