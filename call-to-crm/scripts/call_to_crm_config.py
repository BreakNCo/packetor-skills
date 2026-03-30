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
# mcporter — zoho-bigin calls
# ---------------------------------------------------------------------------

def mcporter_call(tool_name: str, retries: int = 2, timeout: int = 25, **params) -> dict | None:
    """Call an MCP tool via mcporter CLI using the configured zoho-bigin server."""
    args = json.dumps(params) if params else "{}"
    server_tool = f"zoho-bigin.{tool_name}"
    cmd = ["mcporter", "call", server_tool, "--args", args, "--output", "json"]

    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if r.returncode != 0:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None
            raw = json.loads(r.stdout)
            if isinstance(raw, dict) and raw.get("isError"):
                return None
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
        "Bigin_searchRecords",
        path_variables={"module_api_name": config["bigin"]["accountModule"]},
        query_params={"word": name},
    )
    if not result:
        return None
    records = result.get("data", [])
    return records[0] if records else None


def find_open_deal(account_id: str, config: dict) -> dict | None:
    """Find the most recent open deal for an account."""
    result = mcporter_call(
        "Bigin_searchRecords",
        path_variables={"module_api_name": config["bigin"]["dealModule"]},
        query_params={"word": account_id},
    )
    open_stages = set(config["bigin"]["openDealStages"])
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
        "Bigin_updateSpecificRecord",
        path_variables={
            "module_api_name": config["bigin"]["dealModule"],
            "id": deal_id,
        },
        body={"data": [{"Stage": stage}]},
    )
    return bool(result and result.get("data"))


def add_note_to_record(module: str, record_id: str, title: str, content: str, config: dict) -> bool:
    result = mcporter_call(
        "Bigin_addNotesToSpecificRecord",
        path_variables={"module_api_name": module, "id": record_id},
        body={"data": [{"Note_Title": title, "Note_Content": content}]},
    )
    return bool(result and result.get("data"))


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
        "Bigin_addRecords",
        path_variables={"module_api_name": config["bigin"]["taskModule"]},
        body={"data": [data]},
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
