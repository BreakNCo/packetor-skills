#!/usr/bin/env python3
"""Suggest slug, category, title, and outline for a Packets blog draft.

Stdin JSON: {keyword, notes?, categoryHint?}
Stdout JSON: {suggestedSlug, suggestedCategory, suggestedTitle, searchIntent, outline[], primaryKeyword, secondaryKeywords[]}
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_ROOT / "config" / "blog-content-config.json"
FALLBACK_CATEGORY = "soc-2-for-ai-companies"


@dataclass
class Input:
    keyword: str
    notes: str | None = None
    categoryHint: str | None = None


@dataclass
class Plan:
    suggestedSlug: str
    suggestedCategory: str
    suggestedTitle: str
    searchIntent: str
    outline: list[str]
    primaryKeyword: str
    secondaryKeywords: list[str] = field(default_factory=list)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def title_case_keyword(keyword: str) -> str:
    small = {"for", "and", "or", "to", "of", "in", "on", "a", "an", "the"}
    words = keyword.strip().split()
    out: list[str] = []
    for i, word in enumerate(words):
        if word.upper() in {"SOC", "ISO", "AI", "EU", "DPDP", "RBI"}:
            out.append(word.upper())
        elif i > 0 and word.lower() in small:
            out.append(word.lower())
        else:
            out.append(word[:1].upper() + word[1:])
    return " ".join(out)


def suggest_category(keyword: str, notes: str, hint: str | None, mapping: dict[str, list[str]]) -> str:
    if hint and hint in mapping:
        return hint
    haystack = f"{keyword} {notes} {hint or ''}".lower()
    best: tuple[int, str] | None = None
    for slug, needles in mapping.items():
        hits = sum(1 for needle in needles if needle.lower() in haystack)
        if hits and (best is None or hits > best[0]):
            best = (hits, slug)
    return best[1] if best else FALLBACK_CATEGORY


def search_intent(keyword: str, notes: str) -> str:
    hay = f"{keyword} {notes}".lower()
    if any(token in hay for token in (" vs ", "versus", "compare", "alternative")):
        return "commercial-comparison"
    if any(token in hay for token in ("how to", "checklist", "what is", "guide")):
        return "informational"
    return "informational"


def default_outline(keyword: str, intent: str) -> list[str]:
    if intent == "commercial-comparison":
        return [
            f"What {keyword} actually requires",
            "Where a tool-only approach stalls",
            "How Packets runs the work end to end",
            "Packets vs Scrut for this job",
            "Frequently asked questions",
        ]
    return [
        f"What {keyword} means for AI-native SaaS",
        "The questionnaire moment that stalls the deal",
        "What to put in place first",
        "How Packets implements this without a hire",
        "Frequently asked questions",
    ]


def secondary_keywords(keyword: str, notes: str) -> list[str]:
    extras: list[str] = []
    hay = f"{keyword} {notes}".lower()
    candidates = [
        "ISO 42001",
        "EU AI Act",
        "security questionnaire",
        "audit ready",
        "compliance automation",
        "SOC 2 Type II",
        "ISO 27001",
        "DPDP",
    ]
    for item in candidates:
        if item.lower() in hay and item.lower() != keyword.lower():
            extras.append(item)
    return extras[:4]


def build_plan(inp: Input, config: dict) -> Plan:
    keyword = inp.keyword.strip()
    notes = (inp.notes or "").strip()
    mapping = config.get("categoryKeywordMap") or {}
    category = suggest_category(keyword, notes, inp.categoryHint, mapping)
    intent = search_intent(keyword, notes)
    title = title_case_keyword(keyword)
    return Plan(
        suggestedSlug=slugify(keyword),
        suggestedCategory=category,
        suggestedTitle=title,
        searchIntent=intent,
        outline=default_outline(keyword, intent),
        primaryKeyword=keyword,
        secondaryKeywords=secondary_keywords(keyword, notes),
    )


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("Provide JSON on stdin.", file=sys.stderr)
        return 2
    data = json.loads(raw)
    if not str(data.get("keyword", "")).strip():
        print(json.dumps({"error": "keyword is required"}))
        return 2
    inp = Input(
        keyword=str(data["keyword"]),
        notes=data.get("notes"),
        categoryHint=data.get("categoryHint"),
    )
    plan = build_plan(inp, load_config())
    print(json.dumps(asdict(plan), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
