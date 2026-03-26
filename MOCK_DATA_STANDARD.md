# Standardized Mock Data Set (BugleRock CNS)

To ensure consistency across the Universal Router (api_bridge.py), React Dashboard, and all Slack Webhooks, we have standardized the mock test sets for client entities. 

Whenever you test Slash Commands (e.g. `/prep-meeting`, `/flag-compliance`) or trigger webhooks, use these standard entities:

## 1. Bruce Wayne (Individual / UHNW)
- **Department:** Client & UHNW
- **Advisor:** Subiksha
- **Context:** High net worth individual ($25.4M). Concerned about tech stock volatility. 
- **Module A (Email):** Emailed urgently regarding Q3 Rebalancing.
- **Module C (Meeting):** Discussed shifting 15% to Private Credit.
- **Used for Testing:** `/draft-rebalance Bruce Wayne`, `/prep-meeting Bruce Wayne`

## 2. LexCorp Family Office (Institutional / Prospect)
- **Department:** Corporate Dev
- **Advisor:** Dheeraj Bharwani
- **Context:** Large pipeline prospect ($120M AUM target).
- **Module B (Scoring):** Bandwidth Score (BWS) of 94%. Ready to Pitch.
- **Used for Testing:** `/morning-briefing` (appears in Top Scored Prospects)

## 3. Stark Industries Trust (Institutional / Active)
- **Department:** Investments
- **Advisor:** Jeremy Sim
- **Context:** Active massive trust ($450M).
- **Module B (Scoring):** Score 88%, Warm status.
- **Used for Testing:** `/morning-briefing` (Pipeline visibility), `/draft-rebalance Stark Industries Trust`

## 4. Apex Corp (Corporate)
- **Department:** Ops & Compliance
- **Advisor:** Stefan Ho (Risk)
- **Context:** Compliance risks detected, missing documentation.
- **Module A/C:** Needs Q3 Performance Audit sent.
- **Used for Testing:** `/flag-compliance Apex Corp`

## Emoji Standard Policy
By executive request, emojis have been completely purged from all automated Slack communications. They are replaced with professional text bracket tags:
- `[ALERT]` for Compliance Holds
- `[MEETING PREP]` for concise briefs
- `[DRAFT]` for AI written outputs
- `[ACTION]` for meeting extracted tasks
- `[URGENT]` for priority inbound signals
