---
name: bigin-research
description: Research companies using web search and automatically enrich or create their Account records in Zoho Bigin CRM. Use this skill when asked to research a company, enrich CRM data, or bulk-update missing fields like website, employee count, industry, or tech stack.
version: 1.0.0
compatibility: openclaw
tools:
  - ZohoMCP
  - firecrawl
---

# Bigin Company Research

Research companies using Firecrawl web search and automatically create or update their records in Zoho Bigin CRM (Accounts module).

## When to Use

- User asks to research a company and update Bigin
- Need to enrich existing Bigin accounts with latest company info
- Want to gather company details before creating a new Bigin record
- Need to verify or update company data (website, employee count, funding, tech stack, etc.)

## When NOT to Use

- Simple Bigin lookups — use ZohoMCP tools directly
- Company research without Bigin updates — use Firecrawl only
- Bulk operations on many companies — use the batch script (`bigin-batch-research.py`)
- Real-time financial data requiring authenticated feeds

## Prerequisites

**MCP Servers required:**
- `ZohoMCP` — Bigin CRM read/write
- `firecrawl` — Web scraping and search

**Environment:**
- Zoho OAuth credentials configured in ZohoMCP server
- `FIRECRAWL_API_KEY` set in environment

## Workflow

The agent executes these steps via `bigin-scanner.py`. The script outputs structured JSON; the agent sends notifications only on meaningful events.

### 1. Lookup in Bigin
Search the Accounts module for an existing record. If found, use its `id` for updates. If not found, prepare to create.

### 2. Research Online
Use Firecrawl to scrape the company website or search for company details. See `references/field-mapping.md` for how scraped fields map to Bigin fields.

### 3. Upsert Record
- **Existing record:** call `updateSpecificRecord` with enriched fields
- **New record:** call `addRecords` to create
- Add a research note via `addNotesToSpecificRecord` with sources and timestamp

### 4. Output
Script returns JSON with `status`, `bigin_record_id`, `fields_updated`, and `note_added`. Agent surfaces a summary to the user.

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
- Firecrawl searches limited to 3 results per company

## Error Handling

All errors return structured JSON `{"error": "...", "code": "..."}`. Never surface raw tracebacks to the user.

Common codes:
- `BIGIN_NOT_FOUND` — company not in Bigin, will create
- `FIRECRAWL_FAILED` — scrape failed, skip and log
- `BIGIN_WRITE_FAILED` — CRM update failed, retry once
