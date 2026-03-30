"""
Bigin Ops skill — shared MCP helpers and utilities.
Mirrors the pattern from bigin-research/scripts/bigin_config.py.
"""

import ast
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/data/workspace"))
SKILL_DIR = WORKSPACE / "packetor-skills" / "bigin-ops"
STATE_DIR = SKILL_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SERVER = os.environ.get("BIGIN_MCP_SERVER", "zoho-bigin")


def _normalize_params(tool: str, params: dict) -> dict:
    path_keys = {"module_api_name", "id", "record_id", "note_id", "related_list_api_name"}
    query_keys = {"criteria", "email", "phone", "word", "fields", "page", "per_page", "sort_by", "sort_order", "converted"}
    body_hint_keys = {
        "data", "Note_Title", "Note_Content", "Parent_Id", "se_module",
        "Subject", "Status", "What_Id", "Due_Date", "Owner",
        "Event_Title", "Start_DateTime", "End_DateTime", "Description", "Participants", "Venue"
    }

    if any(k in params for k in ("path_variables", "query_params", "body")):
        return dict(params)

    path_variables = {}
    query_params = {}
    body = {}

    for key, value in params.items():
        k = "id" if key == "record_id" else key
        if k in path_keys:
            path_variables[k] = value
        elif k in query_keys:
            query_params[k] = value
        elif k in body_hint_keys:
            body[k] = value
        else:
            body[k] = value

    if tool in {"Bigin_addRecords", "Bigin_updateSpecificRecord"}:
        if "data" in body and isinstance(body["data"], list):
            body = {"data": body["data"]}
        elif body:
            body = {"data": [body]}
    elif tool in {"Bigin_addNotesToSpecificRecord", "Bigin_updateNotes"}:
        pass
    elif tool in {"Bigin_searchRecords", "Bigin_getRecords", "Bigin_getNotesFromSpecificRecord", "Bigin_getRelatedListRecords"}:
        body = {}
    elif tool in {"Bigin_getSpecificRecord", "Bigin_deleteSpecificNote"}:
        body = {}
        query_params = {}

    normalized = {}
    if path_variables:
        normalized["path_variables"] = path_variables
    if query_params:
        normalized["query_params"] = query_params
    if body:
        normalized["body"] = body
    return normalized


def _parse_mcporter_output(stdout: str):
    text = (stdout or "").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    try:
        return ast.literal_eval(text)
    except Exception:
        return None


def mcporter_call(server: str, tool: str, retries: int = 2, timeout: int = 25, **params) -> dict | None:
    """Call an MCP tool via mcporter CLI with current Zoho MCP schema adaptation."""
    server = os.environ.get("BIGIN_MCP_SERVER", server or DEFAULT_SERVER)
    normalized = _normalize_params(tool, params)
    args = json.dumps(normalized) if normalized else "{}"
    config_path = str(WORKSPACE / "config" / "mcporter.json")
    cmd = ["mcporter", "--config", config_path, "call", server, tool, "--args", args]

    env = os.environ.copy()
    env["PATH"] = f"/data/workspace/bin:{env.get('PATH', '')}"

    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
            if r.returncode != 0:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                return None

            raw = _parse_mcporter_output(r.stdout)
            if raw is None:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                return None

            if isinstance(raw, dict) and "content" in raw:
                content = raw["content"]
                if isinstance(content, list) and content:
                    first = content[0]
                    if isinstance(first, dict) and "text" in first:
                        parsed = _parse_mcporter_output(first["text"])
                        if parsed is not None:
                            return parsed
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
    print(json.dumps(data, indent=2))
