---
name: bigin-ops
description: Manage all day-to-day CRM operations in Zoho Bigin — add notes, create tasks, schedule meetings, move deals through pipeline stages, create or update contacts and accounts, and fetch existing records. Use this skill for any direct CRM interaction that is not company research or data enrichment.
version: 1.0.0
compatibility: openclaw
tools:
  - ZohoMCP
---

# Bigin CRM Operations

Handles all direct CRM interactions with Zoho Bigin: reading and writing records across Accounts, Contacts, and Pipelines (deals), plus activities — Notes, Tasks, and Meetings.

## When to Use

- Add a note to a contact, account, or deal
- Create a task or follow-up for a record
- Schedule or log a meeting
- Move a deal to a different pipeline stage
- Create or update a contact or account manually
- Fetch a contact's details, deals, notes, tasks, or meetings
- List deals in a pipeline or filter by stage

## When NOT to Use

- Researching a company online and enriching CRM data → use `bigin-research` skill
- Bulk data imports → use Bigin's native import or a batch script
- Sending emails → use `zoho-mail` skill

## Prerequisites

**MCP Server:** `ZohoMCP`

Zoho OAuth credentials must be configured in the ZohoMCP server.

## Modules

| Module | `module_api_name` | Used for |
|--------|------------------|----------|
| Accounts | `Accounts` | Companies |
| Contacts | `Contacts` | People |
| Pipelines | `Pipelines` | Deals / opportunities |
| Notes | via record relation | Notes on any record |
| Tasks | `Tasks` | Follow-up tasks |
| Meetings | `Meetings` | Calls and meetings |

See `references/bigin-ops.md` for full field names, pipeline stage values, and tool call patterns.

## Workflows

### Notes
- **Add note** → `Bigin_addNotesToSpecificRecord`
- **Fetch notes** → `Bigin_getNotesFromSpecificRecord`
- **Update note** → `Bigin_updateNotes`
- **Delete note** → `Bigin_deleteSpecificNote`

### Tasks
- **Create task** → `Bigin_addRecords` on `Tasks` module
- **Fetch tasks** → `Bigin_getRelatedListRecords` with `related_list_api_name: "Tasks"`
- **Update task** → `Bigin_updateSpecificRecord` on `Tasks`

### Meetings
- **Create meeting** → `Bigin_addRecords` on `Meetings` module
- **Fetch meetings** → `Bigin_getRelatedListRecords` with `related_list_api_name: "Meetings"`
- **Update meeting** → `Bigin_updateSpecificRecord` on `Meetings`

### Pipeline / Deals
- **List deals** → `Bigin_getRecords` on `Pipelines`
- **Move stage** → `Bigin_updateSpecificRecord` with `Stage` field
- **Create deal** → `Bigin_addRecords` on `Pipelines`
- **Fetch deal** → `Bigin_getSpecificRecord` on `Pipelines`

### Contacts & Accounts
- **Search** → `Bigin_searchRecords`
- **Fetch** → `Bigin_getSpecificRecord`
- **Create** → `Bigin_addRecords`
- **Update** → `Bigin_updateSpecificRecord`

## Script Usage

Use `bigin-ops.py` for structured, multi-step operations:

```bash
# Add a note
python3 bigin-ops.py --action add-note --module Contacts --record-id <id> --title "Call notes" --content "Discussed pricing..."

# Create a task
python3 bigin-ops.py --action add-task --record-id <id> --subject "Follow up" --due "2026-04-05" --owner "joseph@packets.build"

# Move deal stage
python3 bigin-ops.py --action move-stage --record-id <id> --stage "Proposal Sent"

# Fetch record with related data
python3 bigin-ops.py --action fetch --module Contacts --record-id <id> --include notes,tasks,meetings
```

## Error Handling

All errors return structured JSON. Never surface raw tracebacks.

Common codes:
- `RECORD_NOT_FOUND` — no matching record in Bigin
- `INVALID_STAGE` — stage name not valid for this pipeline
- `WRITE_FAILED` — CRM update failed, check field names in `references/bigin-ops.md`
