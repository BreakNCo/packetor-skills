---
name: bigin-company-research
description: This skill should be used when the user asks to research a company and update Zoho Bigin CRM, enrich existing Bigin contacts/accounts with latest company information, gather company details before creating new Bigin records, or verify/update company information (website, technologies, employee count, funding, etc.). Trigger phrases include "research [company] in Bigin", "update [company] details in Bigin", "/research [company]", or "enrich [company] account".
version: 2.0.0
compatibility: openclaw
tools:
  - ZohoMCP
  - firecrawl
  - gooseworks
---

# Bigin Company Research

Research companies using Firecrawl (web scraping) boosted by targeted GooseWorks API calls, then create or update their records in Zoho Bigin CRM. **The output must always be a detailed, structured note — never a brief summary.** See the mandatory note format in Step 4.

GooseWorks is used **additively** — it fills gaps that Firecrawl misses (brand metadata, employee count, industry classification) via cheap single-API calls, not by running heavy multi-step skills.

## When to Use

- User asks to research a company and update Bigin
- Need to enrich existing Bigin accounts with latest company info
- Want to gather company details before creating a new Bigin record
- Need to verify or update company data (website, employee count, funding, tech stack, etc.)

## When NOT to Use

- Simple Bigin lookups — use ZohoMCP tools directly
- Company research without Bigin updates — use Firecrawl or GooseWorks only
- Bulk operations on many companies — use the batch script (`scripts/bigin-scanner.py`)
- Real-time financial data requiring authenticated feeds

## Prerequisites

**MCP Servers / Tools required:**
- `ZohoMCP` — Bigin CRM read/write
- `firecrawl` — Web scraping and search (primary research layer)
- `gooseworks` — Targeted gap-fill calls for brand/company metadata (additive layer)

**GooseWorks login check:** If any `gooseworks` command fails with "Not logged in", tell the user to run `npx gooseworks login`.

**Credit tracking:** Keep a running tally throughout the workflow. Each `gooseworks call` prints a `Cost: N credits` line — add those up. For Apollo, count the number of contacts successfully enriched in Phase 2 (each = 1 Apollo credit). Report both totals in the note's **Credits Used** section and as a final summary to the user after the run completes.

**Credit budget:** Check balance before starting: `npx gooseworks credits`. The GooseWorks calls in this skill cost **~5–15 credits total per company** (not 100+). Never invoke full GooseWorks skills (e.g. `tech-stack-teardown`, `company-intel`) — use direct API calls only.

**Phone reveal webhook setup (one-time, required for contact phone numbers):**

Apollo's `reveal_phone_number` flag is async — it fires a POST callback to a public webhook URL. Both `apollo_webhook_server.py` and ngrok run on the **other laptop**. The webhook server stores results in memory and exposes them via `GET /result/<id>`. The skill on this machine polls that HTTP endpoint over the ngrok URL — no filesystem sharing needed.

```
Apollo API
    │  fires POST callback to ngrok URL
    ▼
ngrok (other laptop)
    │  forwards to localhost:9055
    ▼
apollo_webhook_server.py (other laptop, port 9055)
    │  stores result in memory at GET /result/<person_id>
    ▼
apollo_phone_reveal.py (this machine)
    │  polls GET <ngrok_url>/result/<person_id> every 3s
    ▼
Returns phone + email JSON to the skill
```

**Step-by-step setup (do this once per ngrok session on the other laptop):**

```bash
# --- ON THE OTHER LAPTOP ---

# 1. Copy apollo_webhook_server.py to the other laptop (or clone the repo there)

# 2. Start the webhook server (keep this terminal open)
python3 apollo_webhook_server.py --port 9055

# 3. In a second terminal, start ngrok
ngrok http 9055
# ngrok prints a public URL like: https://abc123.ngrok-free.app
```

```bash
# --- ON THIS MACHINE ---

# 4. Save the ngrok URL that was printed
echo "https://abc123.ngrok-free.app" > ~/.apollo_webhook_url

# 5. Verify it works end-to-end
curl $(cat ~/.apollo_webhook_url)/
# Expected: {"status":"ok"}
```

**Before running this skill, always verify the webhook is reachable:**

```bash
WEBHOOK_URL=$(cat ~/.apollo_webhook_url 2>/dev/null)
if [ -z "$WEBHOOK_URL" ]; then
  echo "NOT SET — ask user for ngrok URL"
else
  curl -s "$WEBHOOK_URL/" | grep -q '"ok"' && echo "WEBHOOK OK" || echo "WEBHOOK DOWN"
fi
```

If `~/.apollo_webhook_url` is missing or the health check fails, **stop and ask the user** to start `apollo_webhook_server.py` and ngrok on the other laptop, then provide the URL. Do not skip phone enrichment.

The ngrok URL changes each time ngrok restarts (free tier). Update `~/.apollo_webhook_url` each session. Paid ngrok plans have a static domain and only need setup once.

---

## Workflow

### Step 1 — Lookup in Bigin

```
mcp__ZohoMCP__Bigin_searchRecords(module_api_name: "Accounts", word: "<company_name>")
```

- If found: note the account ID, existing website, and any already-populated fields
- If not found: proceed with research, then create a new record at Step 3

---

### Step 2 — Deep Multi-Source Research (mandatory)

Run **all** of the following sub-steps. Do not stop early. Collect everything before writing the note.

#### 2a. Company website (primary source — Firecrawl)

```
mcp__firecrawl__firecrawl_scrape(url: "<website>", formats: ["markdown"])
```

If website URL is unknown, discover it first:
```
mcp__firecrawl__firecrawl_search(query: "<company_name> official website", limit: 3)
```

#### 2b. LinkedIn (Firecrawl)

```
mcp__firecrawl__firecrawl_search(query: "<company_name> LinkedIn company page", limit: 3)
```

Scrape the LinkedIn page if accessible:
```
mcp__firecrawl__firecrawl_scrape(url: "<linkedin_url>", formats: ["markdown"])
```

#### 2c. Tech stack discovery (Firecrawl)

```
mcp__firecrawl__firecrawl_search(query: "<company_name> technology stack built with", limit: 3)
```

Also scrape BuiltWith or similar tech profiler pages if found in results.

#### 2d. News, funding, and background (Firecrawl)

```
mcp__firecrawl__firecrawl_search(query: "<company_name> funding news founded history", limit: 5)
```

#### 2e. Review / profile sites (Firecrawl)

Search Crunchbase, Tracxn, G2, Clutch, ZoomInfo, or AngelList as relevant:
```
mcp__firecrawl__firecrawl_search(query: "<company_name> Crunchbase OR Tracxn OR ZoomInfo profile", limit: 3)
```

Scrape any useful profile pages found.

#### 2f. GooseWorks Brand Lookup (~1–2 credits)

```bash
gooseworks call brand-dev /v1/brand/retrieve --query='{"domain":"<company_domain>"}'
```

Returns: industry classification, company description, logo URL, brand colours, founding year, employee range, social links. **~1–2 GooseWorks credits.**

#### 2g. GooseWorks Company Search (~2–5 credits)

```bash
gooseworks call fiber /v1/company-search --body='{"searchParams":{"company_names":["<company_name>"]},"pageSize":1}'
```

Returns: employee count, HQ city/country, industry, LinkedIn URL, funding stage. **~2–5 GooseWorks credits.**

Synthesise all findings from 2a–2g before moving to Step 3.

---

### Step 3 — Upsert Bigin Record

Fields listed in `config.research.skipFieldsIfPopulated` (`Account_Name`, `Website` by default) must **not** be overwritten if they already have a value. Never overwrite any field with an empty or uncertain value.

**Update existing account:**
```
mcp__ZohoMCP__Bigin_updateSpecificRecord(
  module_api_name: "Accounts",
  id: "<account_id>",
  data: {
    "Account_Name": "...",
    "Website": "...",
    "Description": "...",
    "Industry": "...",
    "Employees": 0,
    "Phone": "...",
    "Twitter": "...",
    "Billing_City": "...",
    "Billing_State": "...",
    "Billing_Country": "...",
    "Company_Linkedin_Url": "...",
    "Technologies": "...",
    "Founded_Year": "...",
    "Funding_Info": "...",
    "ISO_Certifications": "..."
  }
)
```

**Create new account:**
```
mcp__ZohoMCP__Bigin_addRecords(
  module_api_name: "Accounts",
  data: [{ "Account_Name": "...", "Website": "...", "Description": "...", "Industry": "...", "Account_Type": "Prospect" }]
)
```

---

### Step 4 — Add Detailed Research Note (mandatory, full format required)

Always create a comprehensive structured note using **exactly** the template below. Every section must be present. Use "Not found" for any field you genuinely could not locate — do not omit sections or collapse them into a one-liner.

Use `mcp__ZohoMCP__Bigin_addNotes` with the `data` array format:

```
mcp__ZohoMCP__Bigin_addNotes(
  data: [{
    "Note_Title": "Company Research - <YYYY-MM-DD>",
    "se_module": "Accounts",
    "Parent_Id": "<account_id>",
    "Note_Content": "<full structured note — see template below>"
  }]
)
```

> **Important:** Always use `mcp__ZohoMCP__Bigin_addNotes` (bulk tool with `data` array + `Parent_Id` + `se_module`). Do NOT use `mcp__ZohoMCP__Bigin_addNotesToSpecificRecord` — it uses a different schema that is incompatible.

> **Updating a note:** `mcp__ZohoMCP__Bigin_updateNotes` requires a `data` wrapper that the tool's schema does not expose, so it always fails with `MANDATORY_NOT_FOUND`. The workaround is: (1) delete the old note with `mcp__ZohoMCP__Bigin_deleteSpecificNote`, then (2) re-add a new one with `mcp__ZohoMCP__Bigin_addNotes`.

#### Mandatory Note Template

```
## Company Profile: <Legal Company Name>

### Overview
<2–4 sentence narrative: what the company does, who it serves, its positioning, and any standout facts.>

### Company Details
- **Company Name:** <full legal name>
- **Employees:** <number or range>
- **Industry:** <sector>
- **Founded:** <year>
- **Location:** <full address or city/country>
- **Phone:** <phone number>
- **Markets:** <geographic markets served>
- **Website:** <URL>
- **LinkedIn:** <URL>
- **Twitter:** <URL>
- **Facebook:** <URL>

### Technology Stack
<Organise by category. List every technology found. Write "Not found" if nothing discovered.>
- **Email:** ...
- **Hosting:** ...
- **Backend:** ...
- **Frontend:** ...
- **Database:** ...
- **CMS:** ...
- **Containerization:** ...
- **Monitoring:** ...
- **Analytics:** ...
- **Marketing:** ...
- **Collaboration:** ...
- **Security:** ...
- **Other:** ...

### Core Services/Products
<Bulleted list of every distinct service or product offering found.>

### Key Insights
<Bulleted list of notable facts: years in business, client count, certifications, awards, partnerships, notable clients, recent milestones, funding rounds.>

### Market Position
<1–2 sentences on where this company sits in its market: niche, scale, competition, geography.>

### Target Customer Profile
<Bulleted list of the types of customers this company targets.>

### Business Strengths
<Bulleted list of concrete strengths backed by evidence found.>

### Competitive Differentiators
<Bulleted list of what makes this company stand out vs competitors.>

### Key Contacts
<Contacts found via Apollo Phase 2 enrichment, grouped by priority tier. For each contact include: Name, Title, Email, Phone (if available), LinkedIn URL. Write "Not found" if Apollo returned no results.>

**Priority 1 — Office / Perfect Contact**
- <Name> | <Title> | <Email> | <Phone> | <LinkedIn>

**Priority 2 — C-Suite**
- <Name> | <Title> | <Email> | <Phone> | <LinkedIn>

**Priority 3 — Security / Compliance / IT**
- <Name> | <Title> | <Email> | <Phone> | <LinkedIn>

**Priority 4 — Engineering / Technical**
- <Name> | <Title> | <Email> | <Phone> | <LinkedIn>

**Priority 5 — Fallback**
- <Name> | <Title> | <Email> | <Phone> | <LinkedIn>

### Research Date
<YYYY-MM-DD>

### Data Sources
<List every URL and GooseWorks tool used as a source.>

### Credits Used
- **GooseWorks credits:** <total GooseWorks credits consumed this run — sum of brand-dev call + fiber call + people/match calls (email+phone reveal), reported from `Cost: N credits` output of each gooseworks call>
- **Apollo credits:** <total Apollo credits consumed — number of contacts enriched in Phase 2, since each enrichment costs 1 Apollo credit>
```

---

## Step 5 — Apollo Contact Finder (runs every time, fully automatic)

Apollo API key is passed by the user as an argument (e.g. `APOLLO_API_KEY=xxx`) or read from `~/.env`.

**All Apollo API calls must use the `X-Api-Key` header — NOT `api_key` in the request body.** The body-key form returns `INVALID_API_KEY_LOCATION` and zero results without an error status code, making it a silent failure.

### Step 5a — Resolve the Apollo Org ID

Apollo's people search by domain name or company name string often returns zero results for small/new companies even when they exist in Apollo. The reliable approach is to search by the Apollo **organization ID** directly.

**If the user provides an Apollo URL** (e.g. `https://app.apollo.io/#/organizations/65699c9de77d770001ea387e`), extract the org ID from the URL hash fragment and fetch the org to confirm:

```bash
APOLLO_ORG_ID="<id_from_url>"
curl -s "https://api.apollo.io/v1/organizations/$APOLLO_ORG_ID" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -H "Cache-Control: no-cache"
```

**If no Apollo URL is provided**, try to find the org ID via domain search first, but be aware this fails for small companies:

```bash
# Try 1 — domain search (fails silently for unindexed companies)
curl -s -X POST "https://api.apollo.io/api/v1/mixed_companies/search" \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d '{"q_organization_domains": ["<company_domain>"], "per_page": 1}'
```

If domain search returns no org, **inform the user** that the company was not found in Apollo's search index and ask them to provide the Apollo org URL directly from `app.apollo.io`. Do not attempt name-based search as a fallback — it is equally unreliable for small companies.

### Step 5b — Fetch People by Org ID

Once the org ID is known, use `mixed_people/api_search` with `organization_ids`. This endpoint reaches records that `people/search` and the deprecated `mixed_people/search` cannot find:

```bash
# Phase 1 — get person IDs (names/emails are masked at this stage)
curl -s -X POST "https://api.apollo.io/api/v1/mixed_people/api_search" \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d "{
    \"organization_ids\": [\"$APOLLO_ORG_ID\"],
    \"per_page\": 25
  }"
```

> **Why not `people/search` or `mixed_people/search`?**
> - `people/search` with `organization_ids` returns 0 results for small companies.
> - `mixed_people/search` is deprecated and returns an error directing you to `mixed_people/api_search`.
> - `mixed_people/api_search` with `organization_ids` is the only endpoint that reliably returns all people for a given org ID.

The response contains person objects with `id` and `title` but **names and emails are masked**. Collect all person IDs.

> **Critical — confirm identity before enrichment:** `mixed_people/api_search` returns masked names, so **never assume name-to-ID mapping by position or order**. For each person ID, call `people/match` once WITHOUT `reveal_phone_number` to confirm the real name, title, and email before firing the paid phone reveal. Store the confirmed `{id, name, title, email}` mapping and use it throughout — including when storing webhook results and writing to Bigin. This prevents phones being assigned to the wrong contact, which happened when IDs were assumed to map to names in a certain order but Apollo returned them differently.

#### Contact Priority Order

Enrich all contacts found — do not filter before enrichment. After enrichment, group by priority tier in the note:

| Priority | Roles |
|---|---|
| 1 — Office / Perfect Contact | Main office number, general enquiries contact, company secretary |
| 2 — C-Suite | CEO, CTO, COO, Managing Director, General Manager, Founder, Director |
| 3 — Security / Compliance / IT | CIO, CISO, Compliance Manager, GRC Specialist, ISO Specialist, Information Security Manager, Risk Manager, Data Protection Officer |
| 4 — Engineering / Technical | Technical Architect, Director of Engineering, Senior Engineering Manager, VP Engineering, Head of Technology |
| 5 — Fallback | Receptionist, HR Manager, Business Analyst, other staff |

### Step 5c — Enrich Each Contact via people/match

For every person ID from Phase 1, call `/api/v1/people/match` to reveal name, email, and phone. This is where Apollo credits are consumed (1 credit per call).

> **Critical:** `reveal_phone_number`, `run_waterfall_phone`, and `webhook_url` MUST be **query parameters** in the URL — NOT in the request body. Putting them in the body is silently ignored: Apollo returns person data but never fires the webhook callback. This was confirmed by Apollo's official docs and live testing.

```bash
WEBHOOK_URL=$(cat ~/.apollo_webhook_url)
ENCODED_WEBHOOK_URL=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$WEBHOOK_URL', safe=''))")

curl -s -X POST "https://api.apollo.io/api/v1/people/match?reveal_phone_number=true&run_waterfall_phone=true&webhook_url=${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -H "X-Api-Key: $APOLLO_API_KEY" \
  -d "{
    \"id\": \"<person_id>\"
  }"
```

A successful phone reveal request returns a `waterfall` field in the response:
```json
"waterfall": {"status": "accepted", "message": "Waterfall enrichment request accepted. Results will be sent to the provided webhook URL."}
```

If `waterfall.status` is `"failed"`, Apollo has no phone data for that contact (no callback will arrive). This is normal for small companies.

The sync response returns `name`, `email`, `email_status`, `linkedin_url`, `city`, `state`, `country`, `seniority`, `departments`. **Phone numbers arrive asynchronously** — Apollo fires a POST to the webhook URL after it completes the reveal (can take 30–120s per contact).

**Run enrichment sequentially** — one contact at a time. Each call costs 1 Apollo credit.

### Step 5d — Poll for Phone Results (blocking, do not skip)

After firing all `people/match` calls, poll the webhook for every contact **until all results arrive or the hard timeout expires**. Do not proceed to Bigin insertion while results are still pending.

```bash
WEBHOOK_URL=$(cat ~/.apollo_webhook_url)
HARD_TIMEOUT=300   # 5 minutes total — Apollo can be slow
POLL_INTERVAL=5    # check every 5 seconds

declare -A pending  # person_id -> 1
declare -A phones   # person_id -> phone string

for id in <all_person_ids>; do pending[$id]=1; done

elapsed=0
while [ ${#pending[@]} -gt 0 ] && [ $elapsed -lt $HARD_TIMEOUT ]; do
  sleep $POLL_INTERVAL
  elapsed=$((elapsed + POLL_INTERVAL))
  for id in "${!pending[@]}"; do
    result=$(curl -s "$WEBHOOK_URL/result/$id")
    ready=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ready',False))")
    if [ "$ready" = "True" ]; then
      phone=$(echo "$result" | python3 -c "
import sys, json
d = json.load(sys.stdin).get('data', {})
p = d.get('person', d)
nums = p.get('phone_numbers') or []
mobile = next((n['sanitized_number'] for n in nums if n.get('type')=='mobile'), None)
work   = next((n['sanitized_number'] for n in nums if n.get('type')=='work'), None)
print(mobile or work or '')
")
      phones[$id]="$phone"
      unset pending[$id]
      echo "Got phone for $id: $phone"
    fi
  done
  echo "Waiting... ${#pending[@]} contacts still pending (${elapsed}s elapsed)"
done

if [ ${#pending[@]} -gt 0 ]; then
  echo "Timed out waiting for: ${!pending[@]}"
fi
```

**Key rules:**
- **Never time out after just 8–10 seconds.** Apollo phone reveal is async and regularly takes 60–120s per contact. The hard timeout is 5 minutes (300s). Only give up after that.
- After the poll loop completes (or times out), proceed to Bigin insertion using whatever phone data arrived. Contacts that timed out get inserted without a phone number — do not block or skip them.
- Results are **persisted in SQLite** (`apollo_results.db` alongside the server script) — they survive server restarts. If the server was restarted mid-run, simply poll again; the results will still be there. Do NOT re-fire `people/match` just because the server restarted.
- Do NOT issue `DELETE /result/<id>` calls — results are intentionally kept forever as an audit trail.

**If `~/.apollo_webhook_url` is missing:** Stop and ask the user for the ngrok URL before proceeding. Do not skip phone enrichment.

**Diagnosing a persistent timeout (all contacts, 2+ minutes):** If zero results arrive after 120s, run this diagnostic before assuming Apollo is slow:

```bash
# 1. Verify the webhook server is actually storing POSTs (should return ready:true)
curl -s -X POST "$WEBHOOK_URL/" -H "Content-Type: application/json" \
  -d '{"person":{"id":"diag_test","phone_numbers":[{"sanitized_number":"+1234","type":"mobile"}]}}'
sleep 1
curl -s "$WEBHOOK_URL/result/diag_test"   # expect {"ready":true,...}

# 2. Check if Apollo actually has phone data (sync call WITHOUT reveal_phone_number)
curl -s -X POST "https://api.apollo.io/api/v1/people/match" \
  -H "X-Api-Key: $APOLLO_API_KEY" -H "Content-Type: application/json" \
  -d "{\"id\":\"<person_id>\",\"reveal_phone_number\":false}" \
  | python3 -c "import sys,json; p=json.load(sys.stdin).get('person',{}); print('phones:', p.get('phone_numbers'), 'org_phone:', p.get('organization',{}).get('phone',''))"
```

If step 1 returns `ready:true` but step 2 shows `phone_numbers: None` — **Apollo has no phone data for this contact**. The webhook callback will never arrive because there is nothing to reveal. This is expected for small/new companies. Record the org phone number (`organization.phone`) as `Corporate_Phone` in Bigin if available. If the user saw phone numbers in the Apollo UI, they were sourced from a live enrichment provider that Apollo only exposes via paid plans — the API may not surface the same data.

### Step 5e — Update Bigin Contacts with Phone Numbers

After the poll loop, update any Bigin contact records that received a phone number. Use `mcp__ZohoMCP__Bigin_updateSpecificRecord` for the Contacts module:

```
mcp__ZohoMCP__Bigin_updateSpecificRecord(
  module_api_name: "Contacts",
  id: "<bigin_contact_id>",
  data: [{ "Mobile": "<sanitized_number>" }]
)
```

Run this for every contact where a phone was returned. Then update the research note's Key Contacts section to reflect the phone numbers received (delete old note + re-add with updated content, since `updateNotes` is broken — see Step 4).

### Step 5b — Insert Apollo Contacts into Bigin

For each enriched contact returned by Apollo Phase 2, create a Contact record in Bigin linked to the Account. Use `mcp__ZohoMCP__Bigin_addRecords` for the Contacts module:

```
mcp__ZohoMCP__Bigin_addRecords(
  module_api_name: "Contacts",
  data: [
    {
      "First_Name": "<first_name>",
      "Last_Name": "<last_name>",
      "Full_Name": "<name>",
      "Title": "<title>",
      "Seniority": "<seniority>",
      "Departments": "<departments[0]>",
      "Email": "<email>",
      "Secondary_Email": "<personal_emails[0] if different from email>",
      "Email_Confidence": "<email_status>",
      "Mobile": "<phone_numbers[0].sanitized_number where type=mobile — from apollo_phone_reveal.py output>",
      "Corporate_Phone": "<phone_numbers[0].sanitized_number where type=work, OR primary_phone as fallback>",
      "Account_Name": { "id": "<account_id>", "name": "<account_name>" },
      "Person_Linkedin_Url": "<linkedin_url>",
      "Company_Linkedin_Url": "<organization.linkedin_url>",
      "Twitter_Url": "<twitter_url>",
      "Facebook_Url": "<facebook_url>",
      "Website": "<organization.website_url>",
      "Technologies": "<organization.technology_names comma-separated>",
      "Mailing_City": "<city>",
      "Mailing_State": "<state>",
      "Mailing_Country": "<country>",
      "Description": "Imported from Apollo. Org: <organization_name>. Headline: <headline>."
    },
    ... (one object per contact)
  ]
)
```

**Rules:**
- Link every contact to the Account using the `Account_Name` lookup field with the Bigin account ID from Step 1
- Only insert contacts that have at least a `Last_Name` and either an `Email` or `Title` — skip bare stubs
- Do not insert duplicates: before inserting, search for each contact by email (`mcp__ZohoMCP__Bigin_searchRecords(module_api_name: "Contacts", email: "<email>")`) and skip if already present
- Omit any field that is null/empty — do not send empty strings
- Insert in a single batch call where possible (pass all contact objects in the `data` array)

---

## Field Mapping

See `references/field-mapping.md` for the full scraped-key → Bigin API field mapping. Summary:

| Bigin Field | Source |
|---|---|
| `Account_Name` | Company legal name |
| `Website` | Primary domain (Firecrawl) |
| `Description` | About/mission text — Firecrawl, supplemented by brand-dev `description` |
| `Industry` | Firecrawl, supplemented by brand-dev `industry` or fiber `industry` |
| `Employees` | Firecrawl, supplemented by brand-dev `employeeRange` or fiber `employeeCount` |
| `Phone` | Main contact number (Firecrawl) |
| `Twitter` | Twitter/X URL (Firecrawl or brand-dev `twitter`) |
| `Billing_City` | HQ city (Firecrawl or fiber `hqCity`) |
| `Billing_State` | HQ state/region |
| `Billing_Country` | HQ country |
| `Company_Linkedin_Url` | LinkedIn URL (Firecrawl or fiber `linkedinUrl`) |
| `Technologies` | Comma-separated tech stack (Firecrawl) |
| `Founded_Year` | 4-digit year (Firecrawl or brand-dev `foundedYear`) |
| `Funding_Info` | e.g. "Series B, $20M (2024)" (Firecrawl) |
| `ISO_Certifications` | e.g. "ISO 27001, SOC 2" (Firecrawl) |

**Contact fields (from Apollo Phase 2 → Bigin Contacts module):**

| Bigin Field | Apollo Source |
|---|---|
| `First_Name` | `first_name` |
| `Last_Name` | `last_name` |
| `Full_Name` | `name` |
| `Title` | `title` |
| `Seniority` | `seniority` |
| `Departments` | `departments[0]` |
| `Email` | `email` |
| `Secondary_Email` | `personal_emails[0]` (if different from primary) |
| `Email_Confidence` | `email_status` (e.g. "verified") |
| `Mobile` | `phone_numbers[].sanitized_number` where `type=mobile` — from `apollo_phone_reveal.py` output |
| `Corporate_Phone` | `phone_numbers[].sanitized_number` where `type=work`, fallback to `primary_phone` (org number) |
| `Account_Name` | Linked via account `id` from Step 1 |
| `Person_Linkedin_Url` | `linkedin_url` |
| `Company_Linkedin_Url` | `organization.linkedin_url` |
| `Twitter_Url` | `twitter_url` |
| `Facebook_Url` | `facebook_url` |
| `Website` | `organization.website_url` |
| `Technologies` | `organization.technology_names` (comma-separated) |
| `Mailing_City` | `city` |
| `Mailing_State` | `state` |
| `Mailing_Country` | `country` |
| `Description` | Auto-generated: "Imported from Apollo. Org: `organization_name`. Headline: `headline`." |

---

## GooseWorks Credit Budget

| Call | Tool | Cost | Runs |
|---|---|---|---|
| Brand/industry lookup | `gooseworks call brand-dev /v1/brand/retrieve` | ~1–2 credits | Every run |
| Employee/HQ lookup | `gooseworks call fiber /v1/company-search` (pageSize: 1) | ~2–5 credits | Every run |
| Apollo contact search | `apollo-lead-finder` Phase 1 | **Free** | Every run |
| Apollo contact enrich | `apollo-lead-finder` Phase 2 | 1 Apollo credit/contact | Every run, automatic |
| Apollo email + phone reveal | `curl` direct to `https://api.apollo.io/api/v1/people/match` | **0 GooseWorks credits** (direct Apollo API, uses Apollo credits) | Every run, per contact from Phase 1 |

**Target: ≤15 GooseWorks credits per company research run.**

Never invoke full GooseWorks skills like `tech-stack-teardown` or `company-intel` as part of this workflow — those invoke Apify actors internally and can cost 50–100+ credits per run.

---

## Quality Bar

The note content must match the depth of a full company profile — not a paragraph summary:

- All 13 sections present and populated
- Technology stack broken into labelled categories
- Services/products listed individually as bullets
- Key insights backed by specific numbers (years, client count, etc.)
- Target customer profile as distinct bullet points
- Data sources listed as URLs (including any GooseWorks tools called)

**If the note you are about to write is shorter than ~40 lines, you have not done enough research. Go back to Step 2 and search more sources before writing.**

---

## Error Handling

All errors return structured JSON `{"error": "...", "code": "..."}`. Never surface raw tracebacks to the user.

Common codes:
- `BIGIN_NOT_FOUND` — company not in Bigin, will create
- `FIRECRAWL_FAILED` — scrape failed, skip and log
- `BIGIN_WRITE_FAILED` — CRM update failed, retry once (max retries: `config.research.maxRetries`)
- `GOOSEWORKS_NOT_LOGGED_IN` — run `npx gooseworks login`
- `GOOSEWORKS_INSUFFICIENT_CREDITS` — check balance with `npx gooseworks credits`

---

## Cron Usage

Run as an isolated session cron for batch enrichment:

```json
{
  "name": "BiginResearch",
  "schedule": { "kind": "every", "everyMs": 86400000 },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "Run bigin-scanner.py for all accounts with missing website or employee count"
  }
}
```

## Token Efficiency

- Firecrawl remains the primary research engine (no GooseWorks credits)
- GooseWorks `brand-dev` call (~1–2 credits) fills brand/industry/description gaps efficiently
- GooseWorks `fiber` call (~2–5 credits, pageSize: 1) fills employee/HQ gaps when needed
- Neither call triggers Apify actors, so cost stays low and predictable
- All Bigin field reads use `getRecords` with `fields` param — never fetch full records
