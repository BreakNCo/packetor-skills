#!/usr/bin/env python3
"""
Bigin Company Research Scanner v1.0.0

Researches a company online (via Firecrawl) and creates or updates
its record in Zoho Bigin CRM.

Usage:
    python3 bigin-scanner.py --company "Acme Corp"
    python3 bigin-scanner.py --company "Acme Corp" --website "https://acme.com"
    python3 bigin-scanner.py --batch          # enrich accounts with missing fields
    python3 bigin-scanner.py --record-id "<bigin_id>"  # enrich specific record

Output: JSON to stdout
Logs:   stderr only
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from bigin_config import (
    load_config,
    load_state,
    save_state,
    search_bigin_account,
    update_bigin_account,
    create_bigin_account,
    add_research_note,
    scrape_company_website,
    search_company_online,
    mcporter_call,
    now_iso,
    out,
    SKILL_DIR,
)


# ---------------------------------------------------------------------------
# Field mapping: scraped keys → Bigin API field names
# ---------------------------------------------------------------------------

FIELD_MAP = {
    "company_name":        "Account_Name",
    "description":         "Description",
    "industry":            "Industry",
    "employee_count":      "Employees",
    "phone":               "Phone",
    "twitter_url":         "Twitter",
    "headquarters_city":   "Billing_City",
    "headquarters_state":  "Billing_State",
    "headquarters_country":"Billing_Country",
    "linkedin_url":        "Company_Linkedin_Url",
    "technologies":        "Technologies",
    "founded_year":        "Founded_Year",
    "funding":             "Funding_Info",
    "iso_certifications":  "ISO_Certifications",
}


# ---------------------------------------------------------------------------
# Core research logic
# ---------------------------------------------------------------------------

def research_company(company_name: str, website: str | None, config: dict) -> dict:
    """
    Research a company online. Returns a dict of scraped fields.
    Tries website scrape first; falls back to web search.
    """
    scraped = {}

    if website:
        print(f"[INFO] Scraping {website}", file=sys.stderr)
        result = scrape_company_website(website, config)
        if result and isinstance(result, dict):
            # Firecrawl extract returns data under "extract" key
            scraped = result.get("extract", result)

    if not scraped:
        print(f"[INFO] Web search for {company_name!r}", file=sys.stderr)
        result = search_company_online(company_name, config)
        if result and isinstance(result, list):
            combined = "\n\n".join(
                r.get("markdown", r.get("content", ""))
                for r in result[:3]
                if isinstance(r, dict)
            )
            scraped = {"_raw_search": combined[:4000]}
        elif result and isinstance(result, dict):
            scraped = result.get("data", result)

    return scraped


def map_to_bigin_fields(scraped: dict, existing: dict | None, config: dict) -> dict:
    """
    Map scraped data to Bigin field names, respecting skipFieldsIfPopulated.
    """
    skip = set(config.get("research", {}).get("skipFieldsIfPopulated", []))
    always_overwrite = config.get("research", {}).get("alwaysOverwrite", False)
    fields = {}

    for scraped_key, bigin_key in FIELD_MAP.items():
        value = scraped.get(scraped_key)
        if not value:
            continue
        # Skip if field is already populated and alwaysOverwrite is False
        if (
            not always_overwrite
            and bigin_key in skip
            and existing
            and existing.get(bigin_key)
        ):
            continue
        fields[bigin_key] = value

    return fields


def build_note(company_name: str, fields: dict, website: str | None, config: dict) -> str:
    tag = config.get("research", {}).get("noteSourceTag", "[Auto-Research]")
    lines = [
        f"{tag} Research update — {now_iso()}",
        f"Company: {company_name}",
    ]
    if website:
        lines.append(f"Source: {website}")
    lines.append("")
    lines.append("Fields updated:")
    for k, v in fields.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Single company flow
# ---------------------------------------------------------------------------

def process_company(company_name: str, website: str | None, record_id: str | None, config: dict) -> dict:
    state = load_state()

    # 1. Find existing Bigin record
    existing = None
    if record_id:
        result = mcporter_call(
            "ZohoMCP", "Bigin_getSpecificRecord",
            module_api_name=config["bigin"]["module"],
            record_id=record_id,
        )
        if result:
            existing = result.get("data", [None])[0]
    else:
        existing = search_bigin_account(company_name, config)
        if existing:
            record_id = existing.get("id")

    # Use website from existing record if not provided
    if not website and existing:
        website = existing.get("Website")

    # 2. Research online
    scraped = research_company(company_name, website, config)
    if not scraped:
        return {
            "status": "skipped",
            "reason": "no_data_found",
            "company": company_name,
        }

    # 3. Map fields
    fields = map_to_bigin_fields(scraped, existing, config)
    if website and "Website" not in fields:
        fields["Website"] = website

    if not fields:
        return {
            "status": "skipped",
            "reason": "no_new_fields",
            "company": company_name,
        }

    # 4. Upsert
    if record_id:
        result = update_bigin_account(record_id, fields, config)
        action = "updated"
    else:
        fields["Account_Name"] = fields.get("Account_Name", company_name)
        result = create_bigin_account(fields, config)
        action = "created"
        if result:
            created_data = result.get("data", [{}])
            record_id = created_data[0].get("details", {}).get("id") if created_data else None

    if not result:
        return {
            "status": "error",
            "code": "BIGIN_WRITE_FAILED",
            "company": company_name,
        }

    # 5. Add note
    note_added = False
    if config.get("research", {}).get("addNoteOnUpdate", True) and record_id:
        note_content = build_note(company_name, fields, website, config)
        note_result = add_research_note(record_id, note_content, config)
        note_added = note_result is not None

    # 6. Update state
    if action == "updated":
        state["totalUpdated"] = state.get("totalUpdated", 0) + 1
    else:
        state["totalCreated"] = state.get("totalCreated", 0) + 1
    state["lastRunAt"] = now_iso()
    save_state(state)

    return {
        "status": "ok",
        "action": action,
        "company": company_name,
        "bigin_record_id": record_id,
        "fields_updated": list(fields.keys()),
        "note_added": note_added,
    }


# ---------------------------------------------------------------------------
# Batch flow
# ---------------------------------------------------------------------------

def process_batch(config: dict) -> dict:
    batch_cfg = config.get("batch", {})
    max_per_run = batch_cfg.get("maxPerRun", 20)
    missing_triggers = batch_cfg.get("missingFieldsTrigger", ["Website", "Employees"])

    # Fetch accounts
    result = mcporter_call(
        "ZohoMCP", "Bigin_getRecords",
        module_api_name=config["bigin"]["module"],
        fields=",".join(["id", "Account_Name", "Website"] + missing_triggers),
        per_page=max_per_run,
    )
    if not result:
        return {"status": "error", "code": "BIGIN_FETCH_FAILED"}

    records = result.get("data", []) if isinstance(result, dict) else []

    # Filter to accounts missing at least one trigger field
    needs_research = [
        r for r in records
        if any(not r.get(f) for f in missing_triggers)
    ]

    if not needs_research:
        if batch_cfg.get("heartbeatIfNoneNeeded", True):
            return {"status": "heartbeat", "message": "HEARTBEAT_OK", "checked": len(records)}
        return {"status": "ok", "processed": 0, "message": "nothing to enrich"}

    results = []
    for record in needs_research[:max_per_run]:
        name = record.get("Account_Name", "")
        website = record.get("Website")
        rid = record.get("id")
        if not name:
            continue
        print(f"[BATCH] Processing {name!r}", file=sys.stderr)
        res = process_company(name, website, rid, config)
        results.append(res)

    return {
        "status": "ok",
        "processed": len(results),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Bigin Company Research Scanner")
    parser.add_argument("--company", help="Company name to research")
    parser.add_argument("--website", help="Company website URL")
    parser.add_argument("--record-id", help="Specific Bigin record ID to enrich")
    parser.add_argument("--batch", action="store_true", help="Batch enrich accounts with missing fields")
    args = parser.parse_args()

    config = load_config()

    if args.batch:
        result = process_batch(config)
    elif args.company:
        result = process_company(args.company, args.website, args.record_id, config)
    else:
        parser.print_help()
        sys.exit(1)

    out(result)


if __name__ == "__main__":
    main()
