#!/usr/bin/env python3
"""
Bigin CRM Operations v1.0.0

Handles day-to-day CRM interactions: notes, tasks, meetings,
pipeline stage moves, and contact/account CRUD.

Usage:
    python3 bigin-ops.py --action add-note    --module Contacts --record-id <id> --title "Title" --content "Body"
    python3 bigin-ops.py --action fetch-notes --module Contacts --record-id <id>
    python3 bigin-ops.py --action add-task    --record-id <id> --subject "Follow up" --due "2026-04-05"
    python3 bigin-ops.py --action fetch-tasks --record-id <id>
    python3 bigin-ops.py --action add-meeting --record-id <id> --title "Intro call" --start "2026-04-05T10:00:00" --end "2026-04-05T10:30:00"
    python3 bigin-ops.py --action move-stage  --record-id <id> --stage "Proposal Sent"
    python3 bigin-ops.py --action fetch       --module Contacts --record-id <id> [--include notes,tasks,meetings]
    python3 bigin-ops.py --action search      --module Contacts --query "John"
    python3 bigin-ops.py --action create      --module Contacts --data '{"Last_Name":"Smith","Email":"j@example.com"}'
    python3 bigin-ops.py --action update      --module Contacts --record-id <id> --data '{"Phone":"+1234567890"}'
    python3 bigin-ops.py --action list-deals  [--stage "Proposal Sent"] [--limit 20]

Output: JSON to stdout
Logs:   stderr only
"""

import argparse
import json
import sys

from bigin_ops_config import (
    mcporter_call,
    now_iso,
    out,
)

# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

def add_note(module: str, record_id: str, title: str, content: str) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_addNotesToSpecificRecord",
        module_api_name=module,
        record_id=record_id,
        Note_Title=title,
        Note_Content=content,
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "add-note"}
    return {"status": "ok", "action": "add-note", "record_id": record_id, "title": title}


def fetch_notes(module: str, record_id: str) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_getNotesFromSpecificRecord",
        module_api_name=module,
        record_id=record_id,
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "fetch-notes"}
    notes = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "fetch-notes", "count": len(notes), "notes": notes}


def update_note(note_id: str, title: str | None, content: str | None) -> dict:
    data = {}
    if title:
        data["Note_Title"] = title
    if content:
        data["Note_Content"] = content
    result = mcporter_call(
        "ZohoMCP", "Bigin_updateNotes",
        note_id=note_id,
        **data,
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "update-note"}
    return {"status": "ok", "action": "update-note", "note_id": note_id}


def delete_note(note_id: str) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_deleteSpecificNote",
        note_id=note_id,
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "delete-note"}
    return {"status": "ok", "action": "delete-note", "note_id": note_id}


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def add_task(record_id: str, subject: str, due: str | None, owner: str | None, status: str = "Not Started") -> dict:
    data: dict = {
        "Subject": subject,
        "Status": status,
        "What_Id": {"id": record_id},
    }
    if due:
        data["Due_Date"] = due
    if owner:
        data["Owner"] = {"email": owner}

    result = mcporter_call(
        "ZohoMCP", "Bigin_addRecords",
        module_api_name="Tasks",
        data=[data],
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "add-task"}
    created = result.get("data", [{}])
    task_id = created[0].get("details", {}).get("id") if created else None
    return {"status": "ok", "action": "add-task", "task_id": task_id, "subject": subject}


def fetch_tasks(record_id: str, module: str = "Contacts") -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_getRelatedListRecords",
        module_api_name=module,
        record_id=record_id,
        related_list_api_name="Tasks",
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "fetch-tasks"}
    tasks = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "fetch-tasks", "count": len(tasks), "tasks": tasks}


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------

def add_meeting(record_id: str, title: str, start: str, end: str, description: str | None = None) -> dict:
    data: dict = {
        "Event_Title": title,
        "Start_DateTime": start,
        "End_DateTime": end,
        "What_Id": {"id": record_id},
    }
    if description:
        data["Description"] = description

    result = mcporter_call(
        "ZohoMCP", "Bigin_addRecords",
        module_api_name="Meetings",
        data=[data],
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "add-meeting"}
    created = result.get("data", [{}])
    meeting_id = created[0].get("details", {}).get("id") if created else None
    return {"status": "ok", "action": "add-meeting", "meeting_id": meeting_id, "title": title}


def fetch_meetings(record_id: str, module: str = "Contacts") -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_getRelatedListRecords",
        module_api_name=module,
        record_id=record_id,
        related_list_api_name="Meetings",
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "fetch-meetings"}
    meetings = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "fetch-meetings", "count": len(meetings), "meetings": meetings}


# ---------------------------------------------------------------------------
# Pipeline / Deals
# ---------------------------------------------------------------------------

def move_stage(record_id: str, stage: str) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_updateSpecificRecord",
        module_api_name="Pipelines",
        record_id=record_id,
        data={"Stage": stage},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "move-stage"}
    return {"status": "ok", "action": "move-stage", "record_id": record_id, "stage": stage}


def list_deals(stage: str | None = None, limit: int = 20) -> dict:
    kwargs: dict = {
        "module_api_name": "Pipelines",
        "per_page": limit,
        "fields": "id,Deal_Name,Stage,Amount,Account_Name,Owner,Closing_Date",
    }
    if stage:
        kwargs["criteria"] = f"(Stage:equals:{stage})"

    result = mcporter_call("ZohoMCP", "Bigin_getRecords", **kwargs)
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "list-deals"}
    deals = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "list-deals", "count": len(deals), "deals": deals}


# ---------------------------------------------------------------------------
# Generic record operations
# ---------------------------------------------------------------------------

def fetch_record(module: str, record_id: str, include: list[str] | None = None) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_getSpecificRecord",
        module_api_name=module,
        record_id=record_id,
    )
    if not result:
        return {"status": "error", "code": "RECORD_NOT_FOUND", "action": "fetch"}

    record = result.get("data", [{}])[0] if isinstance(result, dict) else {}
    response: dict = {"status": "ok", "action": "fetch", "record": record}

    if include:
        if "notes" in include:
            notes_result = fetch_notes(module, record_id)
            response["notes"] = notes_result.get("notes", [])
        if "tasks" in include:
            tasks_result = fetch_tasks(record_id, module)
            response["tasks"] = tasks_result.get("tasks", [])
        if "meetings" in include:
            meetings_result = fetch_meetings(record_id, module)
            response["meetings"] = meetings_result.get("meetings", [])

    return response


def search_records(module: str, query: str) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_searchRecords",
        module_api_name=module,
        word=query,
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "search"}
    records = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "search", "module": module, "count": len(records), "records": records}


def create_record(module: str, data: dict) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_addRecords",
        module_api_name=module,
        data=[data],
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "create"}
    created = result.get("data", [{}])
    record_id = created[0].get("details", {}).get("id") if created else None
    return {"status": "ok", "action": "create", "module": module, "record_id": record_id}


def update_record(module: str, record_id: str, data: dict) -> dict:
    result = mcporter_call(
        "ZohoMCP", "Bigin_updateSpecificRecord",
        module_api_name=module,
        record_id=record_id,
        data=data,
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "update"}
    return {"status": "ok", "action": "update", "module": module, "record_id": record_id}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Bigin CRM Operations")
    parser.add_argument("--action", required=True, choices=[
        "add-note", "fetch-notes", "update-note", "delete-note",
        "add-task", "fetch-tasks",
        "add-meeting", "fetch-meetings",
        "move-stage", "list-deals",
        "fetch", "search", "create", "update",
    ])
    parser.add_argument("--module", default="Contacts")
    parser.add_argument("--record-id")
    parser.add_argument("--note-id")
    parser.add_argument("--title")
    parser.add_argument("--content")
    parser.add_argument("--subject")
    parser.add_argument("--due")
    parser.add_argument("--owner")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--description")
    parser.add_argument("--stage")
    parser.add_argument("--query")
    parser.add_argument("--data")
    parser.add_argument("--include", help="Comma-separated: notes,tasks,meetings")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    include = [x.strip() for x in args.include.split(",")] if args.include else None
    data = json.loads(args.data) if args.data else {}

    action = args.action
    rid = args.record_id

    if action == "add-note":
        result = add_note(args.module, rid, args.title or "Note", args.content or "")
    elif action == "fetch-notes":
        result = fetch_notes(args.module, rid)
    elif action == "update-note":
        result = update_note(args.note_id, args.title, args.content)
    elif action == "delete-note":
        result = delete_note(args.note_id)
    elif action == "add-task":
        result = add_task(rid, args.subject or "Follow up", args.due, args.owner)
    elif action == "fetch-tasks":
        result = fetch_tasks(rid, args.module)
    elif action == "add-meeting":
        result = add_meeting(rid, args.title or "Meeting", args.start, args.end, args.description)
    elif action == "fetch-meetings":
        result = fetch_meetings(rid, args.module)
    elif action == "move-stage":
        result = move_stage(rid, args.stage)
    elif action == "list-deals":
        result = list_deals(args.stage, args.limit)
    elif action == "fetch":
        result = fetch_record(args.module, rid, include)
    elif action == "search":
        result = search_records(args.module, args.query)
    elif action == "create":
        result = create_record(args.module, data)
    elif action == "update":
        result = update_record(args.module, rid, data)
    else:
        result = {"status": "error", "code": "UNKNOWN_ACTION"}

    out(result)


if __name__ == "__main__":
    main()
