# Task 03 Error Log

## Issues Found
1. **Draft-Followup Claude Error**
   - **User reported:** `/draft-followup` returns an error stating it couldn't load when trying to draft for Bruce Wayne.
   - **Root Cause:** In `api_bridge.py`, the code uses `claude-3-haiku-20240307`, which is returning a `404 Not Found`. This is because we should be using `claude-haiku-4-5-20251001` or another accessible model for the current key.
   - **Fix:** Update the `model` parameter to `claude-haiku-4-5-20251001` inside `handle_draft_followup`.

2. **Triangle Warning on Regenerate Button Click**
   - **User reported:** Clicking "Regenerate" gives a triangle (⚠️) in Slack.
   - **Root Cause:** We implemented the Slack Interactivity handling in a FastAPI `@app.post("/slack/interactivity")` endpoint while utilizing Bolt's Socket Mode simultaneously. Bolt Socket Mode swallows all interactivity requests, essentially meaning the HTTP endpoint never acks it back properly (or there's a clash), resulting in an unacknowledged action warning.
   - **Fix:** Migrate the interactivity logic natively into `@slack_app.action` handlers (e.g., `@slack_app.action("approve_followup")`, `"regen_followup"`, `"reject_followup"`) so Bolt properly `.ack()`s the request and patches the blocks nicely.

3. **Missing "Edit" Button functionality**
   - **User reported:** Needs an edit button to manually adjust the text before sending.
   - **Root Cause:** A raw static draft block was implemented, without native Slack View/Modal integration or an "Edit" button.
   - **Fix:** Add an `action_id: "edit_followup"`. When clicked, it opens a Slack modal using `client.views_open()`. We can then handle the `view_submission` to save and update the draft.

4. **Sender/Recipient Email Identity Issue**
   - **User reported:** Sending a reply to their own email, but we should make it look like an outbound message (sent *from* their email, *to* the client). 
   - **Root Cause:** The `send_demo_email` function was literally wiring `GMAIL_ADDRESS` as BOTH `To` and `From`.
   - **Fix:** Change the `to_email` parameter to actually mock the client's email (e.g., `client_name.replace(" ", "").lower() + "@example.com"`) and add the explicit sender as the `GMAIL_ADDRESS`. We will also send the email literally to the client, but for demo safety, maybe cc the user or just send to a dummy or keep `to_email` as user but update `To` header visually? "so when i send i should not receive an email but instead have sent an email" -> This likely means the user doesn't want their own inbox pinging with incoming mail; they just want it to go into their "Sent Items" folder. If they send to an external email via SMTP, Gmail naturally puts it into Sent items anyway.
