#!/usr/bin/env python3
"""
Bigin CRM Operations v1.1.0

Handles day-to-day CRM interactions: notes, tasks, meetings,
pipeline stage moves, and contact/account CRUD.

Output: JSON to stdout
Logs:   stderr only
"""

import argparse
import json

from bigin_ops_config import mcporter_call, out

SERVER = "zoho-bigin"


def add_note(module: str, record_id: str, title: str, content: str) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_addNotesToSpecificRecord",
        path_variables={"module_api_name": module, "id": record_id},
        body={"Note_Title": title, "Note_Content": content},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "add-note"}
    return {"status": "ok", "action": "add-note", "record_id": record_id, "title": title, "result": result}


def fetch_notes(module: str, record_id: str) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_getNotesFromSpecificRecord",
        path_variables={"module_api_name": module, "id": record_id},
        query_params={},
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "fetch-notes"}
    notes = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "fetch-notes", "count": len(notes), "notes": notes}


def update_note(module: str, record_id: str, note_id: str, title: str | None, content: str | None) -> dict:
    body = {}
    if title:
        body["Note_Title"] = title
    if content:
        body["Note_Content"] = content
    result = mcporter_call(
        SERVER,
        "Bigin_updateNotes",
        path_variables={"module_api_name": module, "id": record_id, "note_id": note_id},
        body=body,
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "update-note"}
    return {"status": "ok", "action": "update-note", "note_id": note_id, "result": result}


def delete_note(module: str, record_id: str, note_id: str) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_deleteSpecificNote",
        path_variables={"module_api_name": module, "id": record_id, "note_id": note_id},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "delete-note"}
    return {"status": "ok", "action": "delete-note", "note_id": note_id, "result": result}


def add_task(record_id: str, subject: str, due: str | None, owner: str | None, status: str = "Not Started") -> dict:
    item = {
        "Subject": subject,
        "Status": status,
        "What_Id": {"id": record_id},
    }
    if due:
        item["Due_Date"] = due
    if owner:
        item["Owner"] = {"email": owner}

    result = mcporter_call(
        SERVER,
        "Bigin_addRecords",
        path_variables={"module_api_name": "Tasks"},
        body={"data": [item]},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "add-task"}
    created = result.get("data", [{}]) if isinstance(result, dict) else [{}]
    task_id = created[0].get("details", {}).get("id") if created else None
    return {"status": "ok", "action": "add-task", "task_id": task_id, "subject": subject, "result": result}


def fetch_tasks(record_id: str, module: str = "Contacts") -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_getRelatedListRecords",
        path_variables={"module_api_name": module, "id": record_id, "related_list_api_name": "Tasks"},
        query_params={},
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "fetch-tasks"}
    tasks = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "fetch-tasks", "count": len(tasks), "tasks": tasks}


def add_meeting(record_id: str, title: str, start: str, end: str, description: str | None = None) -> dict:
    item = {
        "Event_Title": title,
        "Start_DateTime": start,
        "End_DateTime": end,
        "What_Id": {"id": record_id},
    }
    if description:
        item["Description"] = description

    result = mcporter_call(
        SERVER,
        "Bigin_addRecords",
        path_variables={"module_api_name": "Events"},
        body={"data": [item]},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "add-meeting"}
    created = result.get("data", [{}]) if isinstance(result, dict) else [{}]
    meeting_id = created[0].get("details", {}).get("id") if created else None
    return {"status": "ok", "action": "add-meeting", "meeting_id": meeting_id, "title": title, "result": result}


def fetch_meetings(record_id: str, module: str = "Contacts") -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_getRelatedListRecords",
        path_variables={"module_api_name": module, "id": record_id, "related_list_api_name": "Events"},
        query_params={},
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "fetch-meetings"}
    meetings = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "fetch-meetings", "count": len(meetings), "meetings": meetings}


def move_stage(record_id: str, stage: str) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_updateSpecificRecord",
        path_variables={"module_api_name": "Pipelines", "id": record_id},
        body={"data": [{"Stage": stage}]},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "move-stage"}
    return {"status": "ok", "action": "move-stage", "record_id": record_id, "stage": stage, "result": result}


def list_deals(stage: str | None = None, limit: int = 20) -> dict:
    query_params = {
        "per_page": limit,
        "fields": "id,Deal_Name,Stage,Amount,Account_Name,Owner,Closing_Date",
    }
    if stage:
        query_params["criteria"] = f"(Stage:equals:{stage})"

    result = mcporter_call(
        SERVER,
        "Bigin_getRecords",
        path_variables={"module_api_name": "Pipelines"},
        query_params=query_params,
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "list-deals"}
    deals = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "list-deals", "count": len(deals), "deals": deals}


def fetch_record(module: str, record_id: str, include: list[str] | None = None) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_getSpecificRecord",
        path_variables={"module_api_name": module, "id": record_id},
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
        SERVER,
        "Bigin_searchRecords",
        path_variables={"module_api_name": module},
        query_params={"word": query},
    )
    if not result:
        return {"status": "error", "code": "FETCH_FAILED", "action": "search"}
    records = result.get("data", []) if isinstance(result, dict) else []
    return {"status": "ok", "action": "search", "module": module, "count": len(records), "records": records}


def create_record(module: str, data: dict) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_addRecords",
        path_variables={"module_api_name": module},
        body={"data": [data]},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "create"}
    created = result.get("data", [{}]) if isinstance(result, dict) else [{}]
    record_id = created[0].get("details", {}).get("id") if created else None
    return {"status": "ok", "action": "create", "module": module, "record_id": record_id, "result": result}


def update_record(module: str, record_id: str, data: dict) -> dict:
    result = mcporter_call(
        SERVER,
        "Bigin_updateSpecificRecord",
        path_variables={"module_api_name": module, "id": record_id},
        body={"data": [data]},
    )
    if not result:
        return {"status": "error", "code": "WRITE_FAILED", "action": "update"}
    return {"status": "ok", "action": "update", "module": module, "record_id": record_id, "result": result}


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
        result = update_note(args.module, rid, args.note_id, args.title, args.content)
    elif action == "delete-note":
        result = delete_note(args.module, rid, args.note_id)
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
