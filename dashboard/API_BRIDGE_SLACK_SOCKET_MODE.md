# API Bridge: Webhooks to Socket Mode Migration

## Overview
The `api_bridge.py` script has been successfully refactored from a standard FastAPI HTTP Webhook (`@app.post("/slack/command")`) to an asynchronous **Slack Bolt Socket Mode** implementation.

This modification was necessary because Slack resides on the public internet and cannot natively route event payloads to local development servers (`http://localhost:8005`) without utilizing third-party tunneling solutions (like `ngrok` or `localtunnel`).

## Architectural Changes
1. **Removed:** The FastAPI `@app.post("/slack/command")` HTTP endpoint.
2. **Added:** `slack_bolt.App` and `slack_bolt.adapter.socket_mode.SocketModeHandler`.
3. **Execution Logic:** The Socket Mode handler leverages FastAPI's `@asynccontextmanager` Lifespan events. It spawns the socket listener continuously on a background `threading.Thread` as a Daemon, allowing the FastAPI webserver to spin up asynchronously on the main thread for the Frontend React Dashboard to poll.
4. **Command Methods:**
   - Instead of routing by `command` literal matching string checks, Bolt handles the routing using decorators:
     - `@slack_app.command("/flag-compliance")`
     - `@slack_app.command("/prep-meeting")`
     - `@slack_app.command("/draft-rebalance")`
     - `@slack_app.command("/morning-briefing")`

## Instructions for Use
1. Do **not** use `ngrok`.
2. Do **not** enter a Request URL into the Slack API App Dashboard.
3. Ensure Socket Mode is toggled to **ON** in the Slack App Settings.
4. Ensure `SLACK_BOT_TOKEN` (`xoxb-...`) and `SLACK_APP_TOKEN` (`xapp-...`) are verified in the root `.env` file.
5. Boot system normally: `uvicorn api_bridge:app --reload --port 8005`.

Socket mode will auto-negotiate, keeping the WebSockets connection alive underneath the hood.
