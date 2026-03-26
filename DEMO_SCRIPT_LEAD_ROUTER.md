# Module B - Lead Router (Demo Script Notes)

## The Objective
To showcase the system dynamically evaluating new, high-value incoming prospects and calculating immediate capacity across the advisor pool to make an intelligent assignment recommendation inside Slack.

## Context to Explain in the Video
**Speaker Note:** 
"When a new lead hits our system, we don't just assign it via a round-robin rotation. Our AI extracts their intent and AUM size. Then, we look at our team's active bandwidth across different departments."

"We use a custom Bandwidth Score—BWS. It weighs three factors: Active Clients (x3), Pending Prospects (x2), and Meetings this Week, scaled against an Advisor's maximum capacity base."

## The Slack Demonstration Workflow
**Step 1:** The speaker (or someone on the team) opens Slack and triggers the dynamic lead routing.

*Scenario A (UHNW Routing)*:
Type: `/route-prospect LexCorp Family Office - 120`
* **What the system does:** Recognizes "Family Office" and high AUM (>100M). Filters the search specifically to the **UHNW** department.
* **The Logic Result:** It looks at Dheeraj and Subiksha. It realizes Dheeraj has a much lower active workload (`BWS: 176.67`) compared to Subiksha (`BWS: 280.0`), immediately recommending Dheeraj.

*Scenario B (Investments Routing)*:
Type: `/route-prospect Tech Startup CEO - 45`
* **What the system does:** Recognizes standard criteria mapping to the **Investments** department.
* **The Logic Result:** Automatically recommends the appropriate team member (Jeremy Sim).

## Emphasizing the Flexibility & Team Setup
"We engineered it as a pure **recommendation engine**, rather than a hard constraint. Anyone on the executive team has the power to accept the assignment via the Slack buttons, or choose to 'Re-route' if they want a different team or department to handle the overflow."

"And because the UI is generated strictly via Slack Block Kit and tagged with the user who invoked it, we maintain a clear, emoji-free audit trail of who is routing which leads."
