#!/usr/bin/env python3
"""Build a deterministic outbound email send plan for the marketing-email-send skill.

This script does not call Bigin or Notion directly. It standardizes the decision logic so the
agent can gather data, pass it in, and get back a structured plan for template family,
attachment key, and personalization hints.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict


@dataclass
class Input:
    company_country: str | None = None
    certification_known: bool = False
    certified: bool = False
    market_segment: str | None = None
    has_inhouse_team: bool = False
    summary: str | None = None
    recipient_name: str | None = None
    company_name: str | None = None
    test_mode: bool = False


@dataclass
class Plan:
    template_group: str
    template_family: str
    attachment_filename: str
    suggested_subject: str
    customization_hint: str


def normalize_segment(value: str | None) -> str:
    if not value:
        return "unknown"
    v = value.strip().lower()
    if v in {"enterprise", "mid-market", "mid market", "midmarket", "smb", "startup"}:
        return v.replace(" ", "-")
    return v


def build_plan(inp: Input) -> Plan:
    country = (inp.company_country or "").strip().lower()
    india = country in {"india", "in"}
    segment = normalize_segment(inp.market_segment)

    if inp.certification_known:
        certified = inp.certified
    else:
        certified = False

    inhouse_ok = certified and inp.has_inhouse_team and segment in {"enterprise", "mid-market", "midmarket"}

    if india:
        group = "simplified"
    else:
        group = "standard"

    if inhouse_ok:
        family = "inhouse-team"
        attachment = "Customers_with_inhouse_team.pdf"
        subject = "For companies with an in-house team"
    elif certified:
        family = "already-certified"
        attachment = "Customers_already_certified.pdf"
        subject = "Keeping governance running after certification"
    else:
        family = "new-to-certification"
        attachment = "Customers_new_to_certification.pdf"
        subject = "3 questions to answer before you start ISO 27001"

    if inp.test_mode:
        subject = f"Test: {subject}"

    hint_parts = []
    if inp.recipient_name:
        hint_parts.append(f"Use recipient name: {inp.recipient_name}.")
    if inp.company_name:
        hint_parts.append(f"Use company name: {inp.company_name}.")
    if inp.summary:
        hint_parts.append("Customize lightly using the CRM summary, prioritizing the latest note context.")
    else:
        hint_parts.append("No CRM summary available; keep customization factual and light.")

    return Plan(
        template_group=group,
        template_family=family,
        attachment_filename=attachment,
        suggested_subject=subject,
        customization_hint=" ".join(hint_parts),
    )


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("Provide JSON on stdin.", file=sys.stderr)
        return 2
    data = json.loads(raw)
    inp = Input(**data)
    plan = build_plan(inp)
    print(json.dumps(asdict(plan), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
