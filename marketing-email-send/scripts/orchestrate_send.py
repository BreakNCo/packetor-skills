#!/usr/bin/env python3
"""Scaffold for end-to-end CRM-aware marketing email orchestration.

This script standardizes the workflow shape and IO contract. It leaves provider-specific
fetch/write/send steps to the calling agent, but its output now assumes two body modes:
- notes present -> customize the Notion template lightly
- notes absent -> use the original Notion template body with normal placeholder filling only
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict


@dataclass
class Input:
    contact_id: str
    account_id: str | None = None
    pipeline_record_id: str | None = None
    recipient_name: str | None = None
    recipient_email: str | None = None
    company_name: str | None = None
    company_country: str | None = None
    certification_known: bool = False
    certified: bool = False
    market_segment: str | None = None
    has_inhouse_team: bool = False
    account_notes: list[dict] | None = None
    pipeline_notes: list[dict] | None = None
    notion_templates: dict | None = None
    uploaded_bigin_files: dict | None = None
    test_mode: bool = False


@dataclass
class Output:
    merged_notes_latest_first: list[dict]
    summary: str
    template_group: str
    template_family: str
    attachment_filename: str
    attachment_id: str | None
    suggested_subject: str
    draft_body_guidance: str
    next_actions: list[str]


def latest_first(notes: list[dict]) -> list[dict]:
    def key(n: dict):
        return n.get("time") or n.get("created_time") or n.get("modified_time") or ""
    return sorted(notes, key=key, reverse=True)


def summarize(notes: list[dict]) -> str:
    if not notes:
        return "No CRM notes found on the account or pipeline record."
    lines = []
    for n in notes[:8]:
        text = (n.get("text") or n.get("content") or n.get("note") or "").strip().replace("\n", " ")
        t = n.get("time") or n.get("created_time") or "unknown-time"
        if text:
            lines.append(f"[{t}] {text}")
    return "Latest CRM context: " + " | ".join(lines) if lines else "No usable CRM note text found."


def decide_family(inp: Input):
    country = (inp.company_country or "").strip().lower()
    india = country in {"india", "in"}
    certified = inp.certified if inp.certification_known else False
    segment = (inp.market_segment or "").strip().lower().replace(" ", "-")
    inhouse_ok = certified and inp.has_inhouse_team and segment in {"enterprise", "mid-market", "midmarket"}

    if inhouse_ok:
        return ("simplified" if india else "standard", "inhouse-team", "Customers_with_inhouse_team.pdf", "For companies with an in-house team")
    if certified:
        return ("simplified" if india else "standard", "already-certified", "Customers_already_certified.pdf", "Keeping governance running after certification")
    return ("simplified" if india else "standard", "new-to-certification", "Customers_new_to_certification.pdf", "3 questions to answer before you start ISO 27001")


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("Provide JSON on stdin.", file=sys.stderr)
        return 2
    inp = Input(**json.loads(raw))
    merged = latest_first((inp.account_notes or []) + (inp.pipeline_notes or []))
    summary = summarize(merged)
    group, family, attachment_filename, subject = decide_family(inp)
    if inp.test_mode:
        subject = f"Test: {subject}"
    attachment_id = None
    if inp.uploaded_bigin_files:
        attachment_id = inp.uploaded_bigin_files.get(attachment_filename)
    out = Output(
        merged_notes_latest_first=merged,
        summary=summary,
        template_group=group,
        template_family=family,
        attachment_filename=attachment_filename,
        attachment_id=attachment_id,
        suggested_subject=subject,
        draft_body_guidance=(
            f"Use recipient={inp.recipient_name or 'unknown'}, company={inp.company_name or 'unknown'}. "
            + (
                "Customize lightly using the CRM summary."
                if merged else
                "No notes found: use the original Notion template content with only normal placeholder filling."
            )
        ),
        next_actions=[
            "Write the summary back to the pipeline record as a new note.",
            "Read the exact template text from Notion for the chosen family.",
            "Customize the template with recipient/company facts and summary context.",
            "Build the Bigin sendEmails payload.",
            "Send the email if attachment_id is available; otherwise resolve/re-upload the attachment first.",
        ],
    )
    print(json.dumps(asdict(out), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
