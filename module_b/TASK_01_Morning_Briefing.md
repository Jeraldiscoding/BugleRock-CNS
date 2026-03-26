# TASK: UPGRADE "Morning Briefing" to Institutional Block Kit (Feature 3)

## 1. Context & Objectives
The current `/morning-briefing` outputs a basic markdown string. The competitor team has a highly detailed text list. We must beat them by deploying a **Slack Block Kit** UI that is visually stunning, deeply detailed, and explicitly categorizes data across Module A (Inbox), Module B (Lead Router), and Module C (Meeting Intel).

## 2. Strict Workflow Rules
1. **State Overhaul:** Replace the old `aggregated_briefing` in `demo_state` with a deeply nested dictionary containing specific leads, meeting actions, and inbox signals.
2. **Block Kit Construction:** Rewrite the `/morning-briefing` logic to construct a `blocks` array instead of a `text` string.
3. **Timezone Enforcement:** Maintain the SGT (UTC+8) timestamp generation using `zoneinfo`.
4. **Error Handling:** Keep the `try/except` logging to `api_error.log`.

## 3. Implementation Details

### A. The Deep Mock Data (`demo_state` update)
Replace the old briefing mock data in `api_bridge.py` with this highly detailed set, utilizing BugleRock personnel:
```python
demo_state["rich_briefing"] = {
    "leads": [
        {"name": "Amanda Wu - Wu Family Trust", "aum": "$250M", "score": "98/100", "status": "Qualified", "advisor": "William"},
        {"name": "David Chen - Chen Holdings", "aum": "$120M", "score": "95/100", "status": "Assigned", "advisor": "Parvathy Srikant"},
        {"name": "Stark Family Trust", "aum": "$40M", "score": "87/100", "status": "Pending CEO Approval", "advisor": "Jeremy Sim"}
    ],
    "actions": [
        {"task": "Draft Singapore trust structure proposal", "client": "Wu Family Trust", "due": "Today, 14:00 SGT"},
        {"task": "Execute Q3 Portfolio Rebalancing", "client": "Bruce Wayne", "due": "Tomorrow, 10:00 SGT"}
    ],
    "inbox": [
        {"signal": "Missing UBO Declaration Form", "from": "Apex Corp CFO", "urgency": "High - Compliance Flagged"},
        {"signal": "Inquiry on Private Credit Yields", "from": "Robert Lim", "urgency": "Medium"}
    ]
}