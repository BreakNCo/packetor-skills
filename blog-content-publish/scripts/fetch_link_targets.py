#!/usr/bin/env python3
"""Rank internal-link and CTA targets for a Packets blog draft.

Stdin JSON: {primaryKeyword, category, excludeSlug?}
Stdout JSON: {ctaTargets[], recommendedInternal[], recommendedArticles[]}

Shells out to vendored `cms-tools` `bun run cms:link-targets`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cms_env import cms_tools_dir, cms_tools_installed, extract_json, missing_cms_env_hint, subprocess_env

SCRUT_PATH = "/compare/packets-vs-scrut"


def tokenize(value: str) -> list[str]:
    return [part for part in value.lower().replace("/", " ").replace("-", " ").split() if len(part) > 2]


def score_target(target: dict, keyword: str, category: str) -> int:
    hay = " ".join(
        [
            str(target.get("title") or ""),
            str(target.get("path") or ""),
            str(target.get("category") or ""),
        ]
    ).lower()
    tokens = tokenize(keyword) + tokenize(category)
    return sum(hay.count(token) for token in tokens)


def run_link_targets(site: Path) -> list[dict]:
    try:
        proc = subprocess.run(
            ["bun", "scripts/list-link-targets.ts"],
            cwd=str(site),
            capture_output=True,
            text=True,
            check=False,
            env=subprocess_env(),
        )
    except FileNotFoundError:
        print(
            json.dumps(
                {
                    "error": "BUN_NOT_FOUND",
                    "hint": "Install bun, then run `cd blog-content-publish/cms-tools && bun install`.",
                }
            )
        )
        raise SystemExit(1)

    stdout = proc.stdout.strip()
    if proc.returncode != 0:
        detail = stdout or proc.stderr.strip()
        print(
            json.dumps(
                {
                    "error": "LINK_TARGETS_FAILED",
                    "hint": missing_cms_env_hint(),
                    "detail": detail,
                }
            )
        )
        raise SystemExit(1)

    try:
        parsed = extract_json(stdout)
    except json.JSONDecodeError:
        print(
            json.dumps(
                {
                    "error": "LINK_TARGETS_INVALID",
                    "detail": stdout[:500] or proc.stderr.strip(),
                }
            )
        )
        raise SystemExit(1)
    if isinstance(parsed, dict) and parsed.get("ok") is False:
        print(json.dumps({"error": parsed.get("error"), "detail": parsed.get("detail")}))
        raise SystemExit(1)
    if not isinstance(parsed, list):
        print(json.dumps({"error": "LINK_TARGETS_INVALID", "detail": "Expected a JSON array"}))
        raise SystemExit(1)
    return parsed


def pick(items: list[dict], limit: int) -> list[dict]:
    return items[:limit]


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("Provide JSON on stdin.", file=sys.stderr)
        return 2
    data = json.loads(raw)
    keyword = str(data.get("primaryKeyword") or "").strip()
    category = str(data.get("category") or "").strip()
    exclude = str(data.get("excludeSlug") or "").strip()
    exclude_path = f"/blog/{exclude}" if exclude else ""

    site = cms_tools_dir()
    if not site.exists():
        print(
            json.dumps(
                {
                    "error": "CMS_TOOLS_MISSING",
                    "hint": f"Expected vendored CLI at {site}",
                }
            )
        )
        return 1
    if not cms_tools_installed():
        print(
            json.dumps(
                {
                    "error": "CMS_TOOLS_NOT_INSTALLED",
                    "hint": "Run `cd blog-content-publish/cms-tools && bun install` once.",
                }
            )
        )
        return 1

    targets = [t for t in run_link_targets(site) if t.get("path") != exclude_path]
    ranked = sorted(targets, key=lambda t: score_target(t, keyword, category), reverse=True)

    cta = [t for t in ranked if t.get("kind") == "cta"]
    if not cta:
        cta = [t for t in targets if t.get("kind") == "cta"]
    articles = [t for t in ranked if t.get("kind") == "article"]
    internal = [t for t in ranked if t.get("kind") in {"static", "ia-page"}]

    scrut = next((t for t in targets if t.get("path") == SCRUT_PATH), None)
    if scrut and scrut not in internal:
        internal.insert(0, scrut)
    elif scrut:
        internal = [scrut] + [t for t in internal if t.get("path") != SCRUT_PATH]

    print(
        json.dumps(
            {
                "ctaTargets": pick(cta, 3),
                "recommendedInternal": pick(internal, 8),
                "recommendedArticles": pick(articles, 6),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
