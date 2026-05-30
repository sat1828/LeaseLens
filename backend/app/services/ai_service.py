"""
LeaseLens AI Analysis Service
Calls Claude API asynchronously — never blocks the event loop.
Three-strategy JSON parsing with graceful error recovery.
"""
import anthropic
import asyncio
import json
import re
import time
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import log

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are LeaseLens, an expert AI legal analyst specialising in residential and \
commercial lease agreements. Your sole purpose is protecting tenants.

JURISDICTION: {JURISDICTION}
APPLICABLE LAW:
{LAW_CONTEXT}

══ BEHAVIORAL RULES (STRICT — follow every one) ══
1. NEVER invent laws. If uncertain, mark SUSPECT and say "Verify with local Rent Authority."
2. Security deposit > 2× monthly rent (residential): CRITICAL + ILLEGAL. Cite MTA 2021 §11(2).
3. Any clause waiving tenant's right to Rent Tribunal/Rent Court: CRITICAL + ILLEGAL. Cite MTA 2021 §30.
4. Utility disconnection threat by landlord (water/electricity): CRITICAL + ILLEGAL. Cite MTA 2021 §23.
5. No eviction protection clause: HIGH risk. Per MTA 2021 Chapter V, ALL evictions require a \
Rent Authority/Tribunal order — no landlord can evict through notice alone. \
Clause must state: "Eviction only through Rent Authority order per MTA 2021 Chapter V." \
For rent revision: 90-day advance written notice required.
6. No 24-hour entry notice: HIGH + MISSING. Cite MTA 2021 §17.
7. Agreement > 11 months with no registration clause: HIGH risk. \
Unregistered agreements are inadmissible as evidence in Indian courts.
8. Default to RESIDENTIAL if lease_type is unclear.
9. counter_proposal_letter must be professional, cite specific law sections, ready to send.
10. plain_english: explain to a 22-year-old first-time renter with zero legal knowledge.
11. Maintenance: MTA 2021 Second Schedule assigns landlord duties (structural, whitewashing, plumbing, \
electrical wiring). Any clause shifting these to tenant = HIGH + UNFAIR.
12. TDS: If monthly rent > ₹50,000, agreement should mention tenant's TDS obligation under \
Income Tax Act §194-IB. Missing = MEDIUM risk on high-value leases.

══ FAIRNESS SCORING ══
Start at 50 (neutral baseline).
Each CRITICAL or ILLEGAL clause found: −15 points
Each HIGH risk clause: −8 points
Each MEDIUM risk clause: −3 points
Each FAVORABLE_TO_TENANT clause: +5 points
Each missing mandatory clause: −5 points
Clamp final score to [0, 100].

Score interpretation (include in your analysis context, do not output):
80–100: Tenant-favorable
60–79: Acceptable with negotiation
40–59: Risky — negotiate or consult lawyer
20–39: Predatory — strong recommendation do not sign
0–19: Illegal agreement — file complaint with Rent Authority

══ CLAUSE TAXONOMY ══
Check ALL 16 — flag each absent one as MISSING:
RENT_AMOUNT_AND_PAYMENT, RENT_ESCALATION, SECURITY_DEPOSIT, LEASE_DURATION,
NOTICE_PERIOD, MAINTENANCE_OBLIGATIONS, EVICTION_GROUNDS, ENTRY_AND_PRIVACY,
UTILITY_AND_SERVICES, SUBLETTING, LOCK_IN_PERIOD, ILLEGAL_CLAUSES,
DISPUTE_RESOLUTION, PENALTY_CLAUSES, MODIFICATION_RIGHTS, REGISTRATION_COMPLIANCE

══ OUTPUT FORMAT ══
Return ONLY valid JSON. No markdown fences. No backticks. No explanation before or after. \
First character must be { and last character must be }.

{
  "lease_summary": {
    "property_address": null,
    "landlord_name": null,
    "tenant_name": null,
    "lease_start": null,
    "lease_end": null,
    "monthly_rent": null,
    "currency": "INR",
    "security_deposit": null,
    "lease_type": "RESIDENTIAL"
  },
  "fairness_score": 50,
  "risk_summary": {
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0,
    "missing_clauses": [],
    "illegal_clauses": []
  },
  "clauses": [
    {
      "clause_id": "C001",
      "clause_type": "SECURITY_DEPOSIT",
      "verbatim_excerpt": "exact text from lease ≤150 words",
      "risk_level": "CRITICAL",
      "legal_status": "ILLEGAL",
      "plain_english": "max 80 words, plain language",
      "legal_citation": "Model Tenancy Act 2021, Section 11(2)",
      "negotiation_suggestion": "exact replacement wording to request from landlord",
      "fairness_weight": 1,
      "is_actionable": true
    }
  ],
  "top_3_negotiation_priorities": [
    {
      "priority": 1,
      "clause_id": "C001",
      "reason": "why this is the most urgent issue",
      "suggested_response_letter_snippet": "Dear Landlord, I write to request..."
    }
  ],
  "counter_proposal_letter": "Full formal letter text. Professional tone. Cites specific law sections. Ready to send with zero editing.",
  "legal_disclaimer": "LeaseLens provides AI-assisted analysis for informational purposes only. This is not legal advice. For CRITICAL findings, consult a qualified advocate registered with the Bar Council of India."
}"""

# ── National base law (MTA 2021 + 2025 Rules) ────────────────────────────────
BASE_LAW = """
Model Tenancy Act 2021 (MTA 2021) and Home Rent Rules 2025 — National Framework:

SECURITY DEPOSIT (§11):
  • Residential: MAXIMUM 2 months' rent. Commercial: MAXIMUM 6 months' rent.
  • Must be refunded within 1 month of tenant vacating. 18% p.a. interest if delayed.
  • Deductions only for actual proven damage beyond normal wear-and-tear.

EVICTION (Chapter V):
  • ALL evictions require a Rent Authority order — no self-help eviction permitted.
  • Grounds for eviction application: non-payment >2 months, subletting without consent,
    misuse of premises, landlord genuine need (with 3-month notice).
  • No landlord can evict by notice alone regardless of what the contract says.
  • For rent revision: 90 days written advance notice required.

ENTRY (§17):
  • Landlord must give minimum 24 hours advance written notice before entering.
  • Permitted reasons: inspection, repair, emergency only.
  • Entering without notice is a punishable offence.

UTILITY DISCONNECTION (§23):
  • EXPLICITLY ILLEGAL. Landlord CANNOT disconnect water, electricity, or any essential
    service for any reason including non-payment of rent.
  • Tenant remedy: approach Rent Authority immediately.
  • Landlord liability: criminal prosecution possible.

REGISTRATION:
  • Agreements > 11 months MUST be registered with the Rent Authority.
  • Unregistered agreements are inadmissible as evidence in any Indian court.
  • Both landlord and tenant must sign the tenancy agreement form.

RENT TRIBUNAL (§30):
  • Tenant's right to approach Rent Authority → Rent Court → Rent Tribunal
    CANNOT be waived by any contract clause. Such a clause is void ab initio.

MAINTENANCE (Second Schedule):
  • LANDLORD mandatory duties: structural repairs, whitewashing walls every 3 years,
    maintaining plumbing, maintaining electrical wiring, pest control.
  • TENANT duties: tap washers, drain cleaning, internal painting, minor repairs.
  • Tenant may deduct repair costs from rent (max 1 month/year) after 30-day written
    notice to landlord if landlord fails to act.

TDS (Income Tax Act §194-IB as amended Finance Act 2025):
  • Monthly rent > ₹50,000: Tenant must deduct TDS at 2%.
  • Agreement should mention TDS compliance obligation.
"""

# ── State-specific overrides — all 12 jurisdictions covered ──────────────────
STATE_OVERRIDES: dict[str, str] = {

    "karnataka": """
Karnataka Rent Act 1999 + MTA 2021 Framework (Karnataka adopted MTA Dec 2021):
• Bengaluru HC ruling: Utility disconnection by landlord carries criminal liability under IPC §503 (criminal intimidation).
• Security deposit enforcement: Courts routinely order return with 18% interest p.a. on illegally withheld deposits.
• Late fees: Cannot exceed simple interest at SBI base rate on outstanding rent — excessive penalties are void.
• Standard agreements: 11-month Leave & Licence is universal; agreements >11 months require sub-registrar registration.
• Rent Controller offices: Bengaluru (multiple zones), Mysuru, Hubballi — file complaints in the zone where property is located.
• Key risk: Many Bengaluru landlords insert 15-25% annual escalation — flag any rate above 10% as HIGH.
• Dispute resolution: Rent Controller → Rent Court (City Civil Court) → HC Karnataka.
""",

    "maharashtra": """
Maharashtra Rent Control Act 1999 + MTA 2021 Framework (Maharashtra partial adoption):
• Mumbai: Pagdi system (occupancy rights transfer) may apply to pre-1999 buildings — verify building year.
• Leave & Licence (L&L): Dominant agreement type in Maharashtra; governed by Indian Easements Act §52.
• Late payment interest: Maximum 15% per annum per MRCA §7A — higher rates are void.
• Stamp duty: L&L agreements require stamp duty payment within 30 days of execution.
• Mumbai HC: Security deposit withheld >30 days post-vacating is actionable in Small Causes Court Mumbai.
• Habitable condition: Landlord must maintain structural integrity regardless of contract.
• Dispute resolution: Rent Controller → Small Causes Court (Mumbai) or District Court → HC Bombay.
""",

    "delhi": """
Delhi Rent Control Act 1958 + MTA 2021:
• DRC 1958 applies ONLY to premises with standard rent ≤ ₹3,500/month (mostly older DDA/pre-1990 buildings).
• MTA 2021 governs ALL new agreements above ₹3,500/month threshold.
• Delhi HC: Security deposit wrongfully withheld — tenant entitled to double the deposit as penalty.
• Rent Authority: District Rent Controllers appointed zone-wise across Delhi.
• Subletting: DRC 1958 §14(1)(b) — subletting without consent is a specific eviction ground.
• Key issue: Many Delhi landlords insert "license" framing to avoid Rent Control — courts look at substance not labels.
• Dispute resolution: Rent Controller → Rent Court → Delhi HC (expedited tenancy matters).
""",

    "telangana": """
Telangana Buildings (Lease, Rent & Eviction) Control Act 1960 + MTA 2021:
• Act applies: Hyderabad, Secunderabad, Warangal, Karimnagar, Nizamabad, Khammam.
• Rent Controller: Separate Rent Controllers appointed per jurisdiction under §4 of the Act.
• Security deposit: MTA 2021 cap (2 months) is national floor; 3-month market practice — flag excess.
• GHMC area: Rental agreements must be registered for GHMC municipal property tax records.
• Eviction grounds: Strictly limited to §10 grounds — non-payment, subletting, misuse, self-requirement.
• Deposit refund: Within 1 month of vacating per MTA 2021 §11(3); 18% p.a. interest if delayed.
• Utility disconnection: Illegal under MTA 2021 §23 — carries criminal liability under IPC.
• Dispute resolution: Rent Controller → Appellate Authority → HC Telangana.
""",

    "tamil nadu": """
Tamil Nadu Buildings (Lease and Rent Control) Act 1960 + MTA 2021 Framework:
• TNBRC Act applies in notified areas: Chennai, Coimbatore, Madurai, Salem, Tiruchirappalli, Vellore.
• Fair rent fixation: Either party can apply to Rent Controller to fix/revise standard rent.
• Deposit cap: TNBRC §15 limits advance to 2 months; Chennai market often demands 5–10 months — flag ALL excess as CRITICAL.
• Eviction: Strictly regulated — landlord must obtain Rent Controller's order; self-help eviction is an offence.
• Chennai: Greater Chennai Corporation requires registered agreements for property tax records.
• Subtenancy: Subletting without written landlord consent = eviction ground under §10(2)(ii).
• Tenant protection: Unilateral lockout is a criminal offence under TNBRC Act §22.
• Dispute resolution: Rent Controller → Appellate Authority (District Court) → HC Madras.
""",

    "gujarat": """
Gujarat Rent Control Act 1947 + MTA 2021 National Framework:
• Act applies in notified municipalities: Ahmedabad, Surat, Vadodara, Rajkot, Gandhinagar, Bhavnagar.
• Standard rent fixation: Either party can apply to Rent Controller to fix standard rent under §11.
• Leave & Licence prevalent: Ahmedabad market uses L&L — stamp duty mandatory, paid within 30 days.
• Security deposit: MTA 2021 2-month cap; Gujarat market practice 2–3 months — flag excess.
• Permitted use clause: Agreement must specify residential/commercial — mixed use is an eviction ground.
• Eviction grounds: Strictly per §13 — landlord cannot add contractual grounds beyond the statute.
• Notarised vs registered: Notarised agreements are NOT the same as registered; only registered = court-admissible.
• Dispute resolution: Rent Controller → Appellate Rent Tribunal → HC Gujarat.
""",

    "west bengal": """
West Bengal Premises Tenancy Act 1997 + MTA 2021 Framework:
• WBPT Act applies across West Bengal including Kolkata, Howrah, Asansol, Durgapur, Siliguri.
• Rent increase: Permitted only after 3 years of tenancy per WBPT Act; annual escalation clauses are illegal.
• Security deposit: MTA 2021 2-month cap; Kolkata market practice 2–3 months — flag excess.
• Key Kolkata risk: Old buildings under Kolkata Municipal Corporation may have legacy rent control orders.
• Subletting: Written landlord consent mandatory; sublet without consent = immediate eviction ground.
• Eviction: Must be through Rent Controller; self-help eviction triggers criminal liability.
• Dispute resolution: Rent Controller → District Court → HC Calcutta.
""",

    "odisha": """
Odisha Rent Control Act 1967 + MTA 2021 National Framework:
• Act applies: Bhubaneswar, Cuttack, Puri, Rourkela, Sambalpur, Berhampur, Balasore.
• Rent Tribunal: District-level Rent Tribunals established for all dispute resolution.
• Security deposit: MTA 2021 2-month cap; local practice 2–4 months — flag any excess as CRITICAL.
• BDA/ODA buildings (Bhubaneswar): Development authority has standardised agreement templates — use as benchmark.
• Utility disconnection: Illegal under MTA 2021 §23; landlord liability includes criminal prosecution.
• Eviction: Only through Rent Tribunal order — no self-help permitted.
• Registration: All agreements >11 months must be registered at local Sub-Registrar office.
• Key local issue: Many Bhubaneswar agreements drafted under pre-MTA 2021 formats; flag missing clauses heavily.
• Dispute resolution: Rent Tribunal (district) → HC Odisha (Cuttack).
""",

    "rajasthan": """
Rajasthan Rent Control Act 2001 + MTA 2021 National Framework:
• Act applies in all major cities: Jaipur, Jodhpur, Kota, Udaipur, Ajmer, Bikaner.
• Rent Controller: Separate Rent Controllers in each jurisdiction; file complaints at property location.
• Security deposit: MTA 2021 2-month cap is national floor; flag any excess as CRITICAL.
• Eviction notice: Must be served by registered post to be legally valid — verbal notice has no legal standing.
• Stamp duty: Leave & Licence agreements require stamp duty per Rajasthan Stamp Act 1998 Schedule 1A.
• Registration: Compulsory for agreements >11 months at District Registrar office.
• Key risk: Many Rajasthan landlords draft agreements citing old 1950 Act — verify applicable Act; MTA 2021 governs new agreements.
• Advance rent: Collecting >1 month advance as token money beyond the deposit is illegal.
• Dispute resolution: Rent Controller → Rent Court (Sessions level) → HC Rajasthan.
""",

    "uttar pradesh": """
Uttar Pradesh Urban Buildings (Regulation of Letting, Rent & Eviction) Act 1972 + MTA 2021:
• UP 1972 Act applies in notified urban areas: Lucknow, Kanpur, Agra, Varanasi, Allahabad, Meerut.
• Fair rent fixation: Rent Fixation Officer determines standard rent on application from either party.
• Security deposit: MTA 2021 2-month cap; UP market practice varies — flag any amount >2 months.
• Eviction grounds: Strictly limited to §20 of UP 1972 Act — landlord CANNOT add custom eviction grounds.
• Noida/Greater Noida: Builder-society agreements often use Leave & Licence format — treated differently.
• Advance rent: Collecting >1 month advance as token money is illegal under UP Act.
• RERA: For builder flats, RERA registration of the project must be verified before signing.
• Dispute resolution: Rent Control & Eviction Officer (district) → District Court → HC Allahabad.
""",

    "kerala": """
Kerala Buildings (Lease and Rent Control) Act 1965 + MTA 2021 Framework:
• KBL&RC Act applies across Kerala: Kochi, Thiruvananthapuram, Kozhikode, Thrissur, Kannur.
• Advance deposit: Collecting >2 months' advance rent is prohibited under KBL&RC §21 — flag as CRITICAL.
• Fair rent: Either party can apply to Rent Control Court (Munsiff level) to fix/revise fair rent.
• Eviction: Only Rent Control Court can order eviction — self-help eviction is a criminal offence.
• Kochi specifics: GCDA/KIIFB buildings may have different regulatory regimes — verify building category.
• Kerala HC ruling (2019): Landlord disconnecting utilities = criminal intimidation under IPC §503 + §506.
• Rent revision: Landlord can apply for revision every 5 years; excessive annual escalation clauses = void.
• Dispute resolution: Rent Control Court (Munsiff) → District Court → HC Kerala.
""",
}


def get_jurisdiction_context(jurisdiction: str) -> str:
    """Return jurisdiction-specific legal context. Falls back to BASE_LAW for unrecognised jurisdictions."""
    j_lower = jurisdiction.lower()
    for state_key, override in STATE_OVERRIDES.items():
        if state_key in j_lower:
            return BASE_LAW + "\nState-Specific Rules (take precedence over national framework):\n" + override
    return BASE_LAW


# ── Main async analysis function ─────────────────────────────────────────────
async def analyze_lease(lease_text: str, jurisdiction: str) -> dict:
    """
    Async lease analysis using AsyncAnthropic — never blocks the event loop.
    Includes exponential-backoff retry on connection errors (not rate limits).
    """
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(503, "AI service not configured. Set ANTHROPIC_API_KEY in .env")

    law_context = get_jurisdiction_context(jurisdiction)
    system = (
        SYSTEM_PROMPT
        .replace("{JURISDICTION}", jurisdiction)
        .replace("{LAW_CONTEXT}", law_context)
    )

    # Truncate with logged warning — never silently lose clauses
    MAX_CHARS = 75_000
    if len(lease_text) > MAX_CHARS:
        log.warning(
            "lease.text.truncated",
            original_chars=len(lease_text),
            truncated_to=MAX_CHARS,
        )
        lease_text = (
            lease_text[:MAX_CHARS]
            + "\n\n[SYSTEM NOTE: Document truncated at 75,000 characters. "
            "Flag REGISTRATION_COMPLIANCE and any missing clauses as HIGH risk "
            "due to incomplete document.]"
        )

    user_content = (
        f"Jurisdiction: {jurisdiction}\n\n"
        f"Lease Agreement Text:\n\n{lease_text}"
    )

    start = time.time()
    log.info("ai.analysis.start", jurisdiction=jurisdiction, chars=len(lease_text))

    # BUG-01 FIX: AsyncAnthropic — never blocks the event loop
    async with anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) as client:
        for attempt in range(3):
            try:
                response = await client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    system=system,
                    messages=[{"role": "user", "content": user_content}],
                    timeout=90.0,
                )
                break  # success — exit retry loop
            except anthropic.AuthenticationError:
                raise HTTPException(500, "Invalid Anthropic API key. Check ANTHROPIC_API_KEY in .env")
            except anthropic.RateLimitError:
                raise HTTPException(429, "AI service overloaded. Please retry in 30 seconds.")
            except anthropic.APIConnectionError:
                if attempt == 2:
                    raise HTTPException(503, "Cannot reach AI service. Check your internet connection.")
                wait = 2 ** attempt  # 1s, 2s exponential backoff
                log.warning("ai.connection.retry", attempt=attempt + 1, wait_s=wait)
                await asyncio.sleep(wait)
            except Exception as e:
                log.error("ai.api.error", error=str(e))
                raise HTTPException(503, f"AI service error: {str(e)}")

    elapsed_ms = int((time.time() - start) * 1000)
    raw = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens

    log.info("ai.analysis.done", elapsed_ms=elapsed_ms, tokens=tokens)

    result = _parse_json(raw)
    result["_processing_time_ms"] = elapsed_ms
    result["_tokens_used"] = tokens
    result["_model"] = "claude-sonnet-4-20250514"
    return result


def _parse_json(raw: str) -> dict:
    """
    Three-strategy JSON extraction. Never fails silently.
    Strategy 1: direct parse.
    Strategy 2: strip markdown fences.
    Strategy 3: find outermost braces.
    """
    raw = raw.strip()

    # Strategy 1: direct
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: markdown fence
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: outermost braces
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            pass

    log.error("ai.parse.failed", preview=raw[:300])
    raise HTTPException(
        500,
        "The AI returned an unreadable response. This is rare — please try again. "
        "If it persists, report it to support."
    )
