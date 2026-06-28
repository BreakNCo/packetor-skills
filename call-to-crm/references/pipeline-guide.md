# Call-to-CRM Pipeline Guide

## Flow Overview

```
Audio file
    │
    ▼
[ffmpeg] Convert to mono 16kHz WAV
    │  Split into 10-min chunks if >25MB
    ▼
[Whisper] Transcribe each chunk → merge → full transcript
    │
    ▼
[GPT-4o] Structured CRM summary JSON
    │  account_name, sentiment, stage_change, key_points, action_items
    ▼
[Bigin] Search for Account by name
    │  → Search for open Deal under Account
    ▼
[Bigin] Update pipeline Stage (if stage_change present)
    ▼
[Bigin] Add structured Note to Deal (fallback: Account)
    │  Prefer Pipeline-only note writes; use the working MCP note body shape
    ▼
[Bigin] Create Task per action_item
    │  Use Pipeline-linked task creation with `What_Id={id}` and `$se_module="Deals"`
```

## Account & Deal Lookup Logic

1. If `--account` is provided, search Bigin Accounts by that name
2. If `--account` is omitted, use `account_name` from GPT summary
3. If account not found → note is skipped, result contains `account_lookup: not found`
4. If account found but no open deal → note is added to the Account record
5. If `--deal-id` is provided, skip lookup entirely
6. If a deal id came from an older note, chat message, or another workspace, do not trust it blindly — re-search the current Pipeline record before writing notes or tasks.

### Exact deal id extraction in this environment

When the visible search output does not clearly expose the top-level Pipeline/Deal `id`, extract it with:

```bash
mcporter --config /data/workspace-discord-ops/config/mcporter.json call zoho-bigin.Bigin_searchRecords \
  'path_variables={"module_api_name":"Pipelines"}' \
  'query_params={"word":"<company or deal name>"}' \
| python3 -c 'import sys,json; obj=json.load(sys.stdin); print(obj["data"]["data"][0]["id"])'
```

Example used successfully for Orivios:

```bash
mcporter --config /data/workspace-discord-ops/config/mcporter.json call zoho-bigin.Bigin_searchRecords \
  'path_variables={"module_api_name":"Pipelines"}' \
  'query_params={"word":"Orivios Technologies Private Limited"}' \
| python3 -c 'import sys,json; obj=json.load(sys.stdin); print(obj["data"]["data"][0]["id"])'
```

Output:

```text
1188539000000665129
```

## Note Write Rule

When writing a note to a Pipeline record through the local Zoho Bigin MCP path, use one of these two working patterns:

### Preferred specific-record form
- tool: `Bigin_addNotesToSpecificRecord`
- path variables:
  - `module_api_name = Pipelines`
  - `id = <deal_id>`
- body:

```json
{
  "data": [
    {
      "Note_Title": "...",
      "Note_Content": "..."
    }
  ]
}
```

### Reliable fallback form
- tool: `Bigin_addNotes`
- body:

```json
{
  "data": [
    {
      "Note_Title": "...",
      "Note_Content": "...",
      "Parent_Id": "<deal_id>",
      "se_module": "Pipelines"
    }
  ]
}
```

Important:
- Do **not** use a flat note body like `{ "Note_Title": "...", "Note_Content": "..." }` for `Bigin_addNotesToSpecificRecord` in this environment.
- Pipeline note writes are confirmed working when sent with `body.data = [...]`.

## Stage Change Rules

GPT-4o sets `stage_change` only when the transcript clearly implies the deal advanced.
Examples that trigger a stage change:
- "I'll send you the proposal by Friday" → `Proposal/Price Quote`
- "We're ready to negotiate" → `Negotiation/Review`
- "We're going with Packets" → `Closed Won`
- "We're going with a competitor" → `Closed Lost`

Examples that do NOT trigger a stage change:
- General discussion, status updates, check-ins
- Ambiguous language ("we'll think about it")

## Action Items Detection

GPT-4o extracts action_items only for **concrete, named next steps**:
- ✅ "Send the proposal by Thursday" → task: "Send proposal", due date = Thursday
- ✅ "Book a technical demo with the CTO" → task: "Book technical demo with CTO", due date = earliest practical meeting date
- ❌ "We'll follow up" → too vague, not extracted
- ❌ "Let's keep in touch" → not an action item

## Due Date Rules

Every created task should have a due date.

Use these defaults when the transcript does not give an exact date:
- send email / send details / send deck / send proposal → next day
- callback tomorrow / next day → next day
- this week meeting / schedule this week → next business day
- next week follow-up → earliest practical day next week
- explicit weekday mentioned → use that weekday
- no timing but still clearly actionable → next business day

## Dry Run Mode

Use `--dry-run` to test without writing to Bigin:
```bash
python3 call-to-crm.py --input call.mp4 --dry-run
```
Returns full transcript + GPT summary in JSON. No CRM writes.

## Handling Failures

| Failure | Behaviour |
|---------|-----------|
| ffmpeg fails | Hard stop, return error JSON |
| Whisper chunk fails | Log warning, skip chunk, continue with others |
| GPT summary fails | Fall back to raw transcript as note (if config allows) |
| Account not found | Log warning, return transcript in result, no CRM write |
| Deal not found | Add note to Account instead of Deal |
| Task creation fails | Log, continue — note already added |

## Bigin Stage Values (exact spelling required)

- `Qualification`
- `Needs Analysis`
- `Value Proposition`
- `Identify Decision Makers`
- `Proposal/Price Quote`
- `Negotiation/Review`
- `Closed Won`
- `Closed Lost`
