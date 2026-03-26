# TASK 03: Implement Decay Detection & Auto-Chaser (Feature 2)

## 1. Context & Objectives
Module B must track prospect engagement. It must auto-generate a re-engagement email draft when a prospect reaches the 5-day decay threshold.

## 2. Strict Workflow Rules
1. **Simulation:** Since we cannot wait 5 days in a demo, we will use a `/time-travel-5-days` Slack command to trigger the 5-day decay logic instantly.
2. **AI Integration:** You must use the Anthropic API (`claude-3-haiku-20240307`) to generate the draft.
3. **Error Handling:** Log any Anthropic API timeouts or errors to `api_error.log`.

## 3. Detailed Implementation Steps

### A. Endpoint Logic (`/time-travel-5-days`)
Add this condition to the `/slack/command` handler:
1. Extract the `client_name` from the `text` parameter (e.g., if text is "Bruce Wayne", client is "Bruce Wayne").
2. Update `demo_state["clients"][client_name]["status"]` to `"Decayed - 5 Days"`.

### B. Claude AI Prompting
Implement the Claude API call:
```python
prompt = f"Write a short, professional wealth management email to {client_name} who we have not spoken to in 5 days. Mention that we are ready to proceed with their portfolio strategy. Keep it under 3 sentences."
        
message = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=200,
    messages=[{"role": "user", "content": prompt}]
)
draft = message.content.text