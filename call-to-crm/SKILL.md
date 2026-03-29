---
name: call-to-crm
description: End-to-end skill: take an audio/video recording of a call or meeting, convert it with ffmpeg, transcribe with OpenAI Whisper, summarise in CRM language with GPT-4o, find the matching Bigin account/deal, update the pipeline stage, add a structured note, and create follow-up tasks for any concrete next actions mentioned. Use this skill when someone shares a call recording, meeting file, or voice note and wants their CRM updated.
version: 1.0.0
compatibility: openclaw
tools:
  - ZohoMCP
---

# Call to CRM

Single end-to-end pipeline: audio attachment → ffmpeg conversion → OpenAI Whisper transcription → GPT-4o CRM summary → Bigin account/deal lookup → pipeline update → structured note → follow-up tasks.

## When to Use

- "Here's the recording of my call with Acme — update the CRM"
- "Transcribe this meeting and add notes to the deal"
- "Process this voice note and create follow-ups"
- Any audio or video file that represents a customer interaction

## When NOT to Use

- Transcription only with no CRM update → use `audio-transcribe` skill
- CRM updates with no audio → use `bigin-ops` skill
- Live/real-time calls — Whisper is file-based only

## Prerequisites

**System dependencies:**
- `ffmpeg` — `brew install ffmpeg`

**Environment variables:**
- `OPENAI_API_KEY` — OpenAI API key (Whisper + GPT-4o access)

**MCP Server:**
- `ZohoMCP` — Bigin CRM read/write

**Python dependencies:**
- `pip install openai`

## Pipeline (7 steps)

```
[1] Receive audio file path
      ↓
[2] ffmpeg → convert to mono 16kHz WAV (split if >25MB)
      ↓
[3] Whisper → full transcript
      ↓
[4] GPT-4o → structured CRM summary
    { account_name, contact_name, summary, stage_change,
      key_points[], action_items[], sentiment }
      ↓
[5] Bigin lookup → find Account + Deal by name
      ↓
[6] Bigin update → pipeline stage (if stage_change present)
      ↓
[7] Bigin note → add structured call note
      ↓
[8] Bigin tasks → create task per action_item (if any)
```

## Script Usage

```bash
# Basic — provide audio and company name
python3 call-to-crm.py --input call.mp4 --account "Acme Corp"

# Auto-detect account from transcript (no --account needed)
python3 call-to-crm.py --input meeting.m4a

# With known deal ID — skip lookup
python3 call-to-crm.py --input call.mp4 --deal-id "<bigin_deal_id>"

# Dry run — transcribe and summarise, but don't write to Bigin
python3 call-to-crm.py --input call.mp4 --dry-run

# Set task due date offset (days from today)
python3 call-to-crm.py --input call.mp4 --account "Acme" --task-due-days 3

# Override language for faster transcription
python3 call-to-crm.py --input hindi-call.mp4 --language hi
```

## CRM Summary Schema

GPT-4o produces this JSON before any Bigin writes:

```json
{
  "account_name": "Acme Corp",
  "contact_name": "Jane Smith",
  "call_date": "2026-03-29",
  "duration_minutes": 32,
  "sentiment": "positive",
  "stage_change": "Proposal/Price Quote",
  "summary": "Discussed Q2 compliance requirements. Customer interested in Enterprise plan. Requested formal proposal by end of week.",
  "key_points": [
    "Compliance deadline is June 30",
    "Decision maker is CTO, not procurement",
    "Budget approved up to $50k"
  ],
  "action_items": [
    { "task": "Send formal proposal", "owner": "sales@packets.build", "due_days": 2 },
    { "task": "Schedule technical demo with CTO", "owner": "sales@packets.build", "due_days": 5 }
  ]
}
```

## Note Format in Bigin

Notes are added with the title `[Call] YYYY-MM-DD — <account>` and structured body:

```
[Auto] Call summary — 2026-03-29
Duration: 32 min | Sentiment: Positive

Summary:
Discussed Q2 compliance requirements...

Key Points:
• Compliance deadline is June 30
• Decision maker is CTO, not procurement

Action Items:
• Send formal proposal (due: 2026-03-31)
• Schedule technical demo with CTO (due: 2026-04-03)
```

## Error Handling

All errors return structured JSON. Logs to stderr only.

Common codes:
- `FFMPEG_NOT_FOUND` — install ffmpeg
- `INPUT_NOT_FOUND` — file path doesn't exist
- `OPENAI_AUTH_FAILED` — check OPENAI_API_KEY
- `ACCOUNT_NOT_FOUND` — no matching Bigin account; note stored but no deal update
- `DEAL_NOT_FOUND` — account found but no open deal; note added to account
- `TRANSCRIPTION_FAILED` — Whisper error
- `SUMMARY_FAILED` — GPT-4o parse error; raw transcript saved as note instead
