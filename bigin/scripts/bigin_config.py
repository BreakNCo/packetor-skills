"""
Bigin skill — shared config, state, and MCP helpers.
"""

import json
import os
import sys
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Workspace paths
# ---------------------------------------------------------------------------

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE_DIR", Path.home() / ".openclaw" / "workspace"))
SKILL_DIR = WORKSPACE / "skills" / "bigin"
CONFIG_PATH = SKILL_DIR / "config" / "bigin-config.json"
STATE_PATH = SKILL_DIR / "state" / "bigin-state.json"

SKILL_DIR.mkdir(parents=True, exist_ok=True)
(SKILL_DIR / "state").mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Atomic file I/O
# ---------------------------------------------------------------------------

def atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically using a temp file + os.replace to prevent corruption."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False, suffix=".tmp"
    ) as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    os.replace(tmp_path, path)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load bigin-config.json. Falls back to defaults if missing."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "bigin": {"module": "Accounts"},
        "firecrawl": {"searchLimit": 3},
        "research": {"maxRetries": 2, "retryDelaySeconds": 3, "addNoteOnUpdate": True},
        "batch": {"maxPerRun": 20, "heartbeatIfNoneNeeded": True},
    }


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def load_state() -> dict:
    """Load persistent state. Returns empty dict if not found."""
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {
        "version": "1.0.0",
        "lastRunAt": None,
        "processedToday": 0,
        "totalUpdated": 0,
        "totalCreated": 0,
        "lastErrors": [],
    }


def save_state(state: dict) -> None:
    state["updatedAt"] = now_iso()
    atomic_write(STATE_PATH, state)


# ---------------------------------------------------------------------------
# MCP caller
# ---------------------------------------------------------------------------

def mcporter_call(tool_name: str, arguments: dict, retries: int = 2, timeout: int = 30) -> dict:
    """
    Call an MCP tool via the openclaw mcporter subprocess.
    Returns {"success": True, "data": ...} or {"success": False, "error": "..."}.
    """
    payload = json.dumps({"tool": tool_name, "arguments": arguments})

    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                ["openclaw", "mcporter", "call"],
                input=payload,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "non-zero exit")

            response = json.loads(result.stdout)

            # Strip envelope: {content: [{type: "text", text: "..."}]}
            if "content" in response:
                for item in response["content"]:
                    if item.get("type") == "text":
                        try:
                            return {"success": True, "data": json.loads(item["text"])}
                        except json.JSONDecodeError:
                            return {"success": True, "data": item["text"]}

            return {"success": True, "data": response}

        except Exception as e:
            if attempt < retries:
                time.sleep(3)
                continue
            return {"success": False, "error": str(e), "tool": tool_name}

    return {"success": False, "error": "max retries exceeded", "tool": tool_name}


# ---------------------------------------------------------------------------
# Bigin helpers
# ---------------------------------------------------------------------------

def search_bigin_account(company_name: str, config: dict) -> dict | None:
    """Search Bigin Accounts by name. Returns first match or None."""
    result = mcporter_call(
        "mcp__ZohoMCP__Bigin_searchRecords",
        {
            "module_api_name": config["bigin"]["module"],
            "word": company_name,
        },
    )
    if not result["success"]:
        return None
    data = result["data"]
    records = data.get("data", []) if isinstance(data, dict) else []
    return records[0] if records else None


def update_bigin_account(record_id: str, fields: dict, config: dict) -> dict:
    """Update a specific Bigin account record."""
    return mcporter_call(
        "mcp__ZohoMCP__Bigin_updateSpecificRecord",
        {
            "module_api_name": config["bigin"]["module"],
            "record_id": record_id,
            "data": fields,
        },
    )


def create_bigin_account(fields: dict, config: dict) -> dict:
    """Create a new Bigin account record."""
    return mcporter_call(
        "mcp__ZohoMCP__Bigin_addRecords",
        {
            "module_api_name": config["bigin"]["module"],
            "data": [fields],
        },
    )


def add_research_note(record_id: str, content: str, config: dict) -> dict:
    """Add a research note to a Bigin record."""
    return mcporter_call(
        "mcp__ZohoMCP__Bigin_addNotesToSpecificRecord",
        {
            "module_api_name": config["bigin"]["module"],
            "record_id": record_id,
            "Note_Title": config["bigin"].get("noteTitle", "Company Research Update"),
            "Note_Content": content,
        },
    )


# ---------------------------------------------------------------------------
# Firecrawl helpers
# ---------------------------------------------------------------------------

def scrape_company_website(url: str, config: dict) -> dict:
    """Scrape a company website and extract structured data."""
    return mcporter_call(
        "mcp__firecrawl__firecrawl_scrape",
        {
            "url": url,
            "formats": config["firecrawl"].get("scrapeFormats", ["markdown"]),
            "extract": config["firecrawl"].get("extractFields", {}),
        },
    )


def search_company_online(company_name: str, config: dict) -> dict:
    """Search for company info when no website is known."""
    return mcporter_call(
        "mcp__firecrawl__firecrawl_search",
        {
            "query": f"{company_name} company overview employees industry headquarters",
            "limit": config["firecrawl"].get("searchLimit", 3),
        },
    )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def out(data: dict) -> None:
    """Print structured JSON output to stdout."""
    print(json.dumps(data, indent=2))
