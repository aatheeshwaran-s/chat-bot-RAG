# Top 3 Known System Weaknesses

> **Written and Dated: Wednesday, October 7, 2026**  
> **Author**: Lead AI Engineer, Tier-1 Deflection Assistant Squad  
> **Status**: Unprompted Pre-Defence Engineering Disclosure  
> *Committed prior to external review and Summit evaluation*

---

## 1. Weakness 1: Semantic Embedding Favoritism Towards Retired Macros

### Date Identified
Wednesday, October 7, 2026 · 11:15 AM

### Symptom & Observation
In the standalone RAG retrieval tier, querying tickets with customer phrasing such as *"I want to return an order after 18 days"* consistently scores `zendesk-macros.json` (specifically `MACRO-03: Return Window Expired (14 Days)`) with a higher cosine similarity ($0.841$) than the active article `refund-policy-current-30day.md` ($0.793$). 

### Root Cause
`MACRO-03` contains dense, high-frequency lexical tokens directly matching customer despair (*"expired"*, *"beyond return timeframe"*, *"cannot accept returns"*), whereas the official 30-day policy article is written in neutral, formal legal terms. Without an external entitlement check, naive top-$k$ semantic retrieval will reliably surface the retired macro and mislead the generator.

### Current Mitigation & Remaining Risk
- **Current Fix**: We implemented a mandatory ReAct tool gate (`entitlement_check_mcp`) that overrides raw retrieval scores with the customer's actual plan status.
- **Remaining Vulnerability**: If a customer ticket does not provide an Order ID or Customer ID (e.g. anonymous pre-purchase inquiry), the agent cannot execute an entitlement lookup. In such zero-context scenarios, the retriever still exhibits a $15\text{--}20\%$ statistical pull toward the retired 14-day macro text unless hard metadata filtering is applied to deprecate `MACRO-03`.

---

## 2. Weakness 2: Context Attention Split & Sub-Goal Dropping on Compound Inquiries

### Date Identified
Wednesday, October 7, 2026 · 02:40 PM

### Symptom & Observation
When a customer ticket bundles two distinct logistical inquiries into one message (e.g. Case `TRJ-07`: *"Can I return my router at Day 22, and what courier does DHL use to ship replacements to Berlin?"*), the agent exhibits an attention split (`CAT_A_CONTEXT_SPLIT`).

### Root Cause
The ReAct agent loop terminates as soon as it obtains a conclusive answer for the primary goal (return window approval). It fails to maintain an explicit goal scratchpad stack to track unresolved sub-clauses (the EU shipping courier and timeline).

### Current Mitigation & Remaining Risk
- **Current Fix**: The agent's final prompt reminds it to check for secondary questions, and unresolved inquiries are flagged for Tier-2 escalation if confidence on any sub-clause is low.
- **Remaining Vulnerability**: In 20% of multi-part cases, the assistant successfully deflects the return query but leaves the shipping question unanswered. This passes basic first-contact deflection metrics while triggering an immediate customer re-open within 24 hours.

---

## 3. Weakness 3: High Second-Contact Re-Open Rate on First-Time Approvals (Logistical Blindspot)

### Date Identified
Wednesday, October 7, 2026 · 05:20 PM

### Symptom & Observation
While our gross first-contact deflection rate reached **100%** on routine refund tickets, our second-contact evaluation revealed a **50.0% simulated re-open rate**. Half of the deflected customers wrote back within 48 hours asking operational follow-ups.

### Root Cause
The assistant's initial response answered the legal eligibility question (*"Yes, your return is approved under current 30-day policy"*) but omitted three practical operational details that customers immediately require:
1. Is return shipping prepaid, or must the customer pay courier postage?
2. Does the package need to be returned in original manufacturer retail packaging?
3. What is the expected credit timeline to the customer's bank statement?

### Current Mitigation & Remaining Risk
- **Current Fix**: We modified `capstone_second_contact.py` to benchmark and expose this exact gap rather than hiding behind a vanity 100% deflection metric.
- **Remaining Vulnerability**: Until our response generation template automatically appends standard return logistics (prepaid shipping label link, packing instructions, and 5–7 business day banking window), roughly 1 in 2 deflected customers will continue writing back to Tier-1 queues.
