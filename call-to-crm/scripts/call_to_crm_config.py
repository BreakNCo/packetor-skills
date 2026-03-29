"""
Call-to-CRM skill — shared config, MCP helpers, and utilities.
"""

import json
import os
import subprocess
import time
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config" / "call-to-crm-config.json"
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/data/workspace"))
STATE_DIR = WORKSPACE / "skills" / "call-to-crm" / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def get_openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise EnvironmentError("OPENAI_API_KEY is not set")
    return key


# ---------------------------------------------------------------------------
# mcporter — ZohoMCP calls
# ---------------------------------------------------------------------------

def mcporter_call(server: str, tool: str, retries: int = 2, timeout: int = 25, **params) -> dict | None:
    """Call an MCP tool via mcporter CLI."""
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


# ---------------------------------------------------------------------------
# Bigin helpers
# ---------------------------------------------------------------------------

def find_account(name: str, config: dict) -> dict | None:
    result = mcporter_call(
        "ZohoMCP", "Bigin_searchRecords",
        module_api_name=config["bigin"]["accountModule"],
        word=name,
    )
    if not result:
        return None
    records = result.get("data", [])
    return records[0] if records else None


def find_open_deal(account_id: str, config: dict) -> dict | None:
    """Find the most recent open deal for an account."""
    open_stages = config["bigin"]["openDealStages"]
    result = mcporter_call(
        "ZohoMCP", "Bigin_getRecords",
        module_api_name=config["bigin"]["dealModule"],
        fields="id,Deal_Name,Stage,Account_Name,Owner",
        per_page=10,
    )
    if not result:
        return None
    deals = result.get("data", [])
    for deal in deals:
        acct = deal.get("Account_Name", {})
        acct_id = acct.get("id") if isinstance(acct, dict) else None
        if acct_id == account_id and deal.get("Stage") in open_stages:
            return deal
    return None


def update_deal_stage(deal_id: str, stage: str, config: dict) -> bool:
    result = mcporter_call(
        "ZohoMCP", "Bigin_updateSpecificRecord",
        module_api_name=config["bigin"]["dealModule"],
        record_id=deal_id,
        data={"Stage": stage},
    )
    return result is not None


def add_note_to_record(module: str, record_id: str, title: str, content: str, config: dict) -> bool:
    result = mcporter_call(
        "ZohoMCP", "Bigin_addNotesToSpecificRecord",
        module_api_name=module,
        record_id=record_id,
        Note_Title=title,
        Note_Content=content,
    )
    return result is not None


def create_task(record_id: str, subject: str, due_date: str, owner: str | None, config: dict) -> str | None:
    data = {
        "Subject": subject,
        "Status": config["bigin"]["defaultTaskStatus"],
        "Priority": config["bigin"]["defaultTaskPriority"],
        "Due_Date": due_date,
        "What_Id": {"id": record_id},
    }
    if owner:
        data["Owner"] = {"email": owner}
    result = mcporter_call(
        "ZohoMCP", "Bigin_addRecords",
        module_api_name=config["bigin"]["taskModule"],
        data=[data],
    )
    if not result:
        return None
    created = result.get("data", [{}])
    return created[0].get("details", {}).get("id") if created else None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def due_date_str(days_from_now: int) -> str:
    return (date.today() + timedelta(days=days_from_now)).isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def out(data: dict) -> None:
    print(json.dumps(data, indent=2))
