"""
Bigin Ops skill — shared MCP helpers and utilities.
Mirrors the pattern from bigin-research/scripts/bigin_config.py.
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/data/workspace"))
SKILL_DIR = WORKSPACE / "skills" / "bigin-ops"
STATE_DIR = SKILL_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def mcporter_call(server: str, tool: str, retries: int = 2, timeout: int = 25, **params) -> dict | None:
    """
    Call an MCP tool via mcporter CLI.

    Usage:
        mcporter_call("ZohoMCP", "Bigin_searchRecords", module_api_name="Accounts", word="Acme")
    """
    args = json.dumps(params) if params else "{}"
    cmd = ["mcporter", "call", server, tool, "--args", args]

    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if r.returncode != 0:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None

            raw = json.loads(r.stdout)

            # Strip MCP content envelope: {content: [{type: "text", text: "..."}]}
            if isinstance(raw, dict) and "content" in raw:
                content = raw["content"]
                if isinstance(content, list) and content:
                    first = content[0]
                    if isinstance(first, dict) and "text" in first:
                        try:
                            return json.loads(first["text"])
                        except (json.JSONDecodeError, TypeError):
                            pass
            return raw

        except subprocess.TimeoutExpired:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None
        except Exception:
            return None

    return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def out(data: dict) -> None:
    """Print structured JSON output to stdout."""
    print(json.dumps(data, indent=2))
