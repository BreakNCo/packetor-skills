---
name: bigin-company-research
description: This skill should be used when the user asks to research a company and update Zoho Bigin CRM, enrich existing Bigin contacts/accounts with latest company information, gather company details before creating new Bigin records, or verify/update company information (website, technologies, employee count, funding, etc.). Trigger phrases include "research [company] in Bigin", "update [company] details in Bigin", "/research [company]", or "enrich [company] account".
version: 1.1.0
compatibility: openclaw
tools:
  - ZohoMCP
  - firecrawl
---

# Bigin Company Research

Research companies using Firecrawl web search and automatically create or update their records in Zoho Bigin CRM. **The output must always be a detailed, structured note — never a brief summary.** See the mandatory note format in Step 4.

## When to Use

- User asks to research a company and update Bigin
- Need to enrich existing Bigin accounts with latest company info
- Want to gather company details before creating a new Bigin record
- Need to verify or update company data (website, employee count, funding, tech stack, etc.)

## When NOT to Use

- Simple Bigin lookups — use ZohoMCP tools directly
- Company research without Bigin updates — use Firecrawl only
- Bulk operations on many companies — use the batch script (`scripts/bigin-scanner.py`)
- Real-time financial data requiring authenticated feeds

## Prerequisites

**MCP Servers required:**
- `ZohoMCP` — Bigin CRM read/write
- `firecrawl` — Web scraping and search

---

## Workflow

### Step 1 — Lookup in Bigin

```
mcp__ZohoMCP__Bigin_searchRecords(module_api_name: "Accounts", word: "<company_name>")
```

- If found: note the account ID and existing website/data
- If not found: proceed with research, then create a new record

---

### Step 2 — Deep Multi-Source Research (mandatory)

Do **not** stop after one source. Gather data from **all available sources** before writing anything. Use `config/bigin-config.json` `firecrawl.searchLimit` (default 3) per search.

#### 2a. Company website (primary source)
```
mcp__firecrawl__firecrawl_scrape(url: "<website>", formats: ["markdown"])
```
If website URL is unknown, discover it first:
```
mcp__firecrawl__firecrawl_search(query: "<company_name> official website", limit: 3)
```

#### 2b. LinkedIn
```
mcp__firecrawl__firecrawl_search(query: "<company_name> LinkedIn company page", limit: 3)
```
Scrape the LinkedIn page if accessible:
```
mcp__firecrawl__firecrawl_scrape(url: "<linkedin_url>", formats: ["markdown"])
```

#### 2c. Tech stack discovery
```
mcp__firecrawl__firecrawl_search(query: "<company_name> technology stack built with", limit: 3)
```
Also scrape BuiltWith or similar tech profiler pages if found in results.

#### 2d. News, funding, and background
```
mcp__firecrawl__firecrawl_search(query: "<company_name> funding news founded history", limit: 5)
```

#### 2e. Review / profile sites
Search Crunchbase, G2, Clutch, GlassDoor, or AngelList as relevant:
```
mcp__firecrawl__firecrawl_search(query: "<company_name> Crunchbase OR Clutch OR G2 profile", limit: 3)
```

Synthesise all findings before moving to Step 3.

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

```
mcp__ZohoMCP__Bigin_addNotesToSpecificRecord(
  module_api_name: "Accounts",
  id: "<account_id>",
  data: [{
    "Note_Title": "Company Research - <YYYY-MM-DD>",
    "Note_Content": "<full structured note — see template below>"
  }]
)
```

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

### Research Date
<YYYY-MM-DD>

### Data Sources
<List every URL used as a source.>
```

---

## Field Mapping

See `references/field-mapping.md` for the full scraped-key → Bigin API field mapping. Summary:

| Bigin Field | Maps To |
|---|---|
| `Account_Name` | Company legal name |
| `Website` | Primary domain |
| `Description` | About/mission text (2–4 sentences) |
| `Industry` | Sector (e.g. "Information Technology") |
| `Employees` | Headcount (integer) |
| `Phone` | Main contact number |
| `Twitter` | Twitter/X URL |
| `Billing_City` | HQ city |
| `Billing_State` | HQ state/region |
| `Billing_Country` | HQ country |
| `Company_Linkedin_Url` | LinkedIn company page URL |
| `Technologies` | Comma-separated tech stack |
| `Founded_Year` | 4-digit year |
| `Funding_Info` | e.g. "Series B, $20M (2024)" |
| `ISO_Certifications` | e.g. "ISO 27001, SOC 2" |

---

## Quality Bar

The note content must match the depth of a full company profile — not a paragraph summary:

- All 13 sections present and populated
- Technology stack broken into labelled categories
- Services/products listed individually as bullets
- Key insights backed by specific numbers (years, client count, etc.)
- Target customer profile as distinct bullet points
- Data sources listed as URLs

**If the note you are about to write is shorter than ~40 lines, you have not done enough research. Go back to Step 2 and search more sources before writing.**

---

## Error Handling

All errors return structured JSON `{"error": "...", "code": "..."}`. Never surface raw tracebacks to the user.

Common codes:
- `BIGIN_NOT_FOUND` — company not in Bigin, will create
- `FIRECRAWL_FAILED` — scrape failed, skip and log
- `BIGIN_WRITE_FAILED` — CRM update failed, retry once (max retries: `config.research.maxRetries`)

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

- Script returns `HEARTBEAT_OK` when no accounts need enrichment
- All Bigin field reads use `getRecords` with `fields` param — never fetch full records
- Firecrawl searches limited to 3 results per company (configurable in `config/bigin-config.json`)
