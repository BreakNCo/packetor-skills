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
    ▼
[Bigin] Create Task per action_item
```

## Account & Deal Lookup Logic

1. If `--account` is provided, search Bigin Accounts by that name
2. If `--account` is omitted, use `account_name` from GPT summary
3. If account not found → note is skipped, result contains `account_lookup: not found`
4. If account found but no open deal → note is added to the Account record
5. If `--deal-id` is provided, skip lookup entirely

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
- ✅ "Send the proposal by Thursday" → task: "Send proposal", due_days: 2
- ✅ "Book a technical demo with the CTO" → task: "Book technical demo with CTO", due_days: 5
- ❌ "We'll follow up" → too vague, not extracted
- ❌ "Let's keep in touch" → not an action item

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
